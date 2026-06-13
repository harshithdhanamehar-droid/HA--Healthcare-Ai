# -*- coding: utf-8 -*-
"""
Authentication module for HA! Healthcare AI.
Handles JWT, bcrypt password hashing, OTP generation/validation, and Google OAuth.
"""

import os
import sqlite3
import secrets
import string
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Tuple

from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import requests

logger = logging.getLogger("ha_healthcare.auth")

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production-12345")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
ADMIN_PIN = os.getenv("ADMIN_PIN", "admin2024")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# ─── PASSWORD HASHING ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain, hashed)

# ─── JWT TOKEN MANAGEMENT ────────────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str  # user, doctor, admin
    exp: Optional[int] = None

def create_access_token(user_id: str, role: str, doctor_name: str = None) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    # Add doctor metadata if it's a doctor role
    if role == "doctor" and doctor_name:
        payload["doctor_name"] = doctor_name
        payload["doctor_id"] = user_id
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("Invalid token: %s", e)
        return None

# ─── OTP MANAGEMENT ──────────────────────────────────────────────────────────
def generate_otp(length: int = 6) -> str:
    """Generate a random 6-digit OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))

def store_otp(db_path: str, email: str, otp_code: str, purpose: str, ttl_minutes: int = 10) -> bool:
    """Store OTP in database with expiration."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        expires_at = (datetime.utcnow() + timedelta(minutes=ttl_minutes)).isoformat()
        cursor.execute(
            """
            INSERT INTO otp_store (email, otp_code, purpose, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, otp_code, purpose, expires_at, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        logger.info("OTP stored for email %s, purpose: %s", email, purpose)
        return True
    except Exception as e:
        logger.error("Failed to store OTP: %s", e)
        return False

def verify_otp(db_path: str, email: str, otp_code: str, purpose: str) -> bool:
    """Verify OTP and check expiration."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM otp_store
            WHERE email = ? AND otp_code = ? AND purpose = ? AND expires_at > ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (email, otp_code, purpose, datetime.utcnow().isoformat()),
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            logger.info("OTP verified for email %s, purpose: %s", email, purpose)
            return True
        else:
            logger.warning("OTP verification failed for email %s", email)
            return False
    except Exception as e:
        logger.error("OTP verification error: %s", e)
        return False

def send_otp_email(email: str, otp_code: str, purpose: str = "verification") -> bool:
    """Send OTP via Gmail SMTP."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not configured")
        return False
    
    try:
        subject = f"HA! Healthcare AI - {purpose.title()} Code"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>HA! Healthcare AI</h2>
                <p>Your {purpose} code is:</p>
                <h1 style="color: #2563eb;">{otp_code}</h1>
                <p>This code expires in 10 minutes.</p>
                <p>Do not share this code with anyone.</p>
                <hr>
                <small>If you did not request this code, please ignore this email.</small>
            </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = email
        msg.attach(MIMEText(body, "html"))
        
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, email, msg.as_string())
        
        logger.info("OTP email sent to %s", email)
        return True
    except Exception as e:
        logger.error("Failed to send OTP email: %s", e)
        return False

# ─── DOCTOR ACCOUNT MANAGEMENT ───────────────────────────────────────────────
def create_doctor_account(db_path: str, doctor_id: str, doctor_name: str, email: str, password: str) -> Tuple[bool, str]:
    """Create a doctor account with hashed password."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM doctor_accounts WHERE email = ?", (email,))
        if cursor.fetchone():
            return False, "Email already registered"
        
        password_hash = hash_password(password)
        cursor.execute(
            """
            INSERT INTO doctor_accounts (doctor_id, doctor_name, email, password_hash, is_active, verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, 0, ?, ?)
            """,
            (doctor_id, doctor_name, email, password_hash, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        logger.info("Doctor account created: %s (%s)", doctor_name, email)
        return True, "Account created successfully"
    except Exception as e:
        logger.error("Failed to create doctor account: %s", e)
        return False, str(e)

def verify_doctor_credentials(db_path: str, email: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Verify doctor email and password. Returns (success, doctor_id, doctor_name)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doctor_id, doctor_name, password_hash, is_active FROM doctor_accounts WHERE email = ?",
            (email,),
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            doctor_id, doctor_name, password_hash, is_active = result
            if not is_active:
                logger.warning("Inactive doctor account attempted login: %s", email)
                return False, None, None
            if verify_password(password, password_hash):
                logger.info("Doctor credentials verified: %s (%s)", email, doctor_name)
                return True, doctor_id, doctor_name
        
        logger.warning("Doctor credentials verification failed: %s", email)
        return False, None, None
    except Exception as e:
        logger.error("Doctor credential verification error: %s", e)
        return False, None, None

# ─── GOOGLE OAUTH MANAGEMENT ────────────────────────────────────────────────
def verify_google_token(token: str) -> Optional[Dict]:
    """Verify Google OAuth token and return user info."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.warning("Google OAuth not configured")
        return None
    
    try:
        # Verify token with Google
        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": token},
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.warning("Google token verification failed")
            return None
        
        data = response.json()
        return {
            "google_sub": data.get("user_id"),
            "email": data.get("email"),
            "name": data.get("name"),
        }
    except Exception as e:
        logger.error("Google token verification error: %s", e)
        return None

def link_google_auth(db_path: str, google_sub: str, user_id: str, email: str) -> bool:
    """Link Google OAuth account to user."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if already linked
        cursor.execute("SELECT id FROM google_auth WHERE google_sub = ?", (google_sub,))
        if cursor.fetchone():
            logger.warning("Google account already linked")
            conn.close()
            return False
        
        cursor.execute(
            """
            INSERT INTO google_auth (google_sub, user_id, email, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (google_sub, user_id, email, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        logger.info("Google auth linked for user %s", user_id)
        return True
    except Exception as e:
        logger.error("Failed to link Google auth: %s", e)
        return False

def get_user_by_google_sub(db_path: str, google_sub: str) -> Optional[str]:
    """Get user_id by Google subject. Returns user_id or None."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM google_auth WHERE google_sub = ?", (google_sub,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error("Failed to get user by Google sub: %s", e)
        return None

# ─── ADMIN PIN VERIFICATION ─────────────────────────────────────────────────
def verify_admin_pin(pin: str) -> bool:
    """Verify admin PIN (simple string comparison)."""
    return pin == ADMIN_PIN

# ─── TOKEN STORAGE (OPTIONAL - FOR SESSION TRACKING) ────────────────────────
def store_token(db_path: str, token: str, user_id: str, user_role: str) -> bool:
    """Store token in database for session tracking."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        expires_at = (datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)).isoformat()
        cursor.execute(
            """
            INSERT INTO auth_tokens (token, user_id, user_role, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (token, user_id, user_role, expires_at, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        logger.info("Token stored for user %s (%s)", user_id, user_role)
        return True
    except Exception as e:
        logger.error("Failed to store token: %s", e)
        return False

def invalidate_token(db_path: str, token: str) -> bool:
    """Remove token from database (logout)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        logger.info("Token invalidated")
        return True
    except Exception as e:
        logger.error("Failed to invalidate token: %s", e)
        return False
