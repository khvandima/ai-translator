# AI-Translator — Progress Log

## Статус: Phase 1-6 готовы, деплой следующий

---

## Решения принятые в проекте

| Тема | Решение | Причина |
|------|---------|---------|
| Регистрация | Без регистрации на старте | Скорость MVP, auth добавим позже |
| Аналитика | Анонимная через Redis | Языки, контексты, страна по IP |
| Деплой | Railway | FastAPI + Redis + WebSocket из коробки |
| БД | Redis only | TTL сессий, скорость, нет нужды в персистентности |
| Перевод | Groq llama-3.3-70b | Скорость + бесплатный тир |
| STT | Whisper base | Локально, без API затрат |
| TTS | Groq TTS + edge-tts fallback | Надёжность |
| Фронт | Статичный index.html | UI простой, React избыточен |

---

## Лог изменений

### Phase 1 — Backend core ✅
- `config.py` — pydantic-settings, LANGUAGE_NAMES, CONTEXT_PROMPTS, EDGE_TTS_VOICES
- `logger.py` — app.log + errors.log, путь относительно корня проекта
- `session.py` — Redis, TTL 2ч, create/get/update/delete
- `main.py` — FastAPI, health endpoint, create session, QR endpoint

### Phase 2 — WebSocket + QR join ✅
- `ws_manager.py` — менеджер комнат, broadcast, send_to_partner
- `main.py` — `/ws/{session_id}/{user_role}`, `/join/{session_id}`
- События: connected, waiting, partner_joined, partner_left, message, ping/pong

### Phase 3 — Перевод ✅
- `translator.py` — Groq API, 6 контекстов, retry через tenacity
- Подключён в main.py, перевод в реальном времени

### Phase 4 — UI ✅
- `index.html` — мобильный first, тёмная тема
- Экраны: setup (User A), qr (ожидание), join (User B), chat
- UX: своё сообщение крупно + перевод мелко, чужое — уже переведённое крупно + оригинал мелко

### Phase 5 — STT ✅
- `stt.py` — Whisper, синглтон модели, temp файл → транскрипция → удаление
- Push-to-Talk в браузере через MediaRecorder → base64 → WebSocket

### Phase 6 — TTS ✅
- `tts.py` — Groq TTS основной, edge-tts fallback, мужские и женские голоса
- Переключатель voice on/off в шапке чата
- Анимация эквалайзера при воспроизведении

---

## Следующие шаги

- [ ] Dockerfile + docker-compose.yml
- [ ] Деплой на Railway
- [ ] Тест с телефона (реальный QR)
- [ ] Аналитика (логирование языков, контекстов, страны по IP)
- [ ] Auth (email + Google) — Phase 2+