import base64
import tempfile
import time
from pathlib import Path

import whisper

from config import settings
from logger import get_logger

log = get_logger(__name__)

_model: whisper.Whisper | None = None


def get_model() -> whisper.Whisper:
    global _model
    if _model is None:
        log.info("Loading Whisper model: %s", settings.whisper_model)
        start = time.monotonic()
        _model = whisper.load_model(settings.whisper_model)
        log.info("Whisper model loaded in %.2fs", time.monotonic() - start)
    return _model


async def transcribe(audio_b64: str, mime_type: str = "audio/webm") -> str:
    audio_bytes = base64.b64decode(audio_b64)
    size_kb = len(audio_bytes) / 1024
    log.info("STT received %.1f KB audio [%s]", size_kb, mime_type)

    suffix = ".webm" if "webm" in mime_type else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)

    start = time.monotonic()
    try:
        model = get_model()
        result = model.transcribe(str(tmp_path), fp16=False)
        text = result["text"].strip()
        elapsed = time.monotonic() - start

        if text:
            log.info("STT done in %.2fs: %s", elapsed, text[:80])
        else:
            log.warning("STT returned empty result in %.2fs", elapsed)

        return text
    except Exception as e:
        log.error("STT failed after %.2fs: %s", time.monotonic() - start, e)
        raise
    finally:
        tmp_path.unlink(missing_ok=True)