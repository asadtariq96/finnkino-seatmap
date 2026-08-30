function extractToken(html) {
  const normalized = html.replace(/\\"/g, '"').replace(/\\\//g, "/");
  const match = normalized.match(/"authToken"\s*:\s*"([^"]+)"/);
  return match?.[1] ?? null;
}

export default {
  async fetch(request, env) {
    const secret = env.TOKEN_SECRET;
    if (secret) {
      const auth = request.headers.get("Authorization") ?? "";
      if (auth !== `Bearer ${secret}`) {
        return new Response("Unauthorized", { status: 401 });
      }
    }

    const response = await fetch("https://www.finnkino.fi/", {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml",
      },
    });

    const html = await response.text();
    if (!response.ok || html.includes("Just a moment")) {
      return Response.json({ error: "Finnkino homepage blocked" }, { status: 502 });
    }

    const token = extractToken(html);
    if (!token) {
      return Response.json({ error: "authToken not found" }, { status: 502 });
    }

    return Response.json({ token });
  },
};
