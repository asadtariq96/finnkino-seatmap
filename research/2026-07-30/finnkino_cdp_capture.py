import asyncio, json, urllib.request, time, os
import websockets

BASE='http://127.0.0.1:9223'
def http(url, method='GET'):
    r=urllib.request.Request(url,method=method)
    with urllib.request.urlopen(r) as f: return json.load(f)

async def main():
    page=http(BASE+'/json/new?https%3A%2F%2Fwww.finnkino.fi%2Fen%2Fcinemas%2Ffinnkino-plevna%2F','PUT')
    ws=page['webSocketDebuggerUrl']
    reqs={}; responses={}; scripts=[]; nextid=1
    async with websockets.connect(ws,max_size=50_000_000) as s:
        async def send(method,params={}):
            nonlocal nextid
            i=nextid; nextid+=1
            await s.send(json.dumps({'id':i,'method':method,'params':params})); return i
        await send('Network.enable',{'maxTotalBufferSize':100000000,'maxResourceBufferSize':20000000})
        await send('Page.enable')
        await send('Page.navigate',{'url':'https://www.finnkino.fi/en/cinemas/finnkino-plevna/'})
        end=time.time()+30
        while time.time()<end:
            try: m=json.loads(await asyncio.wait_for(s.recv(),timeout=2))
            except asyncio.TimeoutError: continue
            if m.get('method')=='Network.requestWillBeSent':
                p=m['params']; reqs[p['requestId']]=p['request']
            elif m.get('method')=='Network.responseReceived':
                p=m['params']; responses[p['requestId']]=p['response']
        os.makedirs('finnkino_capture',exist_ok=True)
        with open('finnkino_capture/network.json','w',encoding='utf-8') as f:
            json.dump({'requests':reqs,'responses':responses},f,indent=2,ensure_ascii=False)
        # bodies for JS, document, XHR/fetch
        for rid,r in responses.items():
            typ=r.get('mimeType',''); url=r.get('url','')
            if typ in ('application/javascript','text/javascript','application/json','text/html','application/xml','text/xml') or any(x in url.lower() for x in ['api','seat','show']):
                i=await send('Network.getResponseBody',{'requestId':rid})
                while True:
                    m=json.loads(await s.recv())
                    if m.get('id')==i: break
                if 'result' in m:
                    ext='.js' if 'javascript' in typ else '.json' if 'json' in typ else '.txt'
                    name=str(len(scripts)).zfill(3)+ext
                    body=m['result']['body']
                    with open('finnkino_capture/'+name,'w',encoding='utf-8',errors='ignore') as f:f.write(body)
                    scripts.append({'file':name,'url':url,'mimeType':typ,'status':r.get('status')})
        with open('finnkino_capture/bodies.json','w',encoding='utf-8') as f:json.dump(scripts,f,indent=2)
        i=await send('Runtime.evaluate',{'expression':'document.title+"\\n"+location.href+"\\n"+document.body.innerText.slice(0,2000)','returnByValue':True})
        while True:
            m=json.loads(await s.recv())
            if m.get('id')==i: break
        print(m.get('result',{}).get('result',{}).get('value'))
        print('requests',len(reqs),'responses',len(responses),'bodies',len(scripts))
asyncio.run(main())
