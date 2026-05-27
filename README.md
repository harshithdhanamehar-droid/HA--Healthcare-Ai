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

### 1. Install Ollama (AI Engine)

Download from: https://ollama.com/download

```bash
# Pull the AI model
ollama pull phi3

# Start Ollama server
ollama serve
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000
API Docs at: http://localhost:8000/docs

### 3. Frontend

Open `frontend/index.html` in your browser.

For best results, serve with a local server:
```bash
# Using Python
cd frontend
python -m http.server 3000
# Open: http://localhost:3000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register patient |
| POST | `/chat` | AI health chat |
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

- ✅ AI-powered health chat (Ollama + phi3)
- ✅ Symptom analysis with risk assessment
- ✅ 8 specialist doctors with real-time booking
- ✅ Appointment management (book/cancel)
- ✅ Emergency SOS with AI first-aid guide
- ✅ Emergency helpline numbers (108, 102, 100, 101)
- ✅ Responsive design (mobile + desktop)
- ✅ Dark mode UI
- ✅ Input validation & error handling
- ✅ Offline-first login (works without backend)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python, FastAPI |
| AI Engine | Ollama (phi3 model) |
| Styling | Custom CSS with CSS Variables |
| Markdown | marked.js |

---

*HA! — Healthcare with AI. The `!` means it never stops improving.*
