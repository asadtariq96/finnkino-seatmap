import asyncio
import base64
import json
import os
import re
import secrets
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import web

BASE = "https://digital-api.finnkino.fi/WSVistaWebClient/ocapi/v1"
HOME = "https://www.finnkino.fi/"
ROOT = Path(__file__).parent


def extract_api_config(html: str) -> dict[str, str]:
    normalized = html.replace('\\"', '"').replace('\\/', '/')
    url = re.search(r'"apiUrl"\s*:\s*"([^"]+)"', normalized)
    token = re.search(r'"authToken"\s*:\s*"([^"]+)"', normalized)
    if not url or not token:
        raise ValueError("Finnkino API configuration was not found")
    return {"api_url": url.group(1), "token": token.group(1)}


def pick_showtimes(payload: dict[str, Any], film_id: str) -> list[dict[str, Any]]:
    return sorted(
        (show for show in payload.get("showtimes", []) if show.get("filmId") == film_id),
        key=lambda show: show.get("schedule", {}).get("startsAt", ""),
    )


def window_dates(start: date | None = None) -> list[str]:
    start = start or datetime.now(ZoneInfo("Europe/Helsinki")).date()
    return [(start + timedelta(days=offset)).isoformat() for offset in range(7)]


def multi_site_schedule_path(business_date: str, site_ids: list[str]) -> str:
    query = "&".join(f"siteIds={site_id}" for site_id in site_ids)
    return f"showtimes/by-business-date/{business_date}?{query}"


def build_seat_map(layout: dict[str, Any], availability: dict[str, Any]) -> dict[str, Any]:
    statuses = {seat["seatId"]: seat.get("status", "Unavailable") for seat in availability.get("seatAvailabilities", [])}
    areas = []
    total = available = 0
    for area in layout.get("seatLayout", {}).get("areas", []):
        rows = []
        for row in area.get("rows", []):
            seats = []
            for seat in row.get("seats", []):
                status = statuses.get(seat.get("id"), "Unavailable")
                total += 1
                available += status == "Available"
                seats.append({
                    "id": seat.get("id"), "label": seat.get("label"), "rowLabel": seat.get("rowLabel", row.get("label")),
                    "type": seat.get("type", "Normal"), "status": status, "position": seat.get("position", {}),
                })
            rows.append({"number": row.get("number"), "label": row.get("label"), "seats": seats})
        areas.append({"number": area.get("number"), "name": area.get("name", {}).get("text", ""), "rows": rows})
    return {"layoutId": layout.get("seatLayout", {}).get("id"), "areas": areas,
            "counts": {"total": total, "available": available, "unavailable": total - available}}


class StaleCache:
    def __init__(self):
        self.data: dict[str, tuple[float, float, Any]] = {}

    def get(self, key: str, *, allow_stale: bool = False):
        item = self.data.get(key)
        if not item:
            return None, False
        fresh_until, stale_until, value = item
        now = time.monotonic()
        if now <= fresh_until:
            return value, False
        if allow_stale and now <= stale_until:
            return value, True
        self.data.pop(key, None)
        return None, False

    def put(self, key: str, value: Any, fresh_ttl: float, stale_ttl: float):
        now = time.monotonic()
        self.data[key] = (now + fresh_ttl, now + stale_ttl, value)


class Finnkino:
    def __init__(self):
        self.cache = StaleCache()
        self.config: dict[str, str] | None = None
        self.session = None
        self.show_index: dict[str, str] = {}
        self.warm_status = {"state": "idle", "dates": 0, "layouts": 0, "shows": 0, "error": None}
        self._upstream = asyncio.Semaphore(3)
        self._seatmap_refresh: set[str] = set()

    async def start(self):
        from curl_cffi.requests import AsyncSession
        self.session = AsyncSession(impersonate="chrome")

    async def close(self):
        if self.session:
            await self.session.close()

    async def refresh_config(self):
        response = await self.session.get(HOME, timeout=30)
        response.raise_for_status()
        self.config = extract_api_config(response.text)

    def headers(self) -> dict[str, str]:
        token = self.config["token"]
        payload = token.split(".")[1] + "==="
        subject = json.loads(base64.urlsafe_b64decode(payload))["sub"].replace("|", "")
        return {"Accept": "application/json", "Authorization": f"Bearer {token}",
                "correlationId": f"OCC-{subject}-{secrets.token_urlsafe(5)}-{secrets.token_urlsafe(5)}",
                "Origin": HOME.rstrip("/"), "Referer": HOME}

    async def _fetch_json(self, path: str):
        if not self.config:
            await self.refresh_config()
        url = f"{BASE}/{path}"
        async with self._upstream:
            response = await self.session.get(url, headers=self.headers(), timeout=30)
        if response.status_code == 401:
            await self.refresh_config()
            async with self._upstream:
                response = await self.session.get(url, headers=self.headers(), timeout=30)
        if response.status_code == 429:
            raise web.HTTPTooManyRequests(text="upstream rate limit")
        response.raise_for_status()
        return response.json()

    async def get(self, path: str, fresh_ttl: float = 0, stale_ttl: float = 0):
        key = path
        cached, _ = self.cache.get(key, allow_stale=False)
        if cached is not None:
            return cached
        try:
            value = await self._fetch_json(path)
        except web.HTTPTooManyRequests:
            stale, _ = self.cache.get(key, allow_stale=True)
            if stale is not None:
                return stale
            raise
        if fresh_ttl:
            self.cache.put(key, value, fresh_ttl, stale_ttl or fresh_ttl * 12)
        return value

    async def build_seatmap(self, showtime: str) -> dict[str, Any]:
        layout_id = self.show_index.get(showtime)
        layout_task = (
            self.get(f"seat-layouts/{layout_id}", 86400, 604800)
            if layout_id else self.get(f"showtimes/{showtime}/seat-layout", 43200, 604800)
        )
        layout, availability, detail = await asyncio.gather(
            layout_task,
            self.get(f"showtimes/{showtime}/seat-availability?preview=false", 45, 600),
            self.get(f"showtimes/{showtime}", 300, 3600),
        )
        result = build_seat_map(layout, availability)
        result["detail"] = detail
        return result

    async def seatmap_for(self, showtime: str, *, revalidate: bool = False) -> dict[str, Any]:
        key = f"seatmap:{showtime}"
        if not revalidate:
            cached, stale = self.cache.get(key, allow_stale=True)
            if cached is not None and not stale:
                return cached
            if cached is not None and stale and showtime not in self._seatmap_refresh:
                self._seatmap_refresh.add(showtime)
                asyncio.create_task(self._refresh_seatmap(showtime))
                return cached
        result = await self.build_seatmap(showtime)
        self.cache.put(key, result, 45, 600)
        return result

    async def _refresh_seatmap(self, showtime: str):
        try:
            result = await self.build_seatmap(showtime)
            self.cache.put(f"seatmap:{showtime}", result, 45, 600)
        except Exception:
            pass
        finally:
            self._seatmap_refresh.discard(showtime)

    def backfill_schedule(self, business_date: str, site_ids: list[str], payload: dict[str, Any]):
        shows = payload.get("showtimes", [])
        for show in shows:
            if show.get("seatLayoutId"):
                self.show_index[show["id"]] = show["seatLayoutId"]
        for site_id in site_ids:
            per_site = dict(payload)
            per_site["showtimes"] = [show for show in shows if show.get("siteId") == site_id]
            key = f"showtimes/by-business-date/{business_date}?siteIds={site_id}"
            self.cache.put(key, per_site, 360, 3600)

    async def warm_window(self):
        self.warm_status = {"state": "schedules", "dates": 0, "layouts": 0, "shows": 0, "error": None}
        try:
            sites = (await self.get("sites", 43200, 86400)).get("sites", [])
            site_ids = [site["id"] for site in sites]

            async def load_day(day: str):
                payload = await self.get(multi_site_schedule_path(day, site_ids), 240, 3600)
                self.backfill_schedule(day, site_ids, payload)
                self.warm_status["dates"] += 1
                self.warm_status["shows"] += len(payload.get("showtimes", []))
                return payload

            schedules = await asyncio.gather(*(load_day(day) for day in window_dates()))
            layout_ids = {
                show["seatLayoutId"]
                for payload in schedules
                for show in payload.get("showtimes", [])
                if show.get("seatLayoutId")
            }
            self.warm_status["state"] = "layouts"
            limiter = asyncio.Semaphore(2)

            async def load_layout(layout_id: str):
                async with limiter:
                    try:
                        await self.get(f"seat-layouts/{layout_id}", 86400, 604800)
                        self.warm_status["layouts"] += 1
                    except Exception:
                        pass

            await asyncio.gather(*(load_layout(layout_id) for layout_id in layout_ids))
            self.warm_status["state"] = "ready"
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.warm_status["state"] = "error"
            self.warm_status["error"] = str(exc)

    async def warm_loop(self):
        while True:
            await self.warm_window()
            await asyncio.sleep(300)


fk = Finnkino()


async def json_result(coro):
    try: return web.json_response(await coro)
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=502)


async def sites(_): return await json_result(fk.get("sites", 43200, 86400))

async def schedule(request):
    date, site = request.query.get("date"), request.query.get("site")
    if not date or not site: raise web.HTTPBadRequest(text="date and site are required")
    async def load():
        payload = await fk.get(f"showtimes/by-business-date/{date}?siteIds={site}", 300, 3600)
        fk.backfill_schedule(date, [site], payload)
        return payload
    return await json_result(load())


async def movie_schedule(request):
    business_date = request.query.get("date")
    if not business_date: raise web.HTTPBadRequest(text="date is required")
    async def load():
        site_list = (await fk.get("sites", 43200, 86400)).get("sites", [])
        site_ids = [site["id"] for site in site_list]
        payload = await fk.get(multi_site_schedule_path(business_date, site_ids), 240, 3600)
        fk.backfill_schedule(business_date, site_ids, payload)
        return payload
    return await json_result(load())


async def seatmap(request):
    showtime = request.query.get("showtime")
    if not showtime: raise web.HTTPBadRequest(text="showtime is required")
    return await json_result(fk.seatmap_for(showtime))

async def cache_status(_): return web.json_response(fk.warm_status)

async def index(_): return web.FileResponse(ROOT / "static" / "index.html")


def create_app():
    app = web.Application()
    app.router.add_get("/", index); app.router.add_static("/static/", ROOT / "static"); app.router.add_get("/api/sites", sites)
    app.router.add_get("/api/schedule", schedule); app.router.add_get("/api/movies", movie_schedule)
    app.router.add_get("/api/seatmap", seatmap)
    app.router.add_get("/api/cache-status", cache_status)
    async def startup(app):
        await fk.start()
        app["warm_task"] = asyncio.create_task(fk.warm_loop())
    async def cleanup(app):
        task = app.get("warm_task")
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await fk.close()
    app.on_startup.append(startup); app.on_cleanup.append(cleanup)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="127.0.0.1", port=int(os.getenv("PORT", "8799")), print=lambda _: None)
