# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── AUTH MODULE ──────────────────────────────────────────────────────────────
from auth import (
    create_access_token,
    verify_token,
    verify_password,
    hash_password,
    generate_otp,
    store_otp,
    verify_otp,
    send_otp_email,
    verify_google_token,
    link_google_auth,
    get_user_by_google_sub,
    create_doctor_account,
    verify_doctor_credentials,
    verify_admin_pin,
    store_token,
    invalidate_token,
)

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
                id              TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                email           TEXT UNIQUE,
                phone           TEXT UNIQUE,
                location        TEXT,
                auth_provider   TEXT DEFAULT 'local',
                google_sub      TEXT UNIQUE,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
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

        # Doctors (profile/availability data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id               TEXT PRIMARY KEY,
                doctor_name      TEXT NOT NULL,
                email            TEXT,
                specialty        TEXT NOT NULL,
                location         TEXT NOT NULL,
                hospital         TEXT,
                experience       TEXT,
                rating           REAL DEFAULT 4.5,
                fee              INTEGER DEFAULT 500,
                photo_url        TEXT,
                is_online        BOOLEAN DEFAULT 1,
                is_active        BOOLEAN DEFAULT 1,
                created_at       TEXT NOT NULL,
                updated_at       TEXT NOT NULL
            )
        """)

        # Doctor accounts (for doctor login)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctor_accounts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id        TEXT UNIQUE NOT NULL,
                doctor_name      TEXT NOT NULL,
                email            TEXT UNIQUE NOT NULL,
                password_hash    TEXT NOT NULL,
                is_active        BOOLEAN DEFAULT 1,
                verified         BOOLEAN DEFAULT 0,
                created_at       TEXT NOT NULL,
                updated_at       TEXT NOT NULL,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        # Auth tokens (JWT-like session tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                token            TEXT UNIQUE NOT NULL,
                user_id          TEXT NOT NULL,
                user_role        TEXT NOT NULL,
                expires_at       TEXT NOT NULL,
                created_at       TEXT NOT NULL
            )
        """)

        # OTP storage (email verification, forgot password)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_store (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                email            TEXT NOT NULL,
                otp_code         TEXT NOT NULL,
                purpose          TEXT NOT NULL,
                expires_at       TEXT NOT NULL,
                created_at       TEXT NOT NULL
            )
        """)

        # Google OAuth linkage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_auth (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                google_sub       TEXT UNIQUE NOT NULL,
                user_id          TEXT UNIQUE NOT NULL,
                email            TEXT,
                created_at       TEXT NOT NULL
            )
        """)

        # Chat Sessions (for managing recent chats with titles)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                chat_id          TEXT PRIMARY KEY,
                user_phone       TEXT NOT NULL,
                title            TEXT,
                preview          TEXT,
                is_archived      BOOLEAN DEFAULT 0,
                created_at       TEXT NOT NULL,
                updated_at       TEXT NOT NULL,
                FOREIGN KEY (user_phone) REFERENCES users(phone)
            )
        """)

        # Email Logs (SMTP failure tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient        TEXT NOT NULL,
                email_type       TEXT NOT NULL,
                subject          TEXT,
                status           TEXT NOT NULL,
                error_message    TEXT,
                created_at       TEXT NOT NULL
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_phone   ON chat_history(user_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_id      ON chat_history(chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_phone    ON appointments(patient_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_status   ON appointments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_date     ON appointments(appointment_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctor_email ON doctor_accounts(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_location ON doctors(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_rating ON doctors(rating)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_email    ON otp_store(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_google_sub   ON google_auth(google_sub)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_phone ON chat_sessions(user_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON chat_sessions(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type)")

        conn.commit()
        conn.close()
        logger.info("Database initialised successfully with auth tables.")
    except Exception as e:
        logger.error("Database initialisation failed: %s", e)
        raise

init_database()

def migrate_doctors_to_database():
    """Migrate hardcoded DOCTORS list to SQLite database (one-time operation)."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if doctors already migrated
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
        count = cursor.fetchone()["count"]
        
        if count > 0:
            logger.info("Doctors table already populated (%d doctors)", count)
            conn.close()
            return
        
        logger.info("Migrating hardcoded DOCTORS to database...")
        
        # Migrate all doctors from DOCTORS list
        now = datetime.now().isoformat()
        for doctor in DOCTORS:
            cursor.execute("""
                INSERT INTO doctors 
                (id, doctor_name, email, specialty, location, hospital, 
                 experience, rating, fee, photo_url, is_online, is_active, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doctor["id"],
                doctor["name"],
                doctor.get("email", ""),
                doctor["specialty"],
                doctor.get("location", "Online"),
                doctor.get("hospital", ""),
                doctor["experience"],
                doctor["rating"],
                doctor["fee"],
                doctor.get("photo_url", ""),
                1,  # is_online
                1,  # is_active
                now,
                now
            ))
        
        conn.commit()
        conn.close()
        logger.info("Successfully migrated %d doctors to database", len(DOCTORS))
        
    except Exception as e:
        logger.error("Doctor migration failed: %s", e)
        raise

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
        "location": "Hyderabad",
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
        "location": "Mumbai",
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
        "location": "Bangalore",
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
        "location": "Delhi",
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
        "location": "Chennai",
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
        "location": "Hyderabad",
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
        "location": "Bangalore",
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
        "location": "Mumbai",
        "languages": ["English", "Hindi", "Punjabi"],
    },
]

# Run migration on startup - migrate hardcoded DOCTORS to SQLite database
migrate_doctors_to_database()

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

class UserLoginGoogle(BaseModel):
    google_sub: str
    email: str
    name: str

class UserUpdateLocation(BaseModel):
    location: str

class GoogleCheckUser(BaseModel):
    google_sub: str
    email: str

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

# ─── SMTP EMAIL SERVICE ──────────────────────────────────────────────────────
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def log_email(recipient: str, email_type: str, subject: str, status: str, error: str = None):
    """Log email attempt to database for audit trail."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO email_logs (recipient, email_type, subject, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recipient, email_type, subject, status, error, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to log email: %s", e)

def send_email(to_email: str, subject: str, html_body: str, email_type: str = "general") -> bool:
    """
    Send email via Gmail SMTP.
    Returns True if sent, False if failed (but app continues).
    Never raises exception — all errors are logged.
    """
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    
    # If credentials not set, log warning and continue
    if not gmail_user or not gmail_pass:
        error_msg = "GMAIL_USER or GMAIL_APP_PASSWORD not configured"
        logger.warning("Email disabled: %s", error_msg)
        log_email(to_email, email_type, subject, "skipped", error_msg)
        return False
    
    try:
        # Build message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = to_email
        
        # Add HTML body
        part = MIMEText(html_body, "html")
        msg.attach(part)
        
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, to_email, msg.as_string())
        
        logger.info(f"Email sent to {to_email}: {subject}")
        log_email(to_email, email_type, subject, "sent")
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Email send failed to {to_email}: {error_msg}")
        log_email(to_email, email_type, subject, "failed", error_msg)
        return False

def send_appointment_confirmation(appointment: dict):
    """Send appointment confirmation email to user."""
    subject = f"Appointment Confirmed with Dr. {appointment['doctor_name']}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #00d4aa;">Appointment Confirmed!</h2>
        <p>Dear {appointment['patient_name']},</p>
        <p>Your appointment has been successfully booked.</p>
        
        <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Doctor:</strong> Dr. {appointment['doctor_name']}</p>
            <p><strong>Specialty:</strong> {appointment['specialty']}</p>
            <p><strong>Hospital:</strong> {appointment['hospital']}</p>
            <p><strong>Date:</strong> {appointment['appointment_date']}</p>
            <p><strong>Time:</strong> {appointment['appointment_time']}</p>
            <p><strong>Appointment ID:</strong> {appointment['appointment_id']}</p>
        </div>
        
        <p>Please arrive 15 minutes early. For any queries, contact us at +91-1234-567890.</p>
        <p>Best regards,<br>HA! Healthcare AI Team</p>
    </body>
    </html>
    """
    
    send_email(appointment.get("patient_email", ""), subject, html, "appointment_confirmation")

def send_appointment_cancellation(appointment: dict):
    """Send appointment cancellation email."""
    subject = f"Appointment Cancelled - Dr. {appointment['doctor_name']}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #ef4444;">Appointment Cancelled</h2>
        <p>Dear {appointment['patient_name']},</p>
        <p>Your appointment has been cancelled.</p>
        
        <div style="background: #fff3cd; padding: 16px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Doctor:</strong> Dr. {appointment['doctor_name']}</p>
            <p><strong>Original Date:</strong> {appointment['appointment_date']} at {appointment['appointment_time']}</p>
            <p><strong>Appointment ID:</strong> {appointment['appointment_id']}</p>
        </div>
        
        <p>To reschedule, please visit our app or contact us.</p>
        <p>Best regards,<br>HA! Healthcare AI Team</p>
    </body>
    </html>
    """
    
    send_email(appointment.get("patient_email", ""), subject, html, "appointment_cancellation")

def send_otp_email_message(email: str, otp_code: str, purpose: str = "email_verification"):
    """Send OTP via email."""
    subject = f"Your HA! Healthcare Verification Code: {otp_code}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #00d4aa;">Verify Your Account</h2>
        <p>Your verification code is:</p>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h1 style="color: #00d4aa; letter-spacing: 2px; margin: 0;">{otp_code}</h1>
        </div>
        
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this code, please ignore this email.</p>
        <p>Best regards,<br>HA! Healthcare AI Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, html, "otp_email")

def send_doctor_notification(doctor_email: str, appointment: dict):
    """Send appointment notification to doctor."""
    subject = f"New Appointment: {appointment['patient_name']}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #3b82f6;">New Appointment Notification</h2>
        <p>A new appointment has been booked.</p>
        
        <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Patient:</strong> {appointment['patient_name']}</p>
            <p><strong>Phone:</strong> {appointment['patient_phone']}</p>
            <p><strong>Date & Time:</strong> {appointment['appointment_date']} at {appointment['appointment_time']}</p>
            <p><strong>Symptoms/Reason:</strong> {appointment['symptoms']}</p>
            <p><strong>Appointment ID:</strong> {appointment['appointment_id']}</p>
        </div>
        
        <p>Please log in to your doctor dashboard to view details.</p>
        <p>Best regards,<br>HA! Healthcare AI Team</p>
    </body>
    </html>
    """
    
    send_email(doctor_email, subject, html, "doctor_notification")

# ─── PYDANTIC MODELS FOR AUTHENTICATION ──────────────────────────────────────

class UserLoginGoogleRequest(BaseModel):
    token: str
    name: Optional[str] = None

class UserLoginOTPRequest(BaseModel):
    email: str
    otp_code: str

class UserRequestOTPRequest(BaseModel):
    email: str
    purpose: str  # "verification" or "forgot_password"

class DoctorLoginRequest(BaseModel):
    email: str
    password: str

class DoctorRegisterRequest(BaseModel):
    doctor_id: str
    email: str
    password: str

class DoctorVerifyOTPRequest(BaseModel):
    email: str
    otp_code: str

class AdminLoginRequest(BaseModel):
    pin: str

class TokenResponse(BaseModel):
    token: str
    user_id: str
    role: str
    expires_in: int

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "HA! Healthcare AI Backend Running 🚀", "version": "2.0.0", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ─── NEW JWT-BASED AUTH ROUTES ────────────────────────────────────────────────

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
            "location": existing_user[2],
            "message": "User already exists"
        }
    
    # Create new user
    user_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO users (id, name, phone, location, auth_provider, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, user.name, user.phone, user.location, "local", now, now))
    
    conn.commit()
    conn.close()
    
    logger.info("User registered: %s (%s, %s)", user_id, user.name, user.phone)
    
    return {
        "success": True,
        "user_id": user_id,
        "name": user.name,
        "location": user.location,
        "message": "User registered successfully"
    }

@app.post("/auth/google/check-user")
def google_check_user(data: GoogleCheckUser):
    """
    Check if a user exists with Google account.
    Used to determine if we need to ask for location on first Google login.
    
    Returns:
    - exists: true/false
    - user_id: (if exists)
    - location: (if exists)
    - needs_location: true if new user needs location entry
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists by google_sub
    cursor.execute("""
        SELECT id, name, email, location FROM users WHERE google_sub = ?
    """, (data.google_sub,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "exists": True,
            "user_id": user[0],
            "name": user[1],
            "email": user[2],
            "location": user[3],
            "needs_location": False
        }
    
    return {
        "exists": False,
        "needs_location": True
    }

@app.post("/auth/google/register")
def google_register(data: UserLoginGoogle):
    """
    Register or login user via Google OAuth.
    If new user, requires location to be provided.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists by google_sub
    cursor.execute("""
        SELECT id, name, email, location FROM users WHERE google_sub = ?
    """, (data.google_sub,))
    user = cursor.fetchone()
    
    if user:
        # Existing user - just create JWT token
        conn.close()
        logger.info("Google user login: %s (%s)", user[0], user[1])
        return {
            "success": True,
            "user_id": user[0],
            "name": user[1],
            "email": user[2],
            "location": user[3],
            "is_new": False,
            "message": "Welcome back!"
        }
    
    # New user - create with auth_provider = 'google'
    # Location should be provided, but if not, it can be updated later
    user_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    
    # Extract location from request (optional, can be updated later)
    location = getattr(data, 'location', None)
    
    cursor.execute("""
        INSERT INTO users (id, name, email, google_sub, auth_provider, location, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, data.name, data.email, data.google_sub, "google", location, now, now))
    
    conn.commit()
    conn.close()
    
    logger.info("Google user registered: %s (%s, %s)", user_id, data.name, data.email)
    
    return {
        "success": True,
        "user_id": user_id,
        "name": data.name,
        "email": data.email,
        "location": location,
        "is_new": True,
        "message": "Welcome to HA! Healthcare"
    }

@app.post("/auth/user/{user_id}/location")
def update_user_location(user_id: str, data: UserUpdateLocation):
    """
    Update user location. Used after first-time login if location wasn't provided.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verify user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update location
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE users SET location = ?, updated_at = ? WHERE id = ?
    """, (data.location, now, user_id))
    
    conn.commit()
    conn.close()
    
    logger.info("User location updated: %s → %s", user_id, data.location)
    
    return {
        "success": True,
        "user_id": user_id,
        "location": data.location,
        "message": "Location updated successfully"
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
        
        # Create or update chat session
        cursor.execute("""
            INSERT OR IGNORE INTO chat_sessions (chat_id, user_phone, title, preview, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.chat_id, data.user_phone, data.message[:60], data.message[:80], timestamp, timestamp))
        
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
        
        # Update session's updated_at timestamp
        cursor.execute("""
            UPDATE chat_sessions SET updated_at = ? WHERE chat_id = ?
        """, (timestamp, data.chat_id))
        
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
def get_doctors(specialty: Optional[str] = None, location: Optional[str] = None, user_location: Optional[str] = None):
    """
    Get doctors from SQLite database with optional filtering by specialty and location.
    
    Parameters:
    - specialty: Filter by specialty (case-insensitive partial match)
    - location: Filter by exact location
    - user_location: User's location to prioritize nearby doctors
    
    Returns doctors sorted by:
    1. Same location as user (if user_location provided) - highest rated first
    2. Other locations - highest rated first
    3. If no user_location: sorted by rating descending
    """
    conn = get_conn()
    cursor = conn.cursor()
    
    # Build SQL query with optional filters
    query = "SELECT * FROM doctors WHERE is_active = 1"
    params = []
    
    # Add specialty filter
    if specialty:
        query += " AND specialty LIKE ?"
        params.append(f"%{specialty}%")
    
    # Add location filter (exact match)
    if location:
        query += " AND location = ?"
        params.append(location)
    
    # Execute query
    cursor.execute(query, params)
    db_doctors = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to dictionaries
    doctors = [dict(row) for row in db_doctors]
    
    # Sort by user location + rating (if user_location provided)
    if user_location:
        user_loc_lower = user_location.lower()
        same_location = [d for d in doctors if d.get("location", "").lower() == user_loc_lower]
        other_doctors = [d for d in doctors if d.get("location", "").lower() != user_loc_lower]
        
        # Sort each group by rating (descending)
        same_location.sort(key=lambda x: x["rating"], reverse=True)
        other_doctors.sort(key=lambda x: x["rating"], reverse=True)
        
        # Combine: same location doctors first, then top-rated from other locations
        doctors = same_location + other_doctors
    else:
        # Default sort by rating descending
        doctors.sort(key=lambda x: x["rating"], reverse=True)
    
    # Format for frontend response
    result = []
    for doc in doctors:
        result.append({
            "id": doc["id"],
            "name": doc["doctor_name"],
            "specialty": doc["specialty"],
            "location": doc["location"],
            "hospital": doc["hospital"],
            "experience": doc["experience"],
            "rating": doc["rating"],
            "fee": doc["fee"],
            "photo_url": doc["photo_url"],
            "image": doc["photo_url"] or f"https://api.dicebear.com/7.x/personas/svg?seed={doc['doctor_name'].replace(' ', '').lower()}",
            "is_online": doc["is_online"],
            "available_slots": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM"],  # Generic slots
            "languages": ["English", "Hindi"],  # Generic fallback
        })
    
    return {"doctors": result, "count": len(result)}

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    """
    Get a single doctor from SQLite database by ID.
    Falls back to hardcoded DOCTORS list if not found (for backwards compatibility during migration).
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors WHERE id = ? AND is_active = 1", (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()
    
    if not doctor:
        # Fallback to hardcoded DOCTORS list for backwards compatibility
        doctor = next((d for d in DOCTORS if d["id"] == doctor_id), None)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return {**doctor, "image": get_doctor_display_image(doctor)}
    
    # Convert from database to frontend format
    doc = dict(doctor)
    return {
        "id": doc["id"],
        "name": doc["doctor_name"],
        "specialty": doc["specialty"],
        "location": doc["location"],
        "hospital": doc["hospital"],
        "experience": doc["experience"],
        "rating": doc["rating"],
        "fee": doc["fee"],
        "photo_url": doc["photo_url"],
        "image": doc["photo_url"] or f"https://api.dicebear.com/7.x/personas/svg?seed={doc['doctor_name'].replace(' ', '').lower()}",
        "is_online": doc["is_online"],
        "available_slots": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM"],
        "languages": ["English", "Hindi"],
    }

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
    # Get doctor from database
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors WHERE id = ? AND is_active = 1", (data.doctor_id,))
    doctor_row = cursor.fetchone()
    
    if not doctor_row:
        # Fallback to hardcoded DOCTORS for backwards compatibility
        doctor_dict = next((d for d in DOCTORS if d["id"] == data.doctor_id), None)
        if not doctor_dict:
            logger.warning("Booking failed — doctor not found: %s", data.doctor_id)
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor not found")
        doctor = doctor_dict
        doctor_email = doctor.get("email", "")
    else:
        doctor = dict(doctor_row)
        doctor_email = doctor.get("email", "")

    if not data.patient_name.strip():
        conn.close()
        raise HTTPException(status_code=422, detail="patient_name is required")
    if not data.patient_phone.strip():
        conn.close()
        raise HTTPException(status_code=422, detail="patient_phone is required")

    appointment_id = "APT" + str(uuid.uuid4())[:6].upper()
    now = datetime.now().isoformat()

    try:
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
            doctor.get("id") or data.doctor_id,
            doctor.get("doctor_name") or doctor.get("name", "Doctor"),
            doctor.get("specialty", "General"),
            doctor.get("hospital", "HA! Medical Center"),
            data.date,
            data.time_slot,
            (data.reason or "").strip(),
            doctor.get("fee", 500),
            "pending",
            now, now,
        ))
        conn.commit()
        
        appointment_data = {
            "appointment_id": appointment_id,
            "patient_name": data.patient_name,
            "patient_phone": data.patient_phone,
            "patient_email": "",  # Could be fetched from users table if needed
            "doctor_name": doctor.get("doctor_name") or doctor.get("name", "Doctor"),
            "specialty": doctor.get("specialty", "General"),
            "hospital": doctor.get("hospital", "HA! Medical Center"),
            "appointment_date": data.date,
            "appointment_time": data.time_slot,
            "symptoms": data.reason or "",
            "fee": doctor.get("fee", 500),
        }
        
        # Send emails (non-blocking, errors logged)
        send_appointment_confirmation(appointment_data)
        if doctor_email:
            send_doctor_notification(doctor_email, appointment_data)
        
        logger.info("Appointment created: %s for %s with %s on %s %s",
                    appointment_id, data.patient_name, appointment_data["doctor_name"], data.date, data.time_slot)
    except sqlite3.IntegrityError as e:
        conn.close()
        logger.error("Duplicate appointment_id collision: %s — %s", appointment_id, e)
        raise HTTPException(status_code=409, detail="Appointment ID collision, please retry")
    except Exception as e:
        conn.close()
        logger.error("DB write failed for appointment: %s", e)
        raise HTTPException(status_code=500, detail="Database error, appointment not saved")
    finally:
        conn.close()

    appointment = {
        "id": appointment_id,
        "patient_name": data.patient_name,
        "patient_phone": data.patient_phone,
        "doctor_id": doctor.get("id") or data.doctor_id,
        "doctor_name": doctor.get("doctor_name") or doctor.get("name", "Doctor"),
        "specialty": doctor.get("specialty", "General"),
        "hospital": doctor.get("hospital", "HA! Medical Center"),
        "date": data.date,
        "time_slot": data.time_slot,
        "reason": data.reason or "",
        "fee": doctor.get("fee", 500),
        "status": "pending",
        "booked_at": now,
    }
    return {
        "success": True,
        "appointment": appointment,
        "message": f"Appointment booked with Dr. {appointment['doctor_name']} on {data.date} at {data.time_slot}",
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
    """Get all chat sessions for a user, sorted by recent activity"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get chat sessions from chat_sessions table, ordered by most recent first
    cursor.execute("""
        SELECT 
            chat_id,
            title,
            preview,
            created_at,
            updated_at,
            is_archived
        FROM chat_sessions
        WHERE user_phone = ? AND is_archived = 0
        ORDER BY updated_at DESC
        LIMIT 50
    """, (phone,))
    
    sessions = []
    for row in cursor.fetchall():
        chat_id, title, preview, created_at, updated_at, is_archived = row
        # Use preview if set, otherwise get from first message
        preview_text = preview or title or "New conversation"
        # Truncate preview to 60 characters
        if preview_text and len(preview_text) > 60:
            preview_text = preview_text[:60] + "..."
        sessions.append({
            "chat_id": chat_id,
            "title": title or "Conversation",
            "preview": preview_text,
            "created_at": created_at,
            "updated_at": updated_at
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
    
    # Delete session record
    cursor.execute("DELETE FROM chat_sessions WHERE chat_id = ?", (chat_id,))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Chat session deleted successfully"}

@app.put("/chat/session/{chat_id}/rename")
def rename_chat_session(chat_id: str, data: dict):
    """Rename a chat session"""
    title = data.get("title", "Conversation").strip()
    
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if session exists
    cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Update title
    cursor.execute("""
        UPDATE chat_sessions SET title = ?, updated_at = ? WHERE chat_id = ?
    """, (title, datetime.now().isoformat(), chat_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Chat renamed successfully", "title": title}

@app.put("/chat/session/{chat_id}/archive")
def archive_chat_session(chat_id: str):
    """Archive a chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if session exists
    cursor.execute("SELECT is_archived FROM chat_sessions WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Toggle archive status
    new_archive_state = not row[0]
    cursor.execute("""
        UPDATE chat_sessions SET is_archived = ?, updated_at = ? WHERE chat_id = ?
    """, (new_archive_state, datetime.now().isoformat(), chat_id))
    
    conn.commit()
    conn.close()
    
    action = "archived" if new_archive_state else "unarchived"
    return {"success": True, "message": f"Chat {action} successfully", "is_archived": new_archive_state}

@app.get("/chat/archived/{phone}")
def get_archived_chats(phone: str):
    """Get all archived chat sessions for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            chat_id,
            title,
            preview,
            created_at,
            updated_at
        FROM chat_sessions
        WHERE user_phone = ? AND is_archived = 1
        ORDER BY updated_at DESC
    """, (phone,))
    
    sessions = []
    for row in cursor.fetchall():
        chat_id, title, preview, created_at, updated_at = row
        preview_text = preview or title or "Archived conversation"
        if preview_text and len(preview_text) > 60:
            preview_text = preview_text[:60] + "..."
        sessions.append({
            "chat_id": chat_id,
            "title": title or "Conversation",
            "preview": preview_text,
            "created_at": created_at,
            "updated_at": updated_at
        })
    
    conn.close()
    return {"sessions": sessions, "count": len(sessions)}

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

# ─── DOCTOR ACCOUNT MANAGEMENT (ADMIN) ────────────────────────────────────────

@app.get("/admin/doctors")
def get_all_doctors():
    """Admin: Get all doctor accounts."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, doctor_id, doctor_name, email, is_active, verified, created_at, updated_at
            FROM doctor_accounts
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        doctors = []
        for row in rows:
            doctors.append({
                "id": row[0],
                "doctor_id": row[1],
                "doctor_name": row[2],
                "email": row[3],
                "is_active": bool(row[4]),
                "verified": bool(row[5]),
                "created_at": row[6],
                "updated_at": row[7],
            })
        
        logger.info("Admin retrieved %d doctor accounts", len(doctors))
        return {"doctors": doctors, "count": len(doctors)}
    except Exception as e:
        logger.error("Error fetching doctor accounts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve doctor accounts")

@app.post("/admin/doctors")
def create_doctor_account_admin(data: dict):
    """Admin: Create a new doctor account."""
    doctor_id = data.get("doctor_id", "").strip()
    doctor_name = data.get("doctor_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not doctor_id or not doctor_name or not email or not password:
        raise HTTPException(status_code=422, detail="All fields (doctor_id, doctor_name, email, password) are required")
    
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Valid email required")
    
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    
    success, message = create_doctor_account(DB_PATH, doctor_id, doctor_name, email, password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    logger.info("Admin created doctor account: %s (%s)", doctor_name, email)
    return {"success": True, "message": message, "doctor_id": doctor_id}

@app.put("/admin/doctors/{doctor_id}")
def update_doctor_account(doctor_id: str, data: dict):
    """Admin: Edit a doctor account (name, email, active status)."""
    doctor_name = data.get("doctor_name", "").strip()
    email = data.get("email", "").strip()
    is_active = data.get("is_active", True)
    
    if not doctor_name or not email:
        raise HTTPException(status_code=422, detail="doctor_name and email are required")
    
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Valid email required")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if doctor exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        # Check if new email already exists (for other doctors)
        cursor.execute("SELECT id FROM doctor_accounts WHERE email = ? AND doctor_id != ?", (email, doctor_id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already in use by another doctor")
        
        # Update doctor
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE doctor_accounts
            SET doctor_name = ?, email = ?, is_active = ?, updated_at = ?
            WHERE doctor_id = ?
        """, (doctor_name, email, 1 if is_active else 0, now, doctor_id))
        
        conn.commit()
        conn.close()
        logger.info("Admin updated doctor account: %s", doctor_id)
        
        return {"success": True, "message": "Doctor account updated", "doctor_id": doctor_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating doctor account: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update doctor account")

@app.post("/admin/doctors/{doctor_id}/reset-password")
def reset_doctor_password(doctor_id: str, data: dict):
    """Admin: Reset doctor's password."""
    new_password = data.get("password", "").strip()
    
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if doctor exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        # Hash and update password
        password_hash = hash_password(new_password)
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE doctor_accounts
            SET password_hash = ?, updated_at = ?
            WHERE doctor_id = ?
        """, (password_hash, now, doctor_id))
        
        conn.commit()
        conn.close()
        logger.info("Admin reset password for doctor: %s", doctor_id)
        
        return {"success": True, "message": "Password reset successfully", "doctor_id": doctor_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting doctor password: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reset password")

@app.post("/admin/doctors/{doctor_id}/activate")
def toggle_doctor_active_status(doctor_id: str, data: dict):
    """Admin: Activate/deactivate doctor login."""
    is_active = data.get("is_active", True)
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if doctor exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        # Toggle active status
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE doctor_accounts
            SET is_active = ?, updated_at = ?
            WHERE doctor_id = ?
        """, (1 if is_active else 0, now, doctor_id))
        
        conn.commit()
        conn.close()
        status_text = "activated" if is_active else "deactivated"
        logger.info("Admin %s doctor: %s", status_text, doctor_id)
        
        return {"success": True, "message": f"Doctor {status_text} successfully", "doctor_id": doctor_id, "is_active": is_active}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error toggling doctor active status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update doctor status")

# ─── AUTHENTICATION ROUTES ───────────────────────────────────────────────────

# ─── USER AUTHENTICATION ──────────────────────────────────────────────────────

@app.post("/auth/user/google")
def user_login_google(data: UserLoginGoogleRequest):
    """
    Google OAuth login for users.
    Takes a Google token, creates/links user account.
    """
    # Verify Google token
    google_info = verify_google_token(data.token)
    if not google_info:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    
    google_sub = google_info.get("google_sub")
    email = google_info.get("email")
    name = data.name or google_info.get("name", "User")
    
    try:
        # Check if user already linked to Google
        user_id = get_user_by_google_sub(DB_PATH, google_sub)
        
        if not user_id:
            # Create new user
            user_id = str(uuid.uuid4())[:8]
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, name, phone, location, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, f"google_{google_sub}", "", datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            # Link Google account
            link_google_auth(DB_PATH, google_sub, user_id, email)
        
        # Create JWT token
        access_token = create_access_token(user_id, "user")
        store_token(DB_PATH, access_token, user_id, "user")
        
        logger.info("User logged in via Google: %s", user_id)
        return TokenResponse(
            token=access_token,
            user_id=user_id,
            role="user",
            expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", 1440)) * 60
        )
    except Exception as e:
        logger.error("Google login error: %s", e)
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/auth/user/otp/request")
def user_request_otp(data: UserRequestOTPRequest):
    """
    Request OTP for user email verification or password reset.
    """
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=422, detail="Valid email required")
    
    if data.purpose not in ("verification", "forgot_password"):
        raise HTTPException(status_code=422, detail="Invalid purpose")
    
    # Generate OTP
    otp_code = generate_otp()
    
    # Store OTP
    if not store_otp(DB_PATH, data.email, otp_code, data.purpose):
        raise HTTPException(status_code=500, detail="Failed to store OTP")
    
    # Send OTP email
    if not send_otp_email(data.email, otp_code, data.purpose):
        logger.warning("OTP email failed but OTP was stored: %s", data.email)
        return {
            "success": False,
            "message": "OTP generated but email delivery failed. Contact support.",
            "email": data.email,
        }
    
    logger.info("OTP requested for %s (%s)", data.email, data.purpose)
    return {
        "success": True,
        "message": f"OTP sent to {data.email}",
        "email": data.email,
    }

@app.post("/auth/user/otp/verify")
def user_verify_otp(data: UserLoginOTPRequest):
    """
    Verify OTP and create user account or reset password.
    """
    if not verify_otp(DB_PATH, data.email, data.otp_code, "verification"):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE phone = ?", (data.email,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
        else:
            # Create new user
            user_id = str(uuid.uuid4())[:8]
            cursor.execute("""
                INSERT INTO users (id, name, phone, location, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, data.email.split("@")[0], data.email, "", datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Create JWT token
        access_token = create_access_token(user_id, "user")
        store_token(DB_PATH, access_token, user_id, "user")
        
        logger.info("User verified OTP: %s", user_id)
        return TokenResponse(
            token=access_token,
            user_id=user_id,
            role="user",
            expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", 1440)) * 60
        )
    except Exception as e:
        logger.error("OTP verification error: %s", e)
        raise HTTPException(status_code=500, detail="Verification failed")

# ─── DOCTOR AUTHENTICATION ────────────────────────────────────────────────────

@app.post("/auth/doctor/register")
def doctor_register(data: DoctorRegisterRequest):
    """
    Register a doctor account with email and password.
    """
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=422, detail="Valid email required")
    if len(data.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    
    success, message = create_doctor_account(DB_PATH, data.doctor_id, data.doctor_id, data.email, data.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    logger.info("Doctor registered: %s (%s)", data.doctor_id, data.email)
    return {"success": True, "message": message, "doctor_id": data.doctor_id}

@app.post("/auth/doctor/login")
def doctor_login(data: DoctorLoginRequest):
    """
    Doctor login with email and password.
    """
    success, doctor_id, doctor_name = verify_doctor_credentials(DB_PATH, data.email, data.password)
    if not success:
        # Return specific error messages
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM doctor_accounts WHERE email = ?", (data.email,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=401, detail="Doctor account not found")
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Create JWT token with doctor metadata
    access_token = create_access_token(doctor_id, "doctor", doctor_name)
    store_token(DB_PATH, access_token, doctor_id, "doctor")
    
    logger.info("Doctor logged in: %s (%s)", doctor_id, doctor_name)
    return TokenResponse(
        token=access_token,
        user_id=doctor_id,
        role="doctor",
        expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", 1440)) * 60
    )

@app.post("/auth/doctor/otp/verify")
def doctor_verify_otp(data: DoctorVerifyOTPRequest):
    """
    Verify OTP for doctor account (optional second factor).
    """
    if not verify_otp(DB_PATH, data.email, data.otp_code, "doctor_verification"):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Mark doctor as verified in database
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE doctor_accounts SET verified=1 WHERE email=?
        """, (data.email,))
        cursor.execute("SELECT doctor_id FROM doctor_accounts WHERE email=?", (data.email,))
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if result:
            logger.info("Doctor OTP verified: %s", result[0])
            return {"success": True, "message": "Doctor verified successfully"}
    except Exception as e:
        logger.error("Doctor OTP verification error: %s", e)
        raise HTTPException(status_code=500, detail="Verification failed")

# ─── ADMIN AUTHENTICATION ────────────────────────────────────────────────────

@app.post("/auth/admin/login")
def admin_login(data: AdminLoginRequest):
    """
    Admin login with PIN.
    """
    if not verify_admin_pin(data.pin):
        raise HTTPException(status_code=401, detail="Invalid admin PIN")
    
    # Create JWT token for admin
    admin_id = "admin"
    access_token = create_access_token(admin_id, "admin")
    store_token(DB_PATH, access_token, admin_id, "admin")
    
    logger.info("Admin logged in")
    return TokenResponse(
        token=access_token,
        user_id=admin_id,
        role="admin",
        expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", 1440)) * 60
    )

# ─── TOKEN VERIFICATION ───────────────────────────────────────────────────────

@app.get("/auth/verify")
def verify_token_endpoint(authorization: Optional[str] = Header(None)):
    """
    Verify JWT token validity.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    token_payload = verify_token(token)
    
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "user_id": token_payload.sub,
        "role": token_payload.role,
        "expires_at": token_payload.exp,
    }

@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """
    Logout — invalidate token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    invalidate_token(DB_PATH, token)
    
    logger.info("Token invalidated")
    return {"success": True, "message": "Logged out successfully"}

# ─── ADMIN: DOCTOR ACCOUNT MANAGEMENT ──────────────────────────────────────────

class DoctorAccountCreate(BaseModel):
    doctor_id: str
    doctor_name: str
    email: str
    password: str

class DoctorAccountUpdate(BaseModel):
    doctor_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class DoctorAccountPasswordReset(BaseModel):
    new_password: str

@app.post("/admin/doctors/accounts/create")
def admin_create_doctor_account(data: DoctorAccountCreate):
    """
    Admin endpoint: Create a new doctor account.
    """
    success, message = create_doctor_account(DB_PATH, data.doctor_id, data.doctor_name, data.email, data.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    logger.info("Admin created doctor account: %s (%s)", data.doctor_id, data.email)
    return {
        "success": True,
        "message": message,
        "doctor_id": data.doctor_id,
        "email": data.email,
    }

@app.get("/admin/doctors/accounts")
def admin_get_doctor_accounts():
    """
    Admin endpoint: List all doctor accounts.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, doctor_id, doctor_name, email, is_active, verified, created_at
            FROM doctor_accounts
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        accounts = []
        for row in rows:
            accounts.append({
                "id": row["id"],
                "doctor_id": row["doctor_id"],
                "doctor_name": row["doctor_name"],
                "email": row["email"],
                "is_active": bool(row["is_active"]),
                "verified": bool(row["verified"]),
                "created_at": row["created_at"],
            })
        
        logger.info("Admin retrieved %d doctor accounts", len(accounts))
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts),
        }
    except Exception as e:
        logger.error("Error retrieving doctor accounts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve accounts")

@app.get("/admin/doctors/accounts/{doctor_id}")
def admin_get_doctor_account(doctor_id: str):
    """
    Admin endpoint: Get a specific doctor account.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, doctor_id, doctor_name, email, is_active, verified, created_at
            FROM doctor_accounts
            WHERE doctor_id = ?
        """, (doctor_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        return {
            "success": True,
            "account": {
                "id": row["id"],
                "doctor_id": row["doctor_id"],
                "doctor_name": row["doctor_name"],
                "email": row["email"],
                "is_active": bool(row["is_active"]),
                "verified": bool(row["verified"]),
                "created_at": row["created_at"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving doctor account: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve account")

@app.patch("/admin/doctors/accounts/{doctor_id}")
def admin_update_doctor_account(doctor_id: str, data: DoctorAccountUpdate):
    """
    Admin endpoint: Update a doctor account.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Verify doctor account exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        updates = {}
        if data.doctor_name is not None:
            updates["doctor_name"] = data.doctor_name
        if data.email is not None:
            # Check if email is already in use
            cursor.execute("SELECT id FROM doctor_accounts WHERE email = ? AND doctor_id != ?", (data.email, doctor_id))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=400, detail="Email already in use")
            updates["email"] = data.email
        if data.password is not None:
            updates["password_hash"] = hash_password(data.password)
        if data.is_active is not None:
            updates["is_active"] = 1 if data.is_active else 0
        
        if not updates:
            conn.close()
            return {"success": True, "message": "No changes made"}
        
        # Build update query
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        set_clause += ", updated_at = ?"
        values = list(updates.values()) + [datetime.now().isoformat(), doctor_id]
        
        cursor.execute(f"UPDATE doctor_accounts SET {set_clause} WHERE doctor_id = ?", values)
        conn.commit()
        conn.close()
        
        logger.info("Admin updated doctor account: %s", doctor_id)
        return {
            "success": True,
            "message": "Doctor account updated successfully",
            "doctor_id": doctor_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating doctor account: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update account")

@app.post("/admin/doctors/accounts/{doctor_id}/reset-password")
def admin_reset_doctor_password(doctor_id: str, data: DoctorAccountPasswordReset):
    """
    Admin endpoint: Reset a doctor's password.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Verify doctor account exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        password_hash = hash_password(data.new_password)
        cursor.execute(
            "UPDATE doctor_accounts SET password_hash = ?, updated_at = ? WHERE doctor_id = ?",
            (password_hash, datetime.now().isoformat(), doctor_id)
        )
        conn.commit()
        conn.close()
        
        logger.info("Admin reset password for doctor: %s", doctor_id)
        return {
            "success": True,
            "message": "Password reset successfully",
            "doctor_id": doctor_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting doctor password: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reset password")

@app.delete("/admin/doctors/accounts/{doctor_id}")
def admin_delete_doctor_account(doctor_id: str):
    """
    Admin endpoint: Delete/deactivate a doctor account.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Verify doctor account exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor account not found")
        
        # Soft delete — deactivate instead of deleting
        cursor.execute(
            "UPDATE doctor_accounts SET is_active = 0, updated_at = ? WHERE doctor_id = ?",
            (datetime.now().isoformat(), doctor_id)
        )
        conn.commit()
        conn.close()
        
        logger.info("Admin deactivated doctor account: %s", doctor_id)
        return {
            "success": True,
            "message": "Doctor account deactivated successfully",
            "doctor_id": doctor_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting doctor account: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete account")
