import ipaddress
from datetime import datetime

import httpx
import redis.asyncio as aioredis

from logger import get_logger

log = get_logger(__name__)


class Analytics:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def track_session(
        self,
        language_a: str,
        language_b: str,
        context: str,
        client_ip: str,
    ) -> None:
        try:
            lang_pair = f"{language_a}->{language_b}"
            country = await self._get_country(client_ip)
            date = datetime.utcnow().strftime("%Y-%m-%d")

            pipe = self._redis.pipeline()
            pipe.incr("analytics:sessions:total")
            pipe.incr(f"analytics:sessions:date:{date}")
            pipe.incr(f"analytics:lang:{lang_pair}")
            pipe.incr(f"analytics:context:{context}")
            if country:
                pipe.incr(f"analytics:country:{country}")
            await pipe.execute()

            log.debug("Analytics: session tracked lang=%s context=%s country=%s", lang_pair, context, country)
        except Exception as e:
            log.warning("Analytics track_session failed: %s", e)

    async def track_message(self, mode: str = "text") -> None:
        try:
            pipe = self._redis.pipeline()
            pipe.incr("analytics:messages:total")
            pipe.incr(f"analytics:messages:mode:{mode}")
            await pipe.execute()
        except Exception as e:
            log.warning("Analytics track_message failed: %s", e)

    async def get_stats(self) -> dict:
        try:
            keys_lang = await self._redis.keys("analytics:lang:*")
            keys_context = await self._redis.keys("analytics:context:*")
            keys_country = await self._redis.keys("analytics:country:*")
            keys_date = await self._redis.keys("analytics:sessions:date:*")

            async def get_many(keys: list) -> dict:
                if not keys:
                    return {}
                values = await self._redis.mget(*keys)
                return {
                    k.decode().split(":", 2)[-1]: int(v or 0)
                    for k, v in zip(keys, values)
                }

            total_sessions = int(await self._redis.get("analytics:sessions:total") or 0)
            total_messages = int(await self._redis.get("analytics:messages:total") or 0)
            text_messages = int(await self._redis.get("analytics:messages:mode:text") or 0)
            voice_messages = int(await self._redis.get("analytics:messages:mode:audio") or 0)

            return {
                "sessions": {
                    "total": total_sessions,
                    "by_date": await get_many(keys_date),
                },
                "messages": {
                    "total": total_messages,
                    "text": text_messages,
                    "voice": voice_messages,
                },
                "languages": await get_many(keys_lang),
                "contexts": await get_many(keys_context),
                "countries": await get_many(keys_country),
            }
        except Exception as e:
            log.error("Analytics get_stats failed: %s", e)
            return {}

    async def _get_country(self, ip: str) -> str | None:
        try:
            parsed = ipaddress.ip_address(ip)
            if parsed.is_private or parsed.is_loopback:
                return "LOCAL"
            async with httpx.AsyncClient(timeout=2) as client:
                res = await client.get(f"https://ipapi.co/{ip}/country/")
                if res.status_code == 200:
                    return res.text.strip()
        except Exception:
            pass
        return None


analytics: Analytics | None = None


def get_analytics() -> Analytics:
    if analytics is None:
        raise RuntimeError("Analytics not initialized")
    return analytics


def init_analytics(redis: aioredis.Redis) -> None:
    global analytics
    analytics = Analytics(redis)