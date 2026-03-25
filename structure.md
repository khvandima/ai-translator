# AI-Translator — структура проекта

```
AI-Translator/
│
├── app/
│   ├── main.py              # FastAPI app, lifespan, endpoints, QR
│   ├── config.py            # pydantic-settings, читает .env
│   ├── logger.py            # logging → app.log + errors.log
│   ├── session.py           # Redis, создание/get/update сессий, TTL 2ч
│   ├── ws_manager.py
│   ├── translator.py        # Groq API, перевод с контекстом        [ Phase 3 ]
│   ├── stt.py               # Whisper STT, аудио → текст             [ Phase 5 ]
│   ├── tts.py               # Groq TTS / edge-tts, текст → аудио    [ Phase 6 ]
│   └── static/
│       └── index.html       # Мобильный UI, Push-to-Talk             [ Phase 4 ]
│
├── logs/                    # Создаётся автоматически
│   ├── app.log
│   └── errors.log
│
├── tests/
│   ├── __init__.py
│   ├── test_session.py      # pytest тесты сессий
│   ├── test_translator.py   # pytest тесты перевода
│   └── test_ws.py           # pytest тесты WebSocket
│
├── .env                     # Секреты — никогда не коммитить
├── .env.example             # Шаблон для .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml       # FastAPI + Redis
├── pyproject.toml           # pytest конфиг
├── requirements.txt
└── PROGRESS.md              # Лог прогресса по фазам
```

## Статус файлов

| Файл | Статус | Фаза |
|------|--------|------|
| `requirements.txt` | ✅ готово | 1 |
| `app/config.py` | ✅ готово | 1 |
| `app/logger.py` | ✅ готово | 1 |
| `app/session.py` | ✅ готово | 1 |
| `app/main.py` | ✅ готово | 1 |
| `.env.example` | ✅ готово | 1 |
| `app/translator.py` | ⏳ следующее | 3 |
| `app/stt.py` | ⏳ ожидает | 5 |
| `app/tts.py` | ⏳ ожидает | 6 |
| `app/static/index.html` | ⏳ ожидает | 4 |
| `Dockerfile` | ⏳ ожидает | 6 |
| `docker-compose.yml` | ⏳ ожидает | 6 |
| `pyproject.toml` | ⏳ ожидает | — |
| `tests/` | ⏳ ожидает | — |
| `PROGRESS.md` | ⏳ ожидает | — |