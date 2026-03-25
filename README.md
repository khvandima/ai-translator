# AI-Translator

Real-time AI translation for two people speaking different languages — no registration, no app install, just scan a QR code and talk.

## How it works

1. **User A** opens the site, selects their language and conversation context, gets a QR code
2. **User B** scans the QR code, selects their language
3. Both are connected — they can type or speak, everything is translated instantly
4. Each person sees the conversation in their own language (large) with the original underneath (small)

## Features

- **Three input modes** — text, push-to-talk (voice), or both
- **Real-time translation** via Groq (llama-3.3-70b-versatile)
- **Speech recognition** via Whisper (local, no API cost)
- **Text-to-speech** via Groq TTS with edge-tts fallback
- **Voice toggle** — switch between audio and text-only at any time
- **6 translation contexts** — General, Medical, Banking, Police, Tourism, Legal
- **Cultural awareness** — prompts adapted for honorifics, politeness levels, local expressions
- **12 languages** — RU, EN, ES, FR, ZH, TR, IT, JA, KO, TH, VI, HI
- **Anonymous analytics** — language pairs, contexts, countries tracked in Redis
- **QR sessions** — expire after 2 hours, no data stored permanently

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI |
| Real-time | WebSocket |
| Sessions | Redis (TTL 2h) |
| Translation | Groq API (llama-3.3-70b-versatile) |
| STT | Whisper (base) |
| TTS | Groq TTS + edge-tts fallback |
| Frontend | Vanilla HTML/JS (mobile-first) |
| Deploy | Railway (FastAPI + Redis plugin) |

## Project structure

```
ai-translator/
├── app/
│   ├── main.py           # FastAPI app, endpoints, WebSocket
│   ├── config.py         # Settings, language/context/voice config
│   ├── logger.py         # Logging to app.log + errors.log
│   ├── session.py        # Redis session management
│   ├── ws_manager.py     # WebSocket room manager
│   ├── translator.py     # Groq translation
│   ├── stt.py            # Whisper speech-to-text
│   ├── tts.py            # Groq TTS + edge-tts fallback
│   ├── analytics.py      # Anonymous usage tracking
│   └── static/
│       └── index.html    # Mobile UI
├── tests/
├── logs/                 # Created automatically
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
└── PROGRESS.md
```

## Getting started

### Prerequisites

- Python 3.12+
- Redis
- ffmpeg (`brew install ffmpeg` / `apt install ffmpeg`)
- Groq API key — [console.groq.com](https://console.groq.com)

### Local setup

```bash
# Clone the repo
git clone https://github.com/your-username/ai-translator
cd ai-translator

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Start Redis (or use Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Run the app
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

### Docker (recommended)

```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env

docker-compose up --build
```

## Environment variables

```env
GROQ_API_KEY=           # Required — get from console.groq.com
REDIS_URL=              # Default: redis://localhost:6379
QR_BASE_URL=            # Your public URL (for QR code links)
ADMIN_TOKEN=            # Secret token for /admin/stats
WHISPER_MODEL=base      # base / small / medium
TTS_VOICE_GENDER=female # female / male
```

Full list in `.env.example`.

## Admin analytics

```
GET /admin/stats?token=your-admin-token
```

Returns session counts, language pairs, contexts, countries, and message modes.

## Deploy to Railway

1. Push code to GitHub
2. [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Add Redis: **+ New** → **Database** → **Redis**
4. Set environment variables in Railway dashboard:
   - `GROQ_API_KEY`
   - `QR_BASE_URL` = `https://your-app.up.railway.app`
   - `ADMIN_TOKEN`
   - `REDIS_URL` = auto-filled by Railway Redis plugin
5. Deploy — Railway reads `Dockerfile` automatically

## Translation contexts

| Context | Use case | Special handling |
|---------|----------|-----------------|
| General | Everyday conversation | Cultural tone adaptation |
| Medical | Hospital, clinic | Clinical terminology, symptom metaphors |
| Banking | Bank, finance | Local financial terms |
| Police | Law enforcement | Word-for-word legal accuracy |
| Tourism | Travel, hospitality | Friendly, local expressions |
| Legal | Contracts, legal proceedings | Literal translation + original in brackets |

## Roadmap

- [ ] Auth (email + Google OAuth)
- [ ] Session history
- [ ] More languages
- [ ] Auto language detection
- [ ] Admin dashboard UI

## License

MIT