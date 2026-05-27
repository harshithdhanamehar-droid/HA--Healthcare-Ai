# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

import uuid
from datetime import datetime

app = FastAPI(title="HA! Healthcare AI API", version="2.0.0")

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── IN-MEMORY STORES ────────────────────────────────────────────────────────
appointments_db: List[dict] = []
users_db: dict = {}

# ─── DOCTORS DATA ─────────────────────────────────────────────────────────────
DOCTORS = [
    {
        "id": "d001",
        "name": "Dr. Priya Sharma",
        "specialty": "General Physician",
        "experience": "12 years",
        "rating": 4.9,
        "available_slots": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM"],
        "fee": 500,
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
        "image": "https://api.dicebear.com/7.x/personas/svg?seed=vikram",
        "hospital": "HA! Diabetes Care Center",
        "languages": ["English", "Hindi", "Punjabi"],
    },
]

# ─── MODELS ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    username: Optional[str] = "Patient"

class SymptomRequest(BaseModel):
    symptoms: List[str]
    age: Optional[int] = None
    gender: Optional[str] = None

class AppointmentRequest(BaseModel):
    patient_name: str
    patient_phone: str
    doctor_id: str
    date: str
    time_slot: str
    reason: Optional[str] = ""

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
    user_id = str(uuid.uuid4())[:8]
    users_db[user.phone] = {
        "id": user_id,
        "name": user.name,
        "phone": user.phone,
        "location": user.location,
        "joined": datetime.now().isoformat(),
    }
    return {"success": True, "user_id": user_id, "name": user.name}

@app.post("/chat")
async def chat(data: ChatRequest):
    system_prompt = (
        "You are HA!, an expert AI-powered healthcare assistant. "
        "You provide accurate, empathetic, and helpful medical information. "
        "Always recommend consulting a real doctor for serious conditions. "
        "Keep responses clear, structured, and easy to understand. "
        f"You are speaking with patient: {data.username}."
    )
    reply = call_ai(data.message, system_prompt)
    return {"response": reply, "timestamp": datetime.now().isoformat()}

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
    if specialty:
        filtered = [d for d in DOCTORS if specialty.lower() in d["specialty"].lower()]
        return {"doctors": filtered, "count": len(filtered)}
    return {"doctors": DOCTORS, "count": len(DOCTORS)}

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    doctor = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.post("/appointments/book")
def book_appointment(data: AppointmentRequest):
    doctor = next((d for d in DOCTORS if d["id"] == data.doctor_id), None)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    appointment_id = "APT" + str(uuid.uuid4())[:6].upper()
    appointment = {
        "id": appointment_id,
        "patient_name": data.patient_name,
        "patient_phone": data.patient_phone,
        "doctor_id": data.doctor_id,
        "doctor_name": doctor["name"],
        "specialty": doctor["specialty"],
        "hospital": doctor["hospital"],
        "date": data.date,
        "time_slot": data.time_slot,
        "reason": data.reason,
        "fee": doctor["fee"],
        "status": "confirmed",
        "booked_at": datetime.now().isoformat(),
    }
    appointments_db.append(appointment)
    return {
        "success": True,
        "appointment": appointment,
        "message": f"Appointment confirmed with {doctor['name']} on {data.date} at {data.time_slot}",
    }

@app.get("/appointments/{phone}")
def get_appointments(phone: str):
    user_appointments = [a for a in appointments_db if a["patient_phone"] == phone]
    return {"appointments": user_appointments, "count": len(user_appointments)}

@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: str):
    global appointments_db
    apt = next((a for a in appointments_db if a["id"] == appointment_id), None)
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appointments_db = [a for a in appointments_db if a["id"] != appointment_id]
    return {"success": True, "message": "Appointment cancelled successfully"}

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
