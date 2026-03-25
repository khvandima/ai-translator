import json
import secrets
from dataclasses import asdict, dataclass, field
from typing import Optional

import redis.asyncio as aioredis

from config import settings
from logger import get_logger

log = get_logger(__name__)


@dataclass
class Session:
    session_id: str
    language_a: str = "en"
    language_b: str = "ru"
    context: str = "general"
    user_a_connected: bool = False
    user_b_connected: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(**data)


class SessionManager:
    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._redis = await aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
        log.info("Redis connected: %s", settings.redis_url)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.aclose()
            log.info("Redis disconnected")

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def create(
        self,
        language_a: str = "en",
        language_b: str = "ru",
        context: str = "general",
    ) -> Session:
        session_id = secrets.token_urlsafe(8)
        session = Session(
            session_id=session_id,
            language_a=language_a,
            language_b=language_b,
            context=context,
        )
        await self._redis.setex(
            self._key(session_id),
            settings.session_ttl,
            json.dumps(session.to_dict()),
        )
        log.info("Session created: %s", session_id)
        return session

    async def get(self, session_id: str) -> Optional[Session]:
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return None
        return Session.from_dict(json.loads(raw))

    async def update(self, session: Session) -> None:
        exists = await self._redis.exists(self._key(session.session_id))
        if not exists:
            log.warning("Update on missing session: %s", session.session_id)
            return
        await self._redis.setex(
            self._key(session.session_id),
            settings.session_ttl,
            json.dumps(session.to_dict()),
        )

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
        log.info("Session deleted: %s", session_id)


session_manager = SessionManager()