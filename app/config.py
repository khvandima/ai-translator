from pydantic_settings import BaseSettings, SettingsConfigDict


LANGUAGE_NAMES: dict[str, str] = {
    "ru": "Russian",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese",
    "tr": "Turkish",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese",
    "hi": "Hindi",
}

CONTEXT_PROMPTS: dict[str, str] = {
    "general": (
        "You are a professional translator with deep cultural knowledge. "
        "Translate naturally and accurately. "
        "Adapt tone, formality, and expressions to match the cultural norms of the target language. "
        "For Japanese/Korean: use appropriate honorifics and politeness levels. "
        "For Thai: include appropriate polite particles (ครับ/ค่ะ) where natural. "
        "For Hindi: use respectful forms (आप) in formal contexts. "
        "For Vietnamese: apply correct pronouns based on context (anh/chị/em). "
        "Preserve the original meaning while sounding natural to a native speaker."
    ),
    "medical": (
        "You are a medical interpreter with cultural competency. "
        "Use precise clinical terminology appropriate to the target language. "
        "Translate symptoms, diagnoses, and instructions accurately — never omit or soften. "
        "Adapt medical terms to locally used equivalents where they exist. "
        "For Asian languages: be aware that patients may describe symptoms metaphorically "
        "(e.g. 'wind in the stomach', 'hot/cold imbalance') — translate literally and clinically. "
        "Maintain a calm, professional, reassuring tone appropriate to medical settings."
    ),
    "banking": (
        "You are a banking interpreter with knowledge of local financial customs. "
        "Use formal financial terminology standard in the target language's banking sector. "
        "Translate account details, transactions, and legal terms precisely. "
        "Be aware that financial concepts (credit scoring, collateral, interest) "
        "may have culturally specific connotations — use the locally understood term. "
        "Maintain a formal, professional tone at all times."
    ),
    "police": (
        "You are a legal and police interpreter. "
        "Translate rights, statements, and instructions word for word — never paraphrase legal statements. "
        "Use formal register appropriate to law enforcement in the target language. "
        "Be culturally sensitive: in some cultures direct questions from authority may cause distress — "
        "maintain accuracy while using a calm, neutral tone. "
        "Miranda rights and legal warnings must be translated with full precision."
    ),
    "tourism": (
        "You are a travel and hospitality interpreter. "
        "Use friendly, warm, and natural language appropriate to the target culture. "
        "Adapt greetings and pleasantries to local customs "
        "(e.g. more formal in Japanese/Korean, more casual in Spanish/Italian). "
        "Translate directions, bookings, and casual conversation naturally. "
        "Use locally recognised place names and transport terms where applicable."
    ),
    "legal": (
        "You are a legal interpreter specialising in cross-cultural legal translation. "
        "Use formal legal terminology standard in the target jurisdiction where possible. "
        "Translate contracts, rights, and legal statements with exact precision — never simplify. "
        "Note that legal concepts may not have direct equivalents across legal systems; "
        "in such cases translate the term literally and add the original in parentheses. "
        "Maintain a strictly formal register at all times."
    ),
}

EDGE_TTS_VOICES: dict[str, dict[str, str]] = {
    "ru": {"female": "ru-RU-SvetlanaNeural",  "male": "ru-RU-DmitryNeural"},
    "en": {"female": "en-US-JennyNeural",     "male": "en-US-GuyNeural"},
    "es": {"female": "es-ES-ElviraNeural",    "male": "es-ES-AlvaroNeural"},
    "fr": {"female": "fr-FR-DeniseNeural",    "male": "fr-FR-HenriNeural"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural",  "male": "zh-CN-YunxiNeural"},
    "tr": {"female": "tr-TR-EmelNeural",      "male": "tr-TR-AhmetNeural"},
    "it": {"female": "it-IT-ElsaNeural",      "male": "it-IT-DiegoNeural"},
    "ja": {"female": "ja-JP-NanamiNeural",    "male": "ja-JP-KeitaNeural"},
    "ko": {"female": "ko-KR-SunHiNeural",     "male": "ko-KR-InJoonNeural"},
    "th": {"female": "th-TH-PremwadeeNeural", "male": "th-TH-NiwatNeural"},
    "vi": {"female": "vi-VN-HoaiMyNeural",    "male": "vi-VN-NamMinhNeural"},
    "hi": {"female": "hi-IN-SwaraNeural",     "male": "hi-IN-MadhurNeural"},
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "AI-Translator"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Redis
    redis_url: str = "redis://localhost:6379"
    session_ttl: int = 7200  # 2 hours

    # Groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_tts_model: str = "playai-tts"
    groq_tts_voice: str = "Celeste-PlayAI"

    # Whisper
    whisper_model: str = "base"

    # QR
    qr_base_url: str = "http://localhost:8000"

    # Admin
    admin_token: str = ""

    # Providers
    translator_provider: str = "groq"
    tts_provider: str = "groq"
    stt_provider: str = "whisper"

    # TTS default gender
    tts_voice_gender: str = "female"


settings = Settings()