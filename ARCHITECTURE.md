# HA! Healthcare AI - System Architecture

## Overview

HA! Healthcare AI is a full-stack healthcare assistant application with AI-powered chat, symptom checking, doctor booking, and emergency services.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Vercel - Static Hosting)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  index.html  │  │  chat.html   │  │ symptoms.html│        │
│  │   (Login)    │  │  (AI Chat)   │  │  (Checker)   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ doctors.html │  │appointments  │  │ emergency    │        │
│  │  (Booking)   │  │   .html      │  │   .html      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    JavaScript Layer                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ app.js   │ │ chat.js  │ │symptoms  │ │ doctors  │  │  │
│  │  │(Shared)  │ │(History) │ │  .js     │ │  .js     │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                      CSS Layer                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ style.css│ │ chat.css │ │ login.css│ │ pages.css│  │  │
│  │  │(Global)  │ │(Gemini)  │ │          │ │          │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API SERVER                         │
│                    (Render - Cloud Hosting)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Application                     │ │
│  │                      (main.py)                             │ │
│  │                                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │              API Endpoints                          │ │ │
│  │  │                                                     │ │ │
│  │  │  • POST /auth/register                             │ │ │
│  │  │  • POST /chat                                      │ │ │
│  │  │  • GET  /chat/history/{phone}                     │ │ │
│  │  │  • GET  /chat/session/{chat_id}                   │ │ │
│  │  │  • DELETE /chat/session/{chat_id}                 │ │ │
│  │  │  • POST /symptom-check                            │ │ │
│  │  │  • GET  /doctors                                  │ │ │
│  │  │  • POST /appointments/book                        │ │ │
│  │  │  • GET  /appointments/{phone}                     │ │ │
│  │  │  • POST /emergency/alert                          │ │ │
│  │  │  • GET  /health-tips                              │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                  SQLite Database                          │ │
│  │                (ha_healthcare.db)                         │ │
│  │                                                           │ │
│  │  ┌─────────────────┐      ┌─────────────────────────┐   │ │
│  │  │  users          │      │  chat_history           │   │ │
│  │  ├─────────────────┤      ├─────────────────────────┤   │ │
│  │  │ id (PK)         │      │ id (PK)                 │   │ │
│  │  │ name            │      │ user_phone (FK)         │   │ │
│  │  │ phone (UNIQUE)  │◄─────│ chat_id                 │   │ │
│  │  │ location        │      │ role                    │   │ │
│  │  │ created_at      │      │ message                 │   │ │
│  │  └─────────────────┘      │ created_at              │   │ │
│  │                           └─────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               │ HTTPS API Call
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GROQ CLOUD API                             │
│                  (AI Processing Service)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Model: llama-3.1-8b-instant                                   │
│  Purpose: Generate AI responses for health queries             │
│  Authentication: API Key (GROQ_API_KEY)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. User Registration Flow
```
User → Frontend (index.html)
  ↓
  POST /auth/register
  ↓
Backend (main.py)
  ↓
  INSERT INTO users
  ↓
SQLite Database
  ↓
  Return user_id
  ↓
Frontend (localStorage)
```

### 2. Chat Message Flow
```
User types message → Frontend (chat.html)
  ↓
  Generate chat_id (if new chat)
  ↓
  POST /chat {message, user_phone, chat_id}
  ↓
Backend receives request
  ↓
  Call Groq API with prompt
  ↓
Groq returns AI response
  ↓
Backend saves to database:
  - INSERT user message
  - INSERT AI response
  ↓
  Return AI response to frontend
  ↓
Frontend displays message
  ↓
Frontend reloads chat history
```

### 3. Load Chat History Flow
```
Page loads → Frontend (chat.js)
  ↓
  GET /chat/history/{phone}
  ↓
Backend queries database:
  - SELECT DISTINCT chat_id
  - GROUP BY chat_id
  - Get first message as preview
  ↓
  Return sessions array
  ↓
Frontend displays in sidebar
```

### 4. Load Previous Chat Flow
```
User clicks history item → Frontend
  ↓
  GET /chat/session/{chat_id}
  ↓
Backend queries database:
  - SELECT * WHERE chat_id = ?
  - ORDER BY created_at
  ↓
  Return messages array
  ↓
Frontend:
  - Clear current chat
  - Append all messages
  - Highlight active chat
```

---

## Technology Stack

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling (Gemini-inspired glassmorphism)
- **Vanilla JavaScript** - Logic (no frameworks)
- **marked.js** - Markdown rendering for AI responses
- **localStorage** - Client-side session management

### Backend
- **Python 3.x** - Programming language
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **SQLite** - Database
- **Groq SDK** - AI API client
- **python-dotenv** - Environment variables

### External Services
- **Groq Cloud API** - AI model hosting
- **Render** - Backend hosting
- **Vercel** - Frontend hosting

---

## Security Architecture

### Authentication
- Phone-based identification (no password currently)
- Session stored in localStorage
- User data in SQLite database

### API Security
- CORS enabled (currently allows all origins)
- Environment variables for API keys
- Parameterized SQL queries (prevents SQL injection)

### Data Privacy
- No encryption at rest (SQLite plain text)
- HTTPS in production (Render + Vercel)
- No third-party analytics

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         PRODUCTION                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐              ┌──────────────────────┐
│   Vercel CDN         │              │   Render Cloud       │
│   (Frontend)         │              │   (Backend)          │
│                      │              │                      │
│  • Static files      │◄────HTTPS────┤  • FastAPI app       │
│  • Global CDN        │              │  • SQLite DB         │
│  • Auto SSL          │              │  • Persistent disk   │
│  • Auto deploy       │              │  • Auto deploy       │
└──────────────────────┘              └──────────────────────┘
         │                                      │
         │                                      │
         ▼                                      ▼
┌──────────────────────┐              ┌──────────────────────┐
│   GitHub Repo        │              │   Groq Cloud API     │
│                      │              │                      │
│  • Source code       │              │  • AI model          │
│  • Version control   │              │  • llama-3.1-8b      │
│  • CI/CD trigger     │              │                      │
└──────────────────────┘              └──────────────────────┘
```

---

## File Structure

```
HA-Healthcare-AI/
│
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (not in git)
│   └── ha_healthcare.db        # SQLite database (created at runtime)
│
├── frontend/
│   ├── index.html              # Login page
│   ├── chat.html               # AI Chat with history
│   ├── symptoms.html           # Symptom checker
│   ├── doctors.html            # Doctor listing
│   ├── appointments.html       # Appointments
│   ├── emergency.html          # Emergency SOS
│   │
│   ├── css/
│   │   ├── style.css           # Global variables & resets
│   │   ├── chat.css            # Chat UI (Gemini-inspired)
│   │   ├── login.css           # Login page styles
│   │   └── pages.css           # Other pages styles
│   │
│   └── js/
│       ├── app.js              # Shared utilities & API helpers
│       ├── chat.js             # Chat logic & history
│       ├── login.js            # Login logic
│       ├── symptoms.js         # Symptom checker logic
│       ├── doctors.js          # Doctor booking logic
│       ├── appointments.js     # Appointments logic
│       └── emergency.js        # Emergency logic
│
├── README.md                   # Project overview
├── DEPLOYMENT.md               # Deployment guide
├── CHAT_HISTORY_SUMMARY.md     # Feature implementation summary
├── ARCHITECTURE.md             # This file
├── GIT_COMMANDS.md             # Git deployment commands
├── vercel.json                 # Vercel configuration
└── .gitignore                  # Git ignore rules
```

---

## API Request/Response Examples

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "1234567890",
  "location": "Mumbai"
}

Response:
{
  "success": true,
  "user_id": "a1b2c3d4",
  "name": "John Doe",
  "message": "User registered successfully"
}
```

### Send Chat Message
```http
POST /chat
Content-Type: application/json

{
  "message": "I have a headache",
  "username": "John",
  "user_phone": "1234567890",
  "chat_id": "chat_1234567890_abc123"
}

Response:
{
  "response": "I understand you're experiencing a headache...",
  "timestamp": "2024-01-15T10:30:00"
}
```

### Get Chat History
```http
GET /chat/history/1234567890

Response:
{
  "sessions": [
    {
      "chat_id": "chat_1234567890_abc123",
      "preview": "I have a headache",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

---

## Performance Considerations

### Frontend
- **Lazy Loading:** Chat history loaded once on page load
- **DOM Optimization:** Minimal DOM manipulation
- **CSS Animations:** GPU-accelerated transforms
- **Asset Size:** No heavy frameworks, vanilla JS only

### Backend
- **Database Indexes:** Fast queries on user_phone and chat_id
- **Connection Pooling:** SQLite handles concurrent reads
- **Response Caching:** Static data (doctors) can be cached
- **API Rate Limiting:** Not implemented (consider for production)

### Database
- **SQLite:** Lightweight, serverless, perfect for small-medium scale
- **Indexes:** Optimized for common queries
- **File Size:** Grows with chat history (monitor in production)

---

## Scalability

### Current Limitations
- SQLite: Single-file database (not ideal for high concurrency)
- No caching layer
- No load balancing
- No database replication

### Future Scaling Options
1. **Database:** Migrate to PostgreSQL for better concurrency
2. **Caching:** Add Redis for session management
3. **CDN:** Already using Vercel CDN for frontend
4. **Load Balancing:** Render supports horizontal scaling
5. **Message Queue:** Add for async AI processing

---

## Monitoring & Logging

### Current Setup
- **Backend Logs:** Render provides log streaming
- **Frontend Errors:** Browser console (no tracking)
- **Database:** No query logging

### Recommended Additions
1. **Error Tracking:** Sentry or similar
2. **Analytics:** Google Analytics or Plausible
3. **Performance Monitoring:** New Relic or DataDog
4. **Database Monitoring:** Query performance tracking

---

## Backup & Recovery

### Database Backup
```bash
# Manual backup
cp ha_healthcare.db ha_healthcare_backup.db

# Automated backup (cron job)
0 2 * * * cp /path/to/ha_healthcare.db /path/to/backups/ha_healthcare_$(date +\%Y\%m\%d).db
```

### Disaster Recovery
1. Database stored on Render persistent disk
2. Code in GitHub (version controlled)
3. Environment variables in Render dashboard
4. Frontend on Vercel (auto-deployed from GitHub)

---

## Cost Estimation

### Development (Free Tier)
- **Groq API:** Free tier (limited requests)
- **Render:** Free tier (sleeps after inactivity)
- **Vercel:** Free tier (unlimited bandwidth)
- **GitHub:** Free for public repos

### Production (Estimated)
- **Groq API:** ~$0.10 per 1M tokens
- **Render:** $7/month (Starter plan)
- **Vercel:** Free (Pro $20/month for team features)
- **Total:** ~$7-27/month

---

## Compliance & Legal

### Health Data
- **HIPAA:** Not compliant (no encryption, no BAA)
- **GDPR:** Partial (user can delete chats)
- **Data Retention:** Indefinite (no auto-deletion)

### Disclaimers
- AI responses are informational only
- Not a substitute for professional medical advice
- Emergency: Call 108 (India) or local emergency number

---

**Architecture designed for simplicity, scalability, and maintainability.**
