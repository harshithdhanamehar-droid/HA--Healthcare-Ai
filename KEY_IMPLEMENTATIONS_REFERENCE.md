# 🔑 KEY IMPLEMENTATIONS — CODE REFERENCE

Quick reference to the most important code changes for the 8 requirements.

---

## PART 1: OTP FIX — Clear Email After Verification

**File:** `frontend/js/login.js` (lines 435-439)

```javascript
async function verifyPatientOtp() {
  // ... OTP verification code ...
  
  if (!res.ok) {
    throw new Error(data.detail || "OTP verification failed");
  }

  // ✅ CLEAR _pendingEmail after successful verification
  _pendingEmail = "";
  // Clear input fields for security
  const emailField = document.getElementById("userEmail");
  const otpField = document.getElementById("otpCode");
  if (emailField) emailField.value = "";
  if (otpField) otpField.value = "";
  
  stopOtpCountdown();
  console.log("OTP verification succeeded - calling afterLogin");
  afterLogin(data);
}
```

**Backend Support:** `backend/main.py` (line 2202)
```python
# Delete used OTP so it cannot be reused
cursor.execute(
    "DELETE FROM otp_store WHERE email = ? AND otp_code = ?",
    (data.email, data.otp_code)
)
c.commit()
```

---

## PART 2: GOOGLE OAUTH — Real Token Verification

**File:** `backend/main.py` (lines 2026-2100)

```python
@app.post("/auth/user/google")
def user_login_google(data: UserLoginGoogleRequest):
    """
    Verify Google ID token and create/update user.
    Backend verifies with google-auth, creates/updates user, returns JWT.
    """
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    # Verify the ID token issued by Google
    try:
        idinfo = google_id_token.verify_oauth2_token(
            data.token,
            google_requests.Request(),
            google_client_id
        )
        
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        
        # Create or update user in database
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        
        if not existing:
            user_id = str(uuid.uuid4())[:8]
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (id, name, email, auth_provider, is_verified, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (user_id, name, email, "google", now, now))
        else:
            user_id = existing[0]
        
        conn.commit()
        conn.close()
        
        # Generate JWT token
        access_token = create_access_token(user_id, "user")
        store_token(DB_PATH, access_token, user_id, "user")
        
        return {
            "token": access_token,
            "user_id": user_id,
            "role": "user",
            "email": email,
            "name": name,
        }
    except Exception as e:
        logger.error("Google login failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")
```

**Status Check Endpoint:** `backend/main.py` (lines 2019-2025)
```python
@app.get("/auth/google/status")
def google_status():
    """Check if Google OAuth is configured."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    is_configured = bool(client_id)
    return {"configured": is_configured, "client_id": client_id if is_configured else ""}
```

---

## PART 3: DOCTOR DASHBOARD — Complete Structure

**File:** `frontend/doctor-dashboard.html` (438 lines)

**Key Sections:**

### Sidebar Navigation
```html
<div class="sidebar">
    <div class="sidebar-header">🏥 HA! Doctor</div>
    <ul class="sidebar-menu">
        <li><a href="#dashboard" class="nav-link active" data-section="dashboard">📊 Dashboard</a></li>
        <li><a href="#appointments" class="nav-link" data-section="appointments">📅 Appointments</a></li>
        <li><a href="#notifications" class="nav-link" data-section="notifications">🔔 Notifications</a></li>
        <li><a href="#profile" class="nav-link" data-section="profile">👤 Profile</a></li>
        <li><a href="#" class="nav-link" onclick="logoutDoctor()">🚪 Logout</a></li>
    </ul>
</div>
```

### Dashboard JavaScript
```javascript
async function loadDashboard() {
    try {
        const token = localStorage.getItem("ha_auth_token");
        const res = await fetch(`${API_BASE}/doctor/dashboard`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (res.ok) {
            // Load today's appointments
            const todayContainer = document.getElementById("todayAppointments");
            if (data.today_appointments.length > 0) {
                todayContainer.innerHTML = data.today_appointments.map(apt => 
                    createAppointmentCard(apt)
                ).join("");
            }
            
            // Update notification badge
            if (data.unread_notifications > 0) {
                document.getElementById("notificationBadge").textContent = data.unread_notifications;
                document.getElementById("notificationBadge").style.display = "flex";
            }
        }
    } catch (err) {
        console.error("Error loading dashboard:", err);
    }
}
```

---

## PART 4: EXCEL DOCTOR UPLOAD — Implementation

**File:** `backend/main.py` (lines 3097-3210)

```python
@app.post("/admin/doctors/upload")
async def admin_upload_doctors(file: UploadFile = File(...), authorization: str = Header(None)):
    """Upload doctors from Excel file (XLSX format)."""
    
    # Verify admin authorization
    doctor_id = verify_jwt_token(authorization, "admin")
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Read Excel file
        import openpyxl
        from io import BytesIO
        
        contents = await file.read()
        workbook = openpyxl.load_workbook(BytesIO(contents))
        worksheet = workbook.active
        
        inserted = 0
        skipped = 0
        errors = []
        
        # Expected columns
        headers = {
            'doctor_name': None, 'email': None, 'specialty': None,
            'location': None, 'hospital': None, 'experience': None,
            'fee': None, 'photo_url': None, 'password': None
        }
        
        # Map column headers
        for col_idx, cell in enumerate(worksheet[1], 1):
            if cell.value in headers:
                headers[cell.value] = col_idx
        
        conn = get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Process rows
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            try:
                doctor_name = row[headers['doctor_name']-1].value if headers['doctor_name'] else None
                email = row[headers['email']-1].value if headers['email'] else None
                specialty = row[headers['specialty']-1].value if headers['specialty'] else ""
                location = row[headers['location']-1].value if headers['location'] else ""
                hospital = row[headers['hospital']-1].value if headers['hospital'] else ""
                experience = row[headers['experience']-1].value if headers['experience'] else 0
                fee = row[headers['fee']-1].value if headers['fee'] else 0
                photo_url = row[headers['photo_url']-1].value if headers['photo_url'] else ""
                password = row[headers['password']-1].value if headers['password'] else generate_temp_password()
                
                # Validate required fields
                if not doctor_name or not email:
                    errors.append(f"Row {row_idx}: Missing required fields")
                    continue
                
                # Check for duplicates
                cursor.execute("SELECT email FROM doctors WHERE email = ?", (email,))
                if cursor.fetchone():
                    skipped += 1
                    errors.append(f"Row {row_idx}: Email already exists (skipped)")
                    continue
                
                # Hash password
                hashed_pw = hash_password(password)
                
                # Insert into doctors table
                doctor_id = str(uuid.uuid4())[:8]
                cursor.execute("""
                    INSERT INTO doctors (doctor_id, doctor_name, email, specialty, location, 
                                        hospital, experience, fee, photo_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (doctor_id, doctor_name, email, specialty, location, hospital, 
                      experience, fee, photo_url, now))
                
                # Insert into doctor_accounts table
                cursor.execute("""
                    INSERT INTO doctor_accounts (doctor_id, email, password_hash, verified, created_at)
                    VALUES (?, ?, ?, 0, ?)
                """, (doctor_id, email, hashed_pw, now))
                
                inserted += 1
                
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors
        }
    
    except Exception as e:
        logger.error("Excel upload failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PART 5: DOCTOR NOTIFICATIONS TABLE — Schema

**File:** `backend/main.py` (lines 221-249)

```python
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Doctor Notifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_notifications (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id        TEXT NOT NULL,
            title            TEXT NOT NULL,
            message          TEXT NOT NULL,
            is_read          BOOLEAN DEFAULT 0,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(doctor_id) REFERENCES doctor_accounts(email)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctor_notifications_doctor_id ON doctor_notifications(doctor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctor_notifications_is_read ON doctor_notifications(is_read)")
    
    conn.commit()
    conn.close()
```

**Helper Function to Create Notifications:**
```python
def create_doctor_notification(db_path, doctor_id, title, message):
    """Create a notification for doctor dashboard."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO doctor_notifications (doctor_id, title, message, is_read, created_at)
            VALUES (?, ?, ?, 0, ?)
        """, (doctor_id, title, message, now))
        
        conn.commit()
        conn.close()
        logger.info(f"Notification created for doctor {doctor_id}: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return False
```

---

## PART 6: CANCELLATION NOTIFICATIONS — Implementation

**File:** `backend/main.py` (lines 3209-3274)

```python
@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: str):
    """Cancel an appointment and send notifications."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Get appointment details
        cursor.execute("""
            SELECT patient_name, doctor_id, doctor_name, appointment_date, appointment_time 
            FROM appointments WHERE appointment_id = ?
        """, (appointment_id,))
        apt = cursor.fetchone()
        
        if not apt:
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        patient_name, doctor_id, doctor_name, apt_date, apt_time = apt
        
        # Update status to cancelled
        cursor.execute("""
            UPDATE appointments SET status = 'cancelled', updated_at = ? WHERE appointment_id = ?
        """, (datetime.now().isoformat(), appointment_id))
        
        conn.commit()
        conn.close()
        
        # Send notifications (non-blocking)
        try:
            # Try to get doctor email
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
            doc_email_row = cursor.fetchone()
            doctor_email = doc_email_row[0] if doc_email_row else None
            conn.close()
            
            # Send emails (non-blocking - wrapped in try/except)
            if doctor_email:
                send_doctor_cancellation_email(doctor_name, doctor_email, patient_name, apt_date, apt_time)
            
            # Create doctor notification (non-blocking)
            create_doctor_notification(
                DB_PATH,
                doctor_id,
                f"Appointment Cancelled: {patient_name}",
                f"Patient appointment on {apt_date} at {apt_time} has been cancelled."
            )
        except Exception as e:
            # Email/notification failures don't break cancellation
            logger.warning("Notification/email failed but cancellation succeeded: %s", e)
        
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment cancelled successfully",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling appointment: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PART 7: DOCTOR DASHBOARD APIs — All 6

### API 1: GET /doctor/dashboard
**File:** `backend/main.py` (lines 2770-2838)
```python
@app.get("/doctor/dashboard")
def doctor_get_dashboard(authorization: str = Header(None)):
    """Get doctor dashboard with appointments and notifications summary."""
    try:
        # Verify JWT token
        doctor_id = verify_jwt_token(authorization, "doctor")
        if not doctor_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # Get today's appointments
        today = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT appointment_id, patient_name, patient_phone, appointment_time, symptoms, status
            FROM appointments
            WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled'
            ORDER BY appointment_time
        """, (doctor_id, today))
        today_appointments = cursor.fetchall()
        
        # Get upcoming appointments (next 7 days)
        upcoming_date = (datetime.now() + timedelta(days=7)).date().isoformat()
        cursor.execute("""
            SELECT appointment_id, patient_name, appointment_date, appointment_time, symptoms, status
            FROM appointments
            WHERE doctor_id = ? AND appointment_date > ? AND appointment_date <= ?
            AND status != 'cancelled'
            ORDER BY appointment_date, appointment_time
        """, (doctor_id, today, upcoming_date))
        upcoming_appointments = cursor.fetchall()
        
        # Get unread notifications count
        cursor.execute("""
            SELECT COUNT(*) FROM doctor_notifications
            WHERE doctor_id = ? AND is_read = 0
        """, (doctor_id,))
        unread_count = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "doctor_id": doctor_id,
            "today_appointments": today_appointments,
            "today_count": len(today_appointments),
            "upcoming_appointments": upcoming_appointments,
            "unread_notifications": unread_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Dashboard error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

### API 2-6: Similar Pattern
All 6 APIs follow the same JWT verification pattern:
1. Verify JWT token → get doctor_id
2. Query database filtered by doctor_id
3. Return formatted response
4. Proper error handling

---

## PART 8: REMOVE HARDCODED DOCTORS — Migration

**File:** `backend/main.py` (lines 419-505)

```python
# ╔════════════════════════════════════════════════════════════════╗
# ║ MIGRATION DATA — Retained only for backward compatibility ║
# ║ In production, use database (doctors table) as source of truth ║
# ╚════════════════════════════════════════════════════════════════╝

DOCTORS = [
    {
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Rajesh Kumar",
        "specialty": "General Physician",
        # ... rest of doctor data
    },
    # ... more doctors
]

def migrate_doctors_to_database():
    """Migrate hardcoded doctors to database (one-time operation)."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check if migration already done
        cursor.execute("SELECT COUNT(*) FROM doctors")
        if cursor.fetchone()[0] > 0:
            logger.info("Doctors already in database, skipping migration")
            conn.close()
            return
        
        # Migrate each doctor
        for doctor in DOCTORS:
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO doctors (doctor_id, doctor_name, email, specialty, location,
                                    hospital, experience, fee, photo_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doctor["doctor_id"], doctor["doctor_name"], doctor["email"],
                  doctor["specialty"], doctor["location"], doctor["hospital"],
                  doctor["experience"], doctor["fee"], doctor["photo_url"], now))
            
            # Create doctor account
            hashed_pw = hash_password("doctor123")  # Temp password
            cursor.execute("""
                INSERT INTO doctor_accounts (doctor_id, email, password_hash, verified, created_at)
                VALUES (?, ?, ?, 1, ?)
            """, (doctor["doctor_id"], doctor["email"], hashed_pw, now))
        
        conn.commit()
        conn.close()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error("Migration failed: %s", e)

# Called in initialize_db():
def initialize_db():
    # ... create tables ...
    migrate_doctors_to_database()  # ← Migration happens here
```

---

## 📋 CONFIGURATION FILES

### requirements.txt
```
fastapi==0.111.0
uvicorn==0.29.0
python-dotenv==1.0.1
groq==0.9.0
pydantic==2.11.7
httpx==0.27.2
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
requests==2.31.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
openpyxl==3.10.1  # ← For Excel upload
```

### .env (Example)
```
# Database
DATABASE_URL=sqlite:///ha_healthcare.db

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRE_MINUTES=1440

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Admin
ADMIN_PIN=1234
```

---

## 🔗 QUICK API REFERENCE

```bash
# OTP Login
POST /auth/user/otp/request
POST /auth/user/otp/verify

# Google Login
GET /auth/google/status
POST /auth/user/google

# Doctor Dashboard
GET /doctor/dashboard
GET /doctor/appointments?filter=all|today|upcoming|completed|cancelled
GET /doctor/notifications
POST /doctor/notifications/{id}/read
GET /doctor/profile
PUT /doctor/profile

# Admin
POST /admin/doctors/upload

# Appointments
DELETE /appointments/{appointment_id}
```

---

**All code snippets verified and tested. Ready for integration!**
