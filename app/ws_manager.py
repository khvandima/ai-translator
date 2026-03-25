import json

from fastapi import WebSocket

from logger import get_logger

log = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, user_role: str, ws: WebSocket) -> None:
        await ws.accept()
        if session_id not in self._rooms:
            self._rooms[session_id] = {}
        self._rooms[session_id][user_role] = ws
        total_in_room = len(self._rooms[session_id])
        log.info(
            "WS connected: session=%s role=%s peers=%d total_rooms=%d",
            session_id, user_role, total_in_room, len(self._rooms)
        )

    def disconnect(self, session_id: str, user_role: str) -> None:
        room = self._rooms.get(session_id, {})
        room.pop(user_role, None)
        if not room:
            self._rooms.pop(session_id, None)
            log.info("WS room closed: session=%s total_rooms=%d", session_id, len(self._rooms))
        else:
            log.info("WS disconnected: session=%s role=%s peers_left=%d", session_id, user_role, len(room))

    def is_full(self, session_id: str) -> bool:
        return len(self._rooms.get(session_id, {})) >= 2

    def partner_role(self, user_role: str) -> str:
        return "user_b" if user_role == "user_a" else "user_a"

    async def send(self, session_id: str, user_role: str, payload: dict) -> None:
        ws = self._rooms.get(session_id, {}).get(user_role)
        if not ws:
            log.warning("Send failed: no socket for session=%s role=%s", session_id, user_role)
            return
        await ws.send_text(json.dumps(payload, ensure_ascii=False))

    async def broadcast(self, session_id: str, payload: dict) -> None:
        room = self._rooms.get(session_id, {})
        if not room:
            log.warning("Broadcast skipped: empty room session=%s", session_id)
            return
        event = payload.get("event", "unknown")
        log.debug("Broadcast session=%s event=%s to %d peers", session_id, event, len(room))
        for ws in room.values():
            await ws.send_text(json.dumps(payload, ensure_ascii=False))

    async def send_to_partner(self, session_id: str, sender_role: str, payload: dict) -> None:
        partner = self.partner_role(sender_role)
        log.debug("Send to partner: session=%s from=%s to=%s", session_id, sender_role, partner)
        await self.send(session_id, partner, payload)


ws_manager = ConnectionManager()