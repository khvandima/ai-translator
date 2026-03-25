import time

from groq import AsyncGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import CONTEXT_PROMPTS, LANGUAGE_NAMES, settings
from logger import get_logger

log = get_logger(__name__)


class Translator:
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        log.info("Translator initialized: model=%s", settings.groq_model)

    def _system_prompt(self, source_lang: str, target_lang: str, context: str) -> str:
        base = CONTEXT_PROMPTS.get(context, CONTEXT_PROMPTS["general"])
        src = LANGUAGE_NAMES.get(source_lang, source_lang)
        tgt = LANGUAGE_NAMES.get(target_lang, target_lang)
        return (
            f"{base}\n\n"
            f"Translate from {src} to {tgt}.\n"
            f"Return ONLY the translation. No explanations, no notes, no punctuation changes."
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "general",
    ) -> str:
        if source_lang == target_lang:
            log.debug("Same language [%s], skipping translation", source_lang)
            return text

        log.info("Translating [%s→%s][%s] %d chars", source_lang, target_lang, context, len(text))
        log.debug("Text preview: %s", text[:80])

        start = time.monotonic()
        try:
            response = await self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": self._system_prompt(source_lang, target_lang, context)},
                    {"role": "user", "content": text},
                ],
                max_tokens=1000,
                temperature=0.2,
            )
            translated = response.choices[0].message.content.strip()
            elapsed = time.monotonic() - start
            log.info("Translation done [%s→%s] %.2fs | result: %s", source_lang, target_lang, elapsed, translated[:60])
            return translated

        except Exception as e:
            elapsed = time.monotonic() - start
            log.error("Translation failed [%s→%s] after %.2fs: %s", source_lang, target_lang, elapsed, e)
            raise


translator = Translator()