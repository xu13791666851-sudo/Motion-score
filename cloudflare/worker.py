"""Public API for Motion Score. Activity records are stored by each browser."""

import asyncio
import json
from urllib.parse import parse_qs, urlencode, urlsplit

from js import AbortSignal, Object, Uint8Array, fetch as fetch_url
from pyodide.ffi import to_js
from workers import Response, WorkerEntrypoint

import amap_service as maps
import planner
from catalog_data import CATALOG_JSON

CATALOG = json.loads(CATALOG_JSON)
MAP_PATHS = {"/api/map/image", "/api/map/route", "/api/map/convert"}


def js_object(value):
    return to_js(value, dict_converter=Object.fromEntries)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, allow_nan=False),
        status=status,
        headers={"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"},
    )


async def provider_request(url, *, timeout=12_000, **options):
    return await fetch_url(url, js_object({
        **options, "signal": AbortSignal.timeout(timeout), "redirect": "manual",
    }))


async def amap_request(key, path, params, binary=False):
    if not key:
        raise maps.MapError("线上高德地图服务尚未配置。")
    try:
        response = await provider_request(maps.BASE + path + "?" + urlencode({**params, "key": key}))
        if not response.ok:
            raise OSError()
        mime = (response.headers.get("content-type") or "").split(";")[0]
        raw = Uint8Array.new(await response.arrayBuffer()).to_py().tobytes()
    except Exception:
        raise maps.MapError("高德服务暂时未能连接，请稍后重试。") from None
    return maps.decode_response(raw, mime, binary)


async def find_place(key, address, params):
    result = await amap_request(key, "/v3/geocode/geo", params)
    return maps.decode_geocode(address, result)


async def plan_route(key, data):
    mode, start, end = maps.route_inputs(data)
    start_params = maps.geocode_params(start)
    end_params = maps.geocode_params(end)
    origin, destination = await asyncio.gather(
        find_place(key, start, start_params),
        find_place(key, end, end_params),
    )
    path, params = maps.route_params(mode, origin, destination)
    return maps.decode_route(mode, origin, destination, await amap_request(key, path, params))


async def generate(data, api_key, model):
    req = planner.normalize(data)
    if api_key:
        body = planner.deepseek_body(req, CATALOG, model)
        try:
            response = await provider_request(
                "https://api.deepseek.com/chat/completions",
                method="POST", timeout=25_000,
                headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                body=json.dumps(body, ensure_ascii=False),
            )
            if not response.ok:
                raise OSError()
            payload = json.loads(await response.text())
            intent = planner.decode_deepseek(payload, CATALOG)
        except Exception:
            message = "DeepSeek 暂时无法完成编排，已使用规则继续。"
        else:
            return planner.build_plan(req, CATALOG, intent, "deepseek", "DeepSeek 理解文字需求，已校验歌单。")
    else:
        message = "当前使用规则编排。"
    return planner.build_plan(req, CATALOG, planner.local_intent(req), "rules", message)


async def request_data(request):
    try:
        if int(request.headers.get("Content-Length") or 0) > 450_000:
            raise ValueError()
        raw = await request.text()
        if len(raw) > 450_000:
            raise ValueError()
        return json.loads(raw)
    except (ValueError, TypeError):
        raise planner.InputError("请求资料无效或过大。") from None


def map_image_params(query):
    fields = parse_qs(query, max_num_fields=8)

    def value(name, default=None):
        try:
            return float(fields.get(name, [default])[0])
        except (ValueError, TypeError):
            raise planner.InputError("地图中心、缩放或尺寸参数无效。") from None

    return maps.static_map_params([value("lng"), value("lat")], value("zoom", 13), value("height", 320))


class Default(WorkerEntrypoint):
    def setting(self, key):
        value = getattr(self.env, key, None)
        return value.strip() if isinstance(value, str) else ""

    async def fetch(self, request):
        url = urlsplit(request.url)
        method, path = request.method, url.path
        if path == "/":
            return Response("", status=302, headers={"Location": "/mobile-app.html"})
        if not path.startswith("/api/"):
            return Response("Not found", status=404)

        amap_key = self.setting("AMAP_WEB_SERVICE_KEY")
        ai_key = self.setting("DEEPSEEK_API_KEY")
        try:
            if method == "GET":
                if path == "/api/health":
                    return json_response({"ok": True, "application": "motion-score-online",
                                          "deepseekConfigured": bool(ai_key), "amapConfigured": bool(amap_key)})
                if path == "/api/map/config":
                    return json_response({"configured": bool(amap_key), "provider": "amap"})
                if path == "/api/catalog":
                    return json_response({"tracks": CATALOG})
                if path == "/api/playlist":
                    return json_response({"tracks": CATALOG, "source": "demo"})
                if path == "/api/location":
                    return json_response({"latitude": 22.503, "longitude": 113.956, "source": "demo"})

            caller = request.headers.get("CF-Connecting-IP") or "unknown"
            limiter = None
            if (method == "GET" and path == "/api/map/image") or (method == "POST" and path in MAP_PATHS):
                limiter = self.env.MAP_LIMIT
            elif method == "POST" and path == "/api/playlist/generate":
                limiter = self.env.MUSIC_LIMIT
            if limiter is not None and not (await limiter.limit(js_object({"key": caller}))).success:
                return json_response({"error": "请求过于频繁，请稍后再试。"}, 429)

            if method == "GET" and path == "/api/map/image":
                image, mime = await amap_request(amap_key, "/v3/staticmap", map_image_params(url.query), binary=True)
                return Response(image, headers={"Content-Type": mime, "Cache-Control": "private, max-age=300"})

            if method == "POST" and path in {
                "/api/playlist/generate", "/api/playlist/preview", "/api/playlist/adjust", "/api/map/route", "/api/map/convert",
            }:
                data = await request_data(request)
                if path == "/api/playlist/generate":
                    return json_response(await generate(data, ai_key, self.setting("DEEPSEEK_MODEL") or "deepseek-flash"))
                if path == "/api/playlist/preview":
                    return json_response(planner.plan(data, catalog=CATALOG, use_ai=False))
                if path == "/api/playlist/adjust":
                    return json_response(planner.adjust(data, catalog=CATALOG))
                if path == "/api/map/route":
                    return json_response(await plan_route(amap_key, data))
                params, count = maps.convert_params(data)
                result = await amap_request(amap_key, "/v3/assistant/coordinate/convert", params)
                return json_response(maps.decode_conversion(count, result))
        except (planner.InputError, ValueError) as exc:
            if isinstance(exc, maps.MapError):
                return json_response({"error": str(exc)}, 502)
            if isinstance(exc, planner.InputError):
                return json_response({"error": str(exc)}, 400)
            return json_response({"error": "地图参数无效或返回数据格式错误。"}, 400)
        except (TypeError, KeyError, IndexError):
            return json_response({"error": "服务暂时无法读取返回结果，请稍后重试。"}, 502)

        return json_response({"error": "这个接口不可用。"}, 404)
