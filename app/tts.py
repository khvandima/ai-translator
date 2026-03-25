import base64
import tempfile
import time
from pathlib import Path

import edge_tts
from groq import AsyncGroq

from config import EDGE_TTS_VOICES, settings
from logger import get_logger

log = get_logger(__name__)


class TTS:
    def __init__(self) -> None:
        self._groq = AsyncGroq(api_key=settings.groq_api_key)
        log.info("TTS initialized: primary=groq fallback=edge-tts")

    async def synthesize(self, text: str, language: str, gender: str | None = None) -> str:
        log.info("TTS synthesize lang=%s gender=%s chars=%d", language, gender or settings.tts_voice_gender, len(text))
        try:
            result = await self._groq_tts(text)
            return result
        except Exception as e:
            log.warning("Groq TTS failed: %s — falling back to edge-tts", e)
            return await self._edge_tts(text, language, gender)

    async def _groq_tts(self, text: str) -> str:
        start = time.monotonic()
        response = await self._groq.audio.speech.create(
            model=settings.groq_tts_model,
            voice=settings.groq_tts_voice,
            input=text,
            response_format="wav",
        )
        audio_bytes = response.read()
        elapsed = time.monotonic() - start
        log.info("Groq TTS done in %.2fs: %d bytes", elapsed, len(audio_bytes))
        return base64.b64encode(audio_bytes).decode()

    async def _edge_tts(self, text: str, language: str, gender: str | None = None) -> str:
        gender = gender or settings.tts_voice_gender
        lang_voices = EDGE_TTS_VOICES.get(language, EDGE_TTS_VOICES["en"])
        voice = lang_voices.get(gender, lang_voices["female"])

        log.info("Edge TTS: lang=%s gender=%s voice=%s", language, gender, voice)

        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        start = time.monotonic()
        try:
            await communicate.save(str(tmp_path))
            audio_bytes = tmp_path.read_bytes()
            elapsed = time.monotonic() - start
            log.info("Edge TTS done in %.2fs: %d bytes", elapsed, len(audio_bytes))
            return base64.b64encode(audio_bytes).decode()
        except Exception as e:
            log.error("Edge TTS failed after %.2fs: %s", time.monotonic() - start, e)
            raise
        finally:
            tmp_path.unlink(missing_ok=True)


tts = TTS()