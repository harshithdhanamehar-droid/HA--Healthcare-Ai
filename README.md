# HA! — AI-Powered Healthcare 🏥

> **"AI-Powered Healthcare, Anytime, Anywhere!"**
> The `!` in HA! represents that the project is never-ending.

---

## What is HA!?

HA! is a smart healthcare ecosystem combining:
- 🤖 **Artificial Intelligence** — Powered by local LLM (Ollama + phi3)
- 🩺 **AI Symptom Checker** — Instant health analysis
- 👨‍⚕️ **Doctor Booking** — Book appointments directly from the app
- 🚨 **Emergency SOS** — AI first-aid guide + emergency numbers
- 💬 **Health Chat** — 24/7 AI healthcare assistant

---

## Project Structure

```
HA-Healthcare-AI/
├── backend/
│   ├── main.py              # FastAPI backend
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Login page
│   ├── chat.html            # AI Chat
│   ├── symptoms.html        # Symptom Checker
│   ├── doctors.html         # Find & Book Doctors
│   ├── appointments.html    # My Appointments
│   ├── emergency.html       # Emergency SOS
│   ├── css/
│   │   ├── style.css        # Global styles
│   │   ├── login.css        # Login page styles
│   │   ├── chat.css         # App layout & chat styles
│   │   └── pages.css        # Inner pages styles
│   └── js/
│       ├── app.js           # Shared utilities & auth
│       ├── login.js         # Login logic
│       ├── chat.js          # Chat logic
│       ├── symptoms.js      # Symptom checker logic
│       ├── doctors.js       # Doctor listing & booking
│       ├── appointments.js  # Appointments management
│       └── emergency.js     # Emergency SOS logic
└── README.md
```

---

## Setup & Run

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Groq API key
echo GROQ_API_KEY=your_groq_api_key_here > .env

# Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000
API Docs at: http://localhost:8000/docs

**Note:** SQLite database (`ha_healthcare.db`) will be created automatically on first run.

### 2. Frontend

For local development, update `API_BASE` in `frontend/js/app.js`:
```javascript
const API_BASE = "http://localhost:8000";  // Local development
```

Serve with a local server:
```bash
cd frontend
python -m http.server 3000
# Open: http://localhost:3000
```

### 3. Deployment

**Backend (Render):**
- Deploy from GitHub
- Add environment variable: `GROQ_API_KEY`
- SQLite database persists on Render disk

**Frontend (Vercel):**
- Deploy from GitHub
- Update `API_BASE` in `app.js` to your Render backend URL
- Automatic deployments on push

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register patient |
| POST | `/chat` | AI health chat (saves to history) |
| GET  | `/chat/history/{phone}` | Get all chat sessions for user |
| GET  | `/chat/session/{chat_id}` | Get messages from specific chat |
| DELETE | `/chat/session/{chat_id}` | Delete a chat session |
| POST | `/symptom-check` | Analyze symptoms |
| GET  | `/doctors` | List all doctors |
| GET  | `/doctors/{id}` | Get doctor details |
| POST | `/appointments/book` | Book appointment |
| GET  | `/appointments/{phone}` | Get patient appointments |
| DELETE | `/appointments/{id}` | Cancel appointment |
| POST | `/emergency/alert` | Emergency AI guide |
| GET  | `/health-tips` | Daily health tips |

---

## Features

- ✅ AI-powered health chat (Groq Cloud API)
- ✅ **Chat History** — Save and load previous conversations
- ✅ **User Database** — SQLite database for user management
- ✅ Symptom analysis with risk assessment
- ✅ 8 specialist doctors with real-time booking
- ✅ Appointment management (book/cancel)
- ✅ Emergency SOS with AI first-aid guide
- ✅ Emergency helpline numbers (108, 102, 100, 101)
- ✅ Responsive design (mobile + desktop)
- ✅ Dark mode UI (Gemini AI inspired)
- ✅ Input validation & error handling
- ✅ Cloud deployment ready (Render + Vercel)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python, FastAPI |
| Database | SQLite |
| AI Engine | Groq Cloud API (llama-3.1-8b-instant) |
| Styling | Custom CSS with CSS Variables (Gemini AI inspired) |
| Markdown | marked.js |
| Deployment | Vercel (Frontend) + Render (Backend) |

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    location TEXT,
    created_at TEXT NOT NULL
);
```

### Chat History Table
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_phone) REFERENCES users(phone)
);
```

---

*HA! — Healthcare with AI. The `!` means it never stops improving.*
