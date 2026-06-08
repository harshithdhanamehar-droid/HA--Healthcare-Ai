# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ha_healthcare")

app = FastAPI(title="HA! Healthcare AI API", version="2.1.0")

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── DATABASE SETUP ──────────────────────────────────────────────────────────
DB_PATH = "ha_healthcare.db"

def get_conn() -> sqlite3.Connection:
    """Return a row-factory enabled SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # better write concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_database():
    """Initialize SQLite database with all required tables."""
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                phone      TEXT UNIQUE NOT NULL,
                location   TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT NOT NULL,
                chat_id    TEXT NOT NULL,
                role       TEXT NOT NULL,
                message    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_phone) REFERENCES users(phone)
            )
        """)

        # Appointments — persistent SQLite storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id   TEXT UNIQUE NOT NULL,
                patient_name     TEXT NOT NULL,
                patient_phone    TEXT NOT NULL,
                patient_location TEXT,
                doctor_id        TEXT NOT NULL,
                doctor_name      TEXT NOT NULL,
                specialty        TEXT,
                hospital         TEXT,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                symptoms         TEXT,
                fee              INTEGER DEFAULT 0,
                status           TEXT NOT NULL DEFAULT 'pending',
                created_at       TEXT NOT NULL,
                updated_at       TEXT NOT NULL
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_phone   ON chat_history(user_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_id      ON chat_history(chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_phone    ON appointments(patient_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_status   ON appointments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_date     ON appointments(appointment_date)")

        conn.commit()
        conn.close()
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.error("Database initialisation failed: %s", e)
        raise

init_database()

# ─── DOCTORS DATA ─────────────────────────────────────────────────────────────
# Each doctor has a photo_url field.
# Set photo_url to a real image URL or "" to use the generated avatar fallback.
DOCTORS = [
    {
        "id": "d001",
        "name": "Dr. Priya Sharma",
        "specialty": "General Physician",
        "experience": "12 years",
        "rating": 4.9,
        "available_slots": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM"],
        "fee": 500,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=priya",
        "hospital": "HA! City Medical Center",
        "languages": ["English", "Hindi", "Telugu"],
    },
    {
        "id": "d002",
        "name": "Dr. Arjun Mehta",
        "specialty": "Cardiologist",
        "experience": "18 years",
        "rating": 4.8,
        "available_slots": ["10:00 AM", "11:30 AM", "03:00 PM", "04:30 PM"],
        "fee": 1200,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=arjun",
        "hospital": "HA! Heart Care Institute",
        "languages": ["English", "Hindi"],
    },
    {
        "id": "d003",
        "name": "Dr. Sneha Reddy",
        "specialty": "Dermatologist",
        "experience": "9 years",
        "rating": 4.7,
        "available_slots": ["09:30 AM", "11:00 AM", "01:00 PM", "04:00 PM"],
        "fee": 800,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=sneha",
        "hospital": "HA! Skin & Wellness Clinic",
        "languages": ["English", "Telugu", "Kannada"],
    },
    {
        "id": "d004",
        "name": "Dr. Rahul Verma",
        "specialty": "Neurologist",
        "experience": "15 years",
        "rating": 4.9,
        "available_slots": ["10:00 AM", "12:00 PM", "02:30 PM", "05:00 PM"],
        "fee": 1500,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=rahul",
        "hospital": "HA! Neuro Sciences Center",
        "languages": ["English", "Hindi"],
    },
    {
        "id": "d005",
        "name": "Dr. Kavitha Nair",
        "specialty": "Pediatrician",
        "experience": "11 years",
        "rating": 4.8,
        "available_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "03:30 PM"],
        "fee": 600,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=kavitha",
        "hospital": "HA! Children's Health Hub",
        "languages": ["English", "Malayalam", "Tamil"],
    },
    {
        "id": "d006",
        "name": "Dr. Suresh Patel",
        "specialty": "Orthopedic Surgeon",
        "experience": "20 years",
        "rating": 4.9,
        "available_slots": ["11:00 AM", "01:00 PM", "03:00 PM", "05:00 PM"],
        "fee": 1000,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=suresh",
        "hospital": "HA! Bone & Joint Clinic",
        "languages": ["English", "Hindi", "Gujarati"],
    },
    {
        "id": "d007",
        "name": "Dr. Ananya Das",
        "specialty": "Psychiatrist",
        "experience": "8 years",
        "rating": 4.7,
        "available_slots": ["10:00 AM", "11:30 AM", "02:00 PM", "04:00 PM"],
        "fee": 900,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=ananya",
        "hospital": "HA! Mind & Wellness Center",
        "languages": ["English", "Bengali", "Hindi"],
    },
    {
        "id": "d008",
        "name": "Dr. Vikram Singh",
        "specialty": "Diabetologist",
        "experience": "14 years",
        "rating": 4.8,
        "available_slots": ["09:00 AM", "10:30 AM", "01:30 PM", "03:30 PM"],
        "fee": 700,
        "photo_url": "",
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=vikram",
        "hospital": "HA! Diabetes Care Center",
        "languages": ["English", "Hindi", "Punjabi"],
    },
]

def get_doctor_display_image(doctor: dict) -> str:
    """Return photo_url if set, otherwise fall back to generated avatar."""
    return doctor.get("photo_url") or doctor.get("image", "")


# ─── MODELS ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    username: Optional[str] = "Patient"
    user_phone: Optional[str] = None
    chat_id: Optional[str] = None

class SymptomRequest(BaseModel):
    symptoms: List[str]
    age: Optional[int] = None
    gender: Optional[str] = None

class AppointmentRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_location: Optional[str] = ""
    doctor_id: str
    date: str
    time_slot: str
    reason: Optional[str] = ""        # kept for backwards compat — stored as symptoms

class AppointmentStatusUpdate(BaseModel):
    status: str                        # pending | confirmed | completed | cancelled

class UserRegister(BaseModel):
    name: str
    phone: str
    location: str

# ─── GROQ AI SETUP ─────────────────────────────────────────────
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def call_ai(prompt: str, system_prompt: str = "") -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"
# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "HA! Healthcare AI Backend Running 🚀", "version": "2.0.0", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/auth/register")
def register(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id, name, location FROM users WHERE phone = ?", (user.phone,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return {
            "success": True,
            "user_id": existing_user[0],
            "name": existing_user[1],
            "message": "User already exists"
        }
    
    # Create new user
    user_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO users (id, name, phone, location, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, user.name, user.phone, user.location, created_at))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "user_id": user_id,
        "name": user.name,
        "message": "User registered successfully"
    }

def validate_health_query(message: str) -> str:
    """
    Health Validator: uses LLM intent classification to determine whether
    a query is health-related or not.
    Returns 'HEALTH' or 'NON_HEALTH'.
    """
    validator_system = (
        "You are a strict intent classifier for a healthcare chatbot. "
        "Your only job is to classify the user's query as HEALTH or NON_HEALTH.\n\n"
        "Rules:\n"
        "- HEALTH: The query is exclusively about medical topics such as symptoms, "
        "diseases, medications, mental health, nutrition, fitness, anatomy, "
        "medical procedures, healthcare advice, or patient wellbeing.\n"
        "- NON_HEALTH: The query is about anything outside the healthcare domain "
        "(e.g. cooking, technology, finance, entertainment, sports, general knowledge).\n"
        "- If the query mixes healthcare with ANY non-healthcare topic, classify as NON_HEALTH.\n\n"
        "Respond with exactly one word: HEALTH or NON_HEALTH. No explanation. No punctuation."
    )
    result = call_ai(message, validator_system).strip().upper()
    # Normalise — only accept exact HEALTH, everything else is NON_HEALTH
    if result == "HEALTH":
        return "HEALTH"
    return "NON_HEALTH"


@app.post("/chat")
async def chat(data: ChatRequest):
    # ── Health Validator ──────────────────────────────────────────
    classification = validate_health_query(data.message)
    if classification == "NON_HEALTH":
        return {
            "response": None,
            "classification": "NON_HEALTH",
            "timestamp": datetime.now().isoformat(),
        }

    system_prompt = (
        "You are HA!, an expert AI-powered healthcare assistant. "
        "You provide accurate, empathetic, and helpful medical information. "
        "Always recommend consulting a real doctor for serious conditions. "
        "Keep responses clear, structured, and easy to understand. "
        f"You are speaking with patient: {data.username}."
    )
    reply = call_ai(data.message, system_prompt)
    
    # Save chat history to database if user_phone and chat_id are provided
    if data.user_phone and data.chat_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        # Save user message
        cursor.execute("""
            INSERT INTO chat_history (user_phone, chat_id, role, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (data.user_phone, data.chat_id, "user", data.message, timestamp))
        
        # Save AI response
        cursor.execute("""
            INSERT INTO chat_history (user_phone, chat_id, role, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (data.user_phone, data.chat_id, "assistant", reply, timestamp))
        
        conn.commit()
        conn.close()
    
    return {"response": reply, "timestamp": datetime.now().isoformat(), "classification": "HEALTH"}

@app.post("/symptom-check")
async def symptom_check(data: SymptomRequest):
    symptoms_str = ", ".join(data.symptoms)
    age_info = f"Age: {data.age}" if data.age else ""
    gender_info = f"Gender: {data.gender}" if data.gender else ""
    system_prompt = (
        "You are HA! Symptom Analyzer, a medical AI assistant. "
        "Analyze the given symptoms and provide: "
        "1. Possible conditions (list top 3) "
        "2. Risk level (Low/Medium/High) "
        "3. Recommended specialist to consult "
        "4. Immediate home care tips "
        "5. Warning signs to watch for. "
        "Always remind the user to consult a real doctor. "
        "Format your response clearly with numbered sections."
    )
    prompt = f"Patient symptoms: {symptoms_str}. {age_info}. {gender_info}. Analyze these symptoms."
    analysis = call_ai(prompt, system_prompt)
    return {
        "symptoms": data.symptoms,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "This is AI-generated information only. Please consult a qualified doctor.",
    }

@app.get("/doctors")
def get_doctors(specialty: Optional[str] = None):
    doctors = DOCTORS
    if specialty:
        doctors = [d for d in doctors if specialty.lower() in d["specialty"].lower()]
    # Inject resolved display image into each doctor
    result = [{**d, "image": get_doctor_display_image(d)} for d in doctors]
    return {"doctors": result, "count": len(result)}

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    doctor = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {**doctor, "image": get_doctor_display_image(doctor)}

# ─── APPOINTMENT HELPERS ──────────────────────────────────────────────────────

def _row_to_appointment(row: sqlite3.Row) -> dict:
    """Convert a DB row to the appointment dict the frontend expects."""
    return {
        "id":           row["appointment_id"],
        "appointment_id": row["appointment_id"],
        "patient_name": row["patient_name"],
        "patient_phone": row["patient_phone"],
        "patient_location": row["patient_location"] or "",
        "doctor_id":    row["doctor_id"],
        "doctor_name":  row["doctor_name"],
        "specialty":    row["specialty"] or "",
        "hospital":     row["hospital"] or "",
        "date":         row["appointment_date"],
        "time_slot":    row["appointment_time"],
        "reason":       row["symptoms"] or "",
        "symptoms":     row["symptoms"] or "",
        "fee":          row["fee"],
        "status":       row["status"],
        "booked_at":    row["created_at"],
        "created_at":   row["created_at"],
        "updated_at":   row["updated_at"],
    }

VALID_STATUSES = {"pending", "confirmed", "completed", "cancelled"}

@app.post("/appointments/book")
def book_appointment(data: AppointmentRequest):
    # Validate doctor
    doctor = next((d for d in DOCTORS if d["id"] == data.doctor_id), None)
    if not doctor:
        logger.warning("Booking failed — doctor not found: %s", data.doctor_id)
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not data.patient_name.strip():
        raise HTTPException(status_code=422, detail="patient_name is required")
    if not data.patient_phone.strip():
        raise HTTPException(status_code=422, detail="patient_phone is required")

    appointment_id = "APT" + str(uuid.uuid4())[:6].upper()
    now = datetime.now().isoformat()

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments
              (appointment_id, patient_name, patient_phone, patient_location,
               doctor_id, doctor_name, specialty, hospital,
               appointment_date, appointment_time, symptoms,
               fee, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            appointment_id,
            data.patient_name.strip(),
            data.patient_phone.strip(),
            (data.patient_location or "").strip(),
            doctor["id"],
            doctor["name"],
            doctor["specialty"],
            doctor["hospital"],
            data.date,
            data.time_slot,
            (data.reason or "").strip(),
            doctor["fee"],
            "pending",
            now, now,
        ))
        conn.commit()
        conn.close()
        logger.info("Appointment created: %s for %s with %s on %s %s",
                    appointment_id, data.patient_name, doctor["name"], data.date, data.time_slot)
    except sqlite3.IntegrityError as e:
        logger.error("Duplicate appointment_id collision: %s — %s", appointment_id, e)
        raise HTTPException(status_code=409, detail="Appointment ID collision, please retry")
    except Exception as e:
        logger.error("DB write failed for appointment: %s", e)
        raise HTTPException(status_code=500, detail="Database error, appointment not saved")

    appointment = {
        "id": appointment_id,
        "patient_name": data.patient_name,
        "patient_phone": data.patient_phone,
        "doctor_id": doctor["id"],
        "doctor_name": doctor["name"],
        "specialty": doctor["specialty"],
        "hospital": doctor["hospital"],
        "date": data.date,
        "time_slot": data.time_slot,
        "reason": data.reason or "",
        "fee": doctor["fee"],
        "status": "pending",
        "booked_at": now,
    }
    return {
        "success": True,
        "appointment": appointment,
        "message": f"Appointment booked with {doctor['name']} on {data.date} at {data.time_slot}",
    }

@app.get("/appointments/{phone}")
def get_appointments(phone: str):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM appointments
            WHERE patient_phone = ?
            ORDER BY created_at DESC
        """, (phone,))
        rows = cursor.fetchall()
        conn.close()
        appointments = [_row_to_appointment(r) for r in rows]
        logger.info("Retrieved %d appointments for phone %s", len(appointments), phone)
        return {"appointments": appointments, "count": len(appointments)}
    except Exception as e:
        logger.error("Error retrieving appointments for %s: %s", phone, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve appointments")

@app.patch("/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, data: AppointmentStatusUpdate):
    if data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        )
    now = datetime.now().isoformat()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE appointments SET status=?, updated_at=? WHERE appointment_id=?",
            (data.status, now, appointment_id)
        )
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        conn.commit()
        conn.close()
        logger.info("Appointment %s status updated to %s", appointment_id, data.status)
        return {"success": True, "appointment_id": appointment_id, "status": data.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating appointment %s: %s", appointment_id, e)
        raise HTTPException(status_code=500, detail="Failed to update appointment")

@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: str):
    now = datetime.now().isoformat()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE appointments SET status='cancelled', updated_at=? WHERE appointment_id=?",
            (now, appointment_id)
        )
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        conn.commit()
        conn.close()
        logger.info("Appointment %s cancelled", appointment_id)
        return {"success": True, "message": "Appointment cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling appointment %s: %s", appointment_id, e)
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")

@app.get("/health-tips")
def get_health_tips():
    tips = [
        {"id": 1, "category": "Nutrition", "tip": "Drink at least 8 glasses of water daily to stay hydrated.", "icon": "💧"},
        {"id": 2, "category": "Exercise", "tip": "Walk 10,000 steps daily to maintain cardiovascular health.", "icon": "🚶"},
        {"id": 3, "category": "Sleep", "tip": "Get 7-9 hours of quality sleep every night for optimal health.", "icon": "😴"},
        {"id": 4, "category": "Mental Health", "tip": "Practice 10 minutes of mindfulness or meditation daily.", "icon": "🧘"},
        {"id": 5, "category": "Nutrition", "tip": "Eat 5 servings of fruits and vegetables every day.", "icon": "🥗"},
        {"id": 6, "category": "Prevention", "tip": "Wash hands frequently to prevent infections.", "icon": "🧼"},
    ]
    return {"tips": tips}

# ─── CHAT HISTORY ROUTES ──────────────────────────────────────────────────────

@app.get("/chat/history/{phone}")
def get_chat_history(phone: str):
    """Get all chat sessions for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get distinct chat sessions with first message preview
    cursor.execute("""
        SELECT 
            chat_id,
            MIN(created_at) as first_message_time,
            (SELECT message FROM chat_history 
             WHERE chat_id = ch.chat_id AND role = 'user' 
             ORDER BY created_at ASC LIMIT 1) as preview
        FROM chat_history ch
        WHERE user_phone = ?
        GROUP BY chat_id
        ORDER BY first_message_time DESC
    """, (phone,))
    
    sessions = []
    for row in cursor.fetchall():
        chat_id, created_at, preview = row
        # Truncate preview to 60 characters
        preview_text = preview[:60] + "..." if preview and len(preview) > 60 else preview
        sessions.append({
            "chat_id": chat_id,
            "preview": preview_text,
            "created_at": created_at
        })
    
    conn.close()
    return {"sessions": sessions, "count": len(sessions)}

@app.get("/chat/session/{chat_id}")
def get_chat_session(chat_id: str):
    """Get all messages from a specific chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, role, message, created_at
        FROM chat_history
        WHERE chat_id = ?
        ORDER BY created_at ASC
    """, (chat_id,))
    
    messages = []
    for row in cursor.fetchall():
        msg_id, role, message, created_at = row
        messages.append({
            "id": msg_id,
            "role": role,
            "message": message,
            "created_at": created_at
        })
    
    conn.close()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return {"chat_id": chat_id, "messages": messages, "count": len(messages)}

@app.delete("/chat/session/{chat_id}")
def delete_chat_session(chat_id: str):
    """Delete a specific chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if session exists
    cursor.execute("SELECT COUNT(*) FROM chat_history WHERE chat_id = ?", (chat_id,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete all messages in the session
    cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Chat session deleted successfully"}

@app.post("/emergency/alert")
async def emergency_alert(data: dict):
    patient_name = data.get("patient_name", "Unknown")
    location = data.get("location", "Unknown")
    condition = data.get("condition", "Medical Emergency")
    system_prompt = (
        "You are HA! Emergency Response AI. "
        "Provide immediate, clear first-aid instructions for the described emergency. "
        "Be concise, numbered, and actionable. Always say to call 108 (India emergency) immediately."
    )
    prompt = f"Emergency: {condition}. Patient: {patient_name}. Location: {location}. What should be done immediately?"
    instructions = call_ai(prompt, system_prompt)
    return {
        "alert_id": "EMG" + str(uuid.uuid4())[:6].upper(),
        "status": "alert_sent",
        "emergency_number": "108",
        "instructions": instructions,
        "timestamp": datetime.now().isoformat(),
    }

# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────

@app.get("/admin/users")
def get_all_users():
    """Get all users from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, phone, location, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    
    users = []
    for row in cursor.fetchall():
        user_id, name, phone, location, created_at = row
        users.append({
            "id": user_id,
            "name": name,
            "phone": phone,
            "location": location,
            "created_at": created_at
        })
    
    conn.close()
    return {"users": users, "count": len(users)}

@app.get("/admin/chats")
def get_all_chats():
    """Get all chat sessions grouped by chat_id with message counts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_phone,
            chat_id,
            COUNT(*) as message_count,
            MIN(created_at) as created_at,
            (SELECT message FROM chat_history
             WHERE chat_id = ch.chat_id AND role = 'user'
             ORDER BY created_at ASC LIMIT 1) as first_message
        FROM chat_history ch
        GROUP BY chat_id
        ORDER BY created_at DESC
    """)

    chats = []
    for row in cursor.fetchall():
        user_phone, chat_id, message_count, created_at, first_message = row
        chats.append({
            "user_phone": user_phone,
            "chat_id": chat_id,
            "message_count": message_count,
            "created_at": created_at,
            "first_message": (first_message or "")[:80]
        })

    conn.close()
    return {"chats": chats, "count": len(chats)}


@app.get("/admin/stats")
def get_admin_stats():
    """Dashboard summary stats"""
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM chat_history")
        total_chats = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT user_phone) FROM chat_history
            WHERE created_at >= datetime('now', '-7 days')
        """)
        active_users = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE created_at >= datetime('now', 'start of day')
        """)
        today_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appointments")
        total_appointments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appointments WHERE status='pending'")
        pending_appointments = cursor.fetchone()[0]

        conn.close()
        return {
            "total_users":         total_users,
            "total_chats":         total_chats,
            "active_users":        active_users,
            "today_users":         today_users,
            "total_appointments":  total_appointments,
            "pending_appointments": pending_appointments,
        }
    except Exception as e:
        logger.error("Error fetching admin stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

@app.get("/admin/appointments")
def get_all_appointments():
    """Admin: get all appointments from SQLite, newest first."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        appointments = [_row_to_appointment(r) for r in rows]
        logger.info("Admin retrieved %d appointments", len(appointments))
        return {"appointments": appointments, "count": len(appointments)}
    except Exception as e:
        logger.error("Admin appointments fetch error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve appointments")
