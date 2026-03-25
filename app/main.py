import json
from contextlib import asynccontextmanager
from io import BytesIO

import qrcode
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analytics import analytics, init_analytics
from config import settings
from logger import get_logger
from session import session_manager
from stt import transcribe
from translator import translator
from tts import tts
from ws_manager import ws_manager

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting %s...", settings.app_name)
    await session_manager.connect()
    init_analytics(session_manager._redis)
    log.info("%s started successfully", settings.app_name)
    yield
    log.info("Shutting down %s...", settings.app_name)
    await session_manager.disconnect()
    log.info("Shutdown complete")


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class CreateSessionRequest(BaseModel):
    language_a: str = "ru"
    language_b: str = "en"
    context: str = "general"


class CreateSessionResponse(BaseModel):
    session_id: str
    join_url: str
    qr_url: str


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/admin/stats")
async def admin_stats(token: str = ""):
    if token != settings.admin_token:
        log.warning("Admin stats: invalid token attempt")
        raise HTTPException(status_code=403, detail="Forbidden")
    log.info("Admin stats requested")
    return await analytics.get_stats()


@app.post("/session", response_model=CreateSessionResponse)
async def create_session(request: Request, body: CreateSessionRequest):
    log.info("Create session: lang_a=%s lang_b=%s context=%s", body.language_a, body.language_b, body.context)

    session = await session_manager.create(
        language_a=body.language_a,
        language_b=body.language_b,
        context=body.context,
    )
    join_url = f"{settings.qr_base_url}/join/{session.session_id}"

    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    await analytics.track_session(
        language_a=body.language_a,
        language_b=body.language_b,
        context=body.context,
        client_ip=client_ip,
    )

    log.info("Session created: id=%s ip=%s", session.session_id, client_ip)
    return CreateSessionResponse(
        session_id=session.session_id,
        join_url=join_url,
        qr_url=f"{settings.qr_base_url}/session/{session.session_id}/qr",
    )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    session = await session_manager.get(session_id)
    if not session:
        log.warning("Session not found: %s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.get("/session/{session_id}/qr")
async def get_qr(session_id: str):
    session = await session_manager.get(session_id)
    if not session:
        log.warning("QR requested for missing session: %s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")
    join_url = f"{settings.qr_base_url}/join/{session_id}"
    img = qrcode.make(join_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    log.debug("QR generated for session: %s", session_id)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/join/{session_id}", response_class=HTMLResponse)
async def join_session(session_id: str):
    session = await session_manager.get(session_id)
    if not session:
        log.warning("Join attempt for missing session: %s", session_id)
        return HTMLResponse("<h2>Сессия не найдена или истекла</h2>", status_code=404)
    if ws_manager.is_full(session_id):
        log.warning("Join attempt for full session: %s", session_id)
        return HTMLResponse("<h2>Сессия уже занята</h2>", status_code=403)
    log.info("Join page served: session=%s", session_id)
    with open("app/static/index.html") as f:
        html = f.read()
    return HTMLResponse(html)


@app.websocket("/ws/{session_id}/{user_role}")
async def websocket_endpoint(ws: WebSocket, session_id: str, user_role: str):
    if user_role not in ("user_a", "user_b"):
        log.warning("WS rejected: invalid role=%s session=%s", user_role, session_id)
        await ws.close(code=4000)
        return

    session = await session_manager.get(session_id)
    if not session:
        log.warning("WS rejected: session not found=%s", session_id)
        await ws.close(code=4004)
        return

    if ws_manager.is_full(session_id) and user_role not in ws_manager._rooms.get(session_id, {}):
        log.warning("WS rejected: session full=%s role=%s", session_id, user_role)
        await ws.close(code=4003)
        return

    await ws_manager.connect(session_id, user_role, ws)

    my_lang = session.language_a if user_role == "user_a" else session.language_b
    partner_lang = session.language_b if user_role == "user_a" else session.language_a

    await ws_manager.send(session_id, user_role, {
        "event": "connected",
        "role": user_role,
        "my_language": my_lang,
        "partner_language": partner_lang,
        "context": session.context,
        "session_id": session_id,
    })

    partners = len(ws_manager._rooms.get(session_id, {}))
    if partners == 2:
        log.info("Session full, both users connected: session=%s", session_id)
    await ws_manager.broadcast(session_id, {
        "event": "partner_joined" if partners == 2 else "waiting",
        "message": "Собеседник подключился" if partners == 2 else "Ожидание собеседника...",
    })

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            event = data.get("event")

            if event == "message":
                original_text = data.get("text", "").strip()
                if not original_text:
                    continue

                log.info("Text message: session=%s role=%s chars=%d", session_id, user_role, len(original_text))

                translated_text = await translator.translate(
                    text=original_text,
                    source_lang=my_lang,
                    target_lang=partner_lang,
                    context=session.context,
                )
                await analytics.track_message(mode="text")

                await ws_manager.send(session_id, user_role, {
                    "event": "message",
                    "role": user_role,
                    "original": original_text,
                    "translated": translated_text,
                    "from_me": True,
                })
                await ws_manager.send_to_partner(session_id, user_role, {
                    "event": "message",
                    "role": user_role,
                    "original": translated_text,
                    "translated": original_text,
                    "from_me": False,
                })

            elif event == "audio":
                audio_b64 = data.get("data", "")
                mime_type = data.get("mime_type", "audio/webm")
                if not audio_b64:
                    continue

                log.info("Audio message: session=%s role=%s", session_id, user_role)

                original_text = await transcribe(audio_b64, mime_type)
                if not original_text:
                    log.warning("Empty transcription: session=%s role=%s", session_id, user_role)
                    continue

                translated_text = await translator.translate(
                    text=original_text,
                    source_lang=my_lang,
                    target_lang=partner_lang,
                    context=session.context,
                )
                tts_b64 = await tts.synthesize(translated_text, partner_lang)
                await analytics.track_message(mode="audio")

                await ws_manager.send(session_id, user_role, {
                    "event": "message",
                    "role": user_role,
                    "original": original_text,
                    "translated": translated_text,
                    "from_me": True,
                })
                await ws_manager.send_to_partner(session_id, user_role, {
                    "event": "message",
                    "role": user_role,
                    "original": translated_text,
                    "translated": original_text,
                    "from_me": False,
                    "audio": tts_b64,
                })

            elif event == "ping":
                await ws_manager.send(session_id, user_role, {"event": "pong"})

    except WebSocketDisconnect:
        log.info("WS disconnected: session=%s role=%s", session_id, user_role)
        ws_manager.disconnect(session_id, user_role)
        await ws_manager.broadcast(session_id, {
            "event": "partner_left",
            "message": "Собеседник отключился",
        })
    except Exception as e:
        log.error("WS error: session=%s role=%s error=%s", session_id, user_role, e)
        ws_manager.disconnect(session_id, user_role)