# FastAPI WhatsApp & Telegram AI Agent & CRM Template

A production-ready FastAPI boilerplate for building autonomous, multilingual AI sales consultants and customer support agents across **WhatsApp Cloud API** and **Telegram** using OpenAI.

Features persistent multi-turn conversation memory, autonomous tool use (lead qualification, consultation bookings, language preference tracking), dynamic business knowledge retrieval, a real-time dark-mode Admin Live Control Hub & CRM dashboard with channel filtering, live human agent takeover, and secure proactive outbound messaging.

---

## Features

- **Dual-Platform Support (WhatsApp & Telegram)**: Native asynchronous webhook adapters for both Meta WhatsApp Cloud API and Telegram Bot API.
- **Multilingual Intelligence**: Automatically detects and mirrors customer language (English, Pidgin, Yorùbá, Hausa, Igbo, French, Spanish, Arabic, etc.) with language preference storage.
- **Autonomous Tool Calling**:
  - `save_qualified_lead`: Captures client details, niche, interested services, budget, intent score (`HOT`, `WARM`, `COLD`), and notes.
  - `book_service_consultation`: Schedules consultations and strategy sessions directly into the database.
  - `set_preferred_language`: Persists customer language preferences.
- **Dynamic Knowledge Base (`knowledge/business_profile.json`)**: Configurable business identity, services, pricing matrices, and FAQs injected dynamically into prompt context.
- **Real-Time Admin CRM Hub (`/admin`)**:
  - Live dual-platform inbox with search, channel badges (WhatsApp vs Telegram), and lead status filtering.
  - Real-time metrics (Total Contacts, Active Leads, Hot Leads, Bookings, Active Takeovers).
  - **Live Human Takeover**: One-click toggle to pause AI replies for specific chats and send manual replies directly to WhatsApp or Telegram.
  - Lead profiles & consultation booking inspector.
- **Async Database Persistence**: Async SQLAlchemy engine supporting SQLite (`aiosqlite`) locally and PostgreSQL (`asyncpg`, e.g., Neon Postgres) for production.
- **Outbound Automation Endpoints**: Key-protected `POST /whatsapp/send` and `POST /telegram/send` endpoints for n8n workflows, CRM triggers, and scheduled alerts.
- **Production Ready**: Pre-configured Docker, Docker Compose, Railway, Render blueprints, and Cloudflare/LocalTunnel support.

---

## Project Structure

```plaintext
whatsapp-fastapi-agent/
├── api/                   # FastAPI routers
│   ├── admin.py           # Dashboard statistics, chat management, takeover & manual messages
│   ├── dependencies.py    # Authentication & API key verifiers
│   ├── telegram.py        # Telegram webhook listener & outbound send API
│   └── whatsapp.py        # Meta Webhook verification, inbound listener, outbound send API
├── core/                  # Application core
│   ├── config.py          # Pydantic Settings management
│   └── database.py        # Async SQLAlchemy engine, session maker, table initialization
├── knowledge/             # JSON business profiles, service catalogs & FAQs
│   └── business_profile.json
├── models/                # Pydantic & SQLAlchemy ORM models
│   ├── db_models.py       # User, ChatMessage, Lead, ServiceBooking tables
│   └── whatsapp.py        # Webhook payload & outbound message models
├── screenshots/           # UI and bot conversation demonstration images
├── services/              # Business logic layer
│   ├── agent_tools.py     # OpenAI tool definitions & execution handlers
│   ├── knowledge_service.py # Dynamic business profile loader & FAQ search
│   ├── memory_store.py    # Conversation memory helpers
│   ├── openai_service.py  # Prompt engineering, conversation orchestration & LLM calls
│   ├── telegram_service.py# Telegram Bot API sender
│   └── whatsapp_service.py# Meta Graph API sender
├── static/                # Static assets & frontend UI
│   └── admin/index.html   # Real-Time Admin Live Control Hub SPA
├── .env.example           # Environment variables template
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose setup
├── main.py                # FastAPI application entrypoint
├── railway.json           # Railway deployment configuration
├── render.yaml            # Render Blueprint deployment config
├── requirements.txt       # Python package dependencies
├── SETUP_GUIDE.md         # Comprehensive setup & integration guide
└── README.md              # Project overview & quick start
```

---

## Screenshots & Demos

### Admin Live Control Hub & CRM Dashboard
<p align="center">
  <img src="./screenshots/admin-demo.jpg" alt="Admin CRM Dashboard Live Hub" width="100%">
</p>

### Admin Multi-Channel Overview (WhatsApp & Telegram)
<p align="center">
  <img src="./screenshots/admin-demo-wa1.jpg" alt="Admin WhatsApp Chat View" width="49%">
  <img src="./screenshots/admin-demo-tg2.png" alt="Admin Telegram Chat View" width="49%">
</p>

### WhatsApp AI Sales & Support Bot
<p align="center">
  <img src="./screenshots/wabot1.png" alt="WhatsApp AI Agent Demo 1" width="49%">
  <img src="./screenshots/wabot2.png" alt="WhatsApp AI Agent Demo 2" width="49%">
</p>

### Telegram AI Sales & Support Bot
<p align="center">
  <img src="./screenshots/tgbot1.png" alt="Telegram AI Agent Demo 1" width="49%">
  <img src="./screenshots/tgbot2.png" alt="Telegram AI Agent Demo 2" width="49%">
</p>

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Meta Business Account & Developer App with WhatsApp Cloud API enabled
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/samolubukun/FastAPI-WhatsApp-Telegram-AI-Agent-CRM-Template.git
cd FastAPI-WhatsApp-Telegram-AI-Agent-CRM-Template

# Create & activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure the following variables in `.env`:
```env
ENVIRONMENT="development"

# Meta / WhatsApp Credentials
VERIFY_TOKEN="your_webhook_verify_token"
WHATSAPP_TOKEN="your_permanent_whatsapp_system_user_token"
PHONE_NUMBER_ID="your_whatsapp_phone_number_id"
WHATSAPP_API_VERSION="v22.0"

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_WEBHOOK_SECRET="your_telegram_webhook_secret"

# Database (SQLite default or PostgreSQL)
DATABASE_URL="sqlite+aiosqlite:///./whatsapp_agent.db"
# Postgres: "postgresql+asyncpg://user:password@host/dbname?sslmode=require"

# OpenAI
OPENAI_API_KEY="sk-..."
OPENAI_MODEL_NAME="gpt-4o-mini"
MEMORY_HISTORY_LIMIT=30

# Security for Admin & Outbound API
INTERNAL_API_KEY="your_secure_internal_api_key"
```

> For detailed instructions on generating tokens (Meta Permanent Token, Secret Keys), configuring Cloudflare/localtunnel, or connecting n8n, see [SETUP_GUIDE.md](./SETUP_GUIDE.md).

### 4. Run Locally

```bash
uvicorn main:app --reload --port 8000
```

- **Health Check**: `http://127.0.0.1:8000/`
- **Admin Control Hub**: `http://127.0.0.1:8000/admin`
- **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`

---

## Local Webhook Testing

You can simulate WhatsApp webhook messages locally without Meta:

1. Create a `test_payload.json` file:
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "123456789",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "YOUR_PHONE_NUMBER_ID"
            },
            "contacts": [
              {
                "profile": { "name": "Test User" },
                "wa_id": "1234567890"
              }
            ],
            "messages": [
              {
                "from": "1234567890",
                "id": "wamid.test_message_123",
                "timestamp": "1701108242",
                "text": { "body": "Hi, I would like to book a consultation for cargo freight." },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

2. Send the request via PowerShell / curl:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/whatsapp/webhook -Method POST -Headers @{ "Content-Type" = "application/json" } -Body (Get-Content -Raw .\test_payload.json)
```

3. Open `http://127.0.0.1:8000/admin` to see the conversation, lead qualification, and booking in real time.

---

## Knowledge Base Customization

To customize business identity, offerings, pricing, and responses:
1. Open [`knowledge/business_profile.json`](./knowledge/business_profile.json).
2. Edit business details, services, pricing matrices, and FAQ entries.
3. The AI agent automatically incorporates updates on every query.

---

## Outbound API (n8n / External Triggers)

Trigger proactive outbound messages:

- **WhatsApp**: `POST /whatsapp/send`
- **Telegram**: `POST /telegram/send`
- **Header**: `x-api-key: <INTERNAL_API_KEY>`
- **Payload**:
```json
{
  "to": "1234567890",
  "text": "Hello! Your appointment is scheduled for tomorrow at 10:00 AM."
}
```

---

## Deployment

### Docker
```bash
docker build -t fastapi-ai-agent .
docker run -p 8000:8000 --env-file .env fastapi-ai-agent
```

### Railway
Deploy directly via GitHub repository linking using the included [`railway.json`](./railway.json). Set environment variables in Railway Dashboard.

### Render
Deploy via Blueprint using the included [`render.yaml`](./render.yaml).

---

## License

MIT License. Free for personal and commercial use.
