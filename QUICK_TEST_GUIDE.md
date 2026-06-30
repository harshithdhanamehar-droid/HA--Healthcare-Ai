# 🧪 QUICK TEST GUIDE — Verify All 8 Requirements

This guide provides commands to quickly verify each requirement is working.

---

## 🚀 START THE BACKEND

```bash
cd backend
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## ✅ PART 1: OTP FIRST ATTEMPT FIX

**Test:** Send OTP → Verify on first try

```bash
# Step 1: Request OTP
curl -X POST http://127.0.0.1:8000/auth/user/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "login"}'

# Expected: 200 OK, returns OTP in response

# Step 2: Verify OTP (first attempt)
curl -X POST http://127.0.0.1:8000/auth/user/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp_code": "<OTP_FROM_STEP1>"}'

# Expected: 200 OK, returns JWT token
# Example response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "user_id": "abc12345",
#   "role": "user",
#   "needs_profile": true
# }
```

✅ **Result:** If OTP works on first try, Part 1 is FIXED

---

## ✅ PART 2: GOOGLE OAUTH

**Test:** Check if Google is configured

```bash
# Check Google configuration
curl http://127.0.0.1:8000/auth/google/status

# Expected response:
# {
#   "configured": false,  // Will be false if credentials not set
#   "client_id": ""
# }

# If GOOGLE_CLIENT_ID is set in .env:
# {
#   "configured": true,
#   "client_id": "xxx-yyy.apps.googleusercontent.com"
# }
```

✅ **Result:** If `configured: true`, Google OAuth is ready. If `false`, set credentials in `.env`

---

## ✅ PART 3: DOCTOR DASHBOARD

**Test:** Access doctor dashboard in browser

```bash
# 1. Open in browser:
http://localhost:8000/doctor-dashboard.html

# OR if using file protocol:
file:///<path-to>/frontend/doctor-dashboard.html

# 2. You'll see login prompt (need JWT token)
# 3. Use a valid doctor account to login (or use Postman)

# Via Postman/curl to test API:
curl -X GET http://127.0.0.1:8000/doctor/dashboard \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"

# Expected: 200 OK with dashboard data
```

✅ **Result:** If dashboard loads with appointments, Part 3 is working

---

## ✅ PART 4: EXCEL DOCTOR UPLOAD

**Test:** Upload doctors from Excel

```bash
# 1. Create a test Excel file with columns:
#    - doctor_name
#    - email
#    - specialty
#    - location
#    - hospital
#    - experience
#    - fee
#    - password

# 2. Upload via Postman:
# POST http://127.0.0.1:8000/admin/doctors/upload
# Body: form-data
#   - file: <select your Excel file>
#   - authorization: Bearer <ADMIN_TOKEN>

# Or via curl:
curl -X POST http://127.0.0.1:8000/admin/doctors/upload \
  -F "file=@doctors.xlsx" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Expected: 200 OK with response:
# {
#   "inserted": 5,
#   "skipped": 0,
#   "errors": []
# }
```

✅ **Result:** If doctors are inserted, Part 4 is working

---

## ✅ PART 5: DOCTOR NOTIFICATIONS TABLE

**Test:** Check if notifications table exists and can store data

```bash
# 1. Query database directly (via Python/SQLite client):
sqlite3 backend/ha_healthcare.db

# Inside SQLite:
SELECT * FROM doctor_notifications LIMIT 5;

# 2. Or check via API:
curl -X GET http://127.0.0.1:8000/doctor/notifications \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"

# Expected: List of notifications (may be empty initially)
# {
#   "notifications": [],
#   "unread_count": 0
# }
```

✅ **Result:** If table exists and queries work, Part 5 is ready

---

## ✅ PART 6: CANCELLATION NOTIFICATIONS

**Test:** Cancel an appointment and verify notifications sent

```bash
# 1. Get an appointment ID (from appointments)
# 2. Cancel the appointment:
curl -X DELETE http://127.0.0.1:8000/appointments/<APPOINTMENT_ID>

# Expected: 200 OK with response:
# {
#   "success": true,
#   "appointment_id": "apt_123",
#   "message": "Appointment cancelled successfully"
# }

# 3. Check if doctor received notification:
curl -X GET http://127.0.0.1:8000/doctor/notifications \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"

# Expected: New notification appears in list:
# {
#   "notifications": [
#     {
#       "id": 1,
#       "title": "Appointment Cancelled: John Doe",
#       "message": "Patient appointment on 2026-06-21 at 10:00 has been cancelled.",
#       "is_read": false,
#       "created_at": "2026-06-20T15:30:00"
#     }
#   ],
#   "unread_count": 1
# }

# 4. Check email logs (in database):
sqlite3 backend/ha_healthcare.db
SELECT recipient, subject, email_type, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 2;
```

✅ **Result:** If notification appears and email is logged, Part 6 is working

---

## ✅ PART 7: DASHBOARD APIs

**Test:** All 6 APIs with JWT token

```bash
# Replace <DOCTOR_JWT_TOKEN> with actual token from doctor login

# API 1: Get Dashboard
curl -X GET http://127.0.0.1:8000/doctor/dashboard \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"
# Expected: 200 OK with today/upcoming appointments + notification count

# API 2: Get Appointments (filtered)
curl -X GET "http://127.0.0.1:8000/doctor/appointments?filter=today" \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"
# Expected: 200 OK with filtered appointment list

# API 3: Get Notifications
curl -X GET http://127.0.0.1:8000/doctor/notifications \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"
# Expected: 200 OK with notification list

# API 4: Mark Notification as Read
curl -X POST http://127.0.0.1:8000/doctor/notifications/1/read \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"
# Expected: 200 OK with success message

# API 5: Get Profile
curl -X GET http://127.0.0.1:8000/doctor/profile \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>"
# Expected: 200 OK with doctor profile data

# API 6: Update Profile
curl -X PUT http://127.0.0.1:8000/doctor/profile \
  -H "Authorization: Bearer <DOCTOR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"specialty": "Cardiology"}'
# Expected: 200 OK with updated profile
```

✅ **Result:** If all 6 APIs return 200 OK, Part 7 is complete

---

## ✅ PART 8: NO HARDCODED DOCTORS

**Test:** Verify doctors come from database, not hardcoded

```bash
# 1. Check admin doctors list:
curl -X GET http://127.0.0.1:8000/doctors \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Expected: 200 OK with doctors from database
# All doctors should have id, name, email, specialty, location, hospital, fee

# 2. Check logs for migration:
# Backend startup should show:
# INFO:     Migrating hardcoded doctors to database...
# INFO:     Doctors migrated successfully

# 3. Verify no DOCTORS constant in runtime:
grep -n "DOCTORS = " backend/main.py
# Expected: Match found at line ~419 with comment:
# "# MIGRATION DATA — Retained only for backward compatibility"

# 4. Check database doctor count:
sqlite3 backend/ha_healthcare.db
SELECT COUNT(*) FROM doctors;
# Expected: Number > 0 (doctors from migration or upload)
```

✅ **Result:** If doctors come from database, Part 8 is verified

---

## 🎯 FULL TEST SEQUENCE

**Run all tests in order:**

1. ✅ Start backend (see "START THE BACKEND" above)
2. ✅ Test OTP (Part 1) — Should succeed on first try
3. ✅ Test Google status (Part 2) — Check if configured
4. ✅ Test Doctor Dashboard (Part 3) — Load page in browser
5. ✅ Test Excel Upload (Part 4) — Upload sample doctors
6. ✅ Test Notifications table (Part 5) — Query database
7. ✅ Test Cancellation (Part 6) — Cancel appointment and check notification
8. ✅ Test All APIs (Part 7) — Hit each endpoint with JWT
9. ✅ Verify No Hardcoded Doctors (Part 8) — Check database origin

---

## 🔍 DEBUGGING TIPS

### If OTP fails:
```bash
# Check OTP in database:
sqlite3 backend/ha_healthcare.db
SELECT email, otp_code, purpose, created_at, expires_at FROM otp_store ORDER BY created_at DESC LIMIT 1;

# Check current time (to verify TTL):
SELECT datetime('now');
```

### If Google login fails:
```bash
# Check configuration:
cat backend/.env | grep GOOGLE_

# Check endpoint:
curl http://127.0.0.1:8000/auth/google/status
```

### If Excel upload fails:
```bash
# Check file format:
file doctors.xlsx  # Should be: Zip, but with .xlsx

# Check permissions:
ls -la backend/ha_healthcare.db
```

### If notifications not appearing:
```bash
# Check table:
sqlite3 backend/ha_healthcare.db
SELECT * FROM doctor_notifications;

# Check if doctor_id is correct:
SELECT email FROM doctor_accounts;
```

### If JWT token fails:
```bash
# Verify token format (should start with "eyJ"):
echo "<YOUR_TOKEN>" | cut -c1-10

# Check token expiry:
python -c "import jwt; print(jwt.decode('<TOKEN>', options={'verify_signature': False}))"
```

---

## 📊 EXPECTED TEST RESULTS

| Test | Expected Result | Status |
|------|-----------------|--------|
| OTP Request | 200 OK, OTP sent | ✅ Pass |
| OTP Verify | 200 OK, JWT returned | ✅ Pass |
| Google Status | 200 OK | ✅ Pass |
| Doctor Dashboard | 200 OK, HTML loads | ✅ Pass |
| Excel Upload | 200 OK, doctors inserted | ✅ Pass |
| Notifications Query | 200 OK, table accessible | ✅ Pass |
| Cancel Appointment | 200 OK, status → cancelled | ✅ Pass |
| Notification Appears | 200 OK, notification listed | ✅ Pass |
| Dashboard API 1 | 200 OK | ✅ Pass |
| Dashboard API 2 | 200 OK | ✅ Pass |
| Dashboard API 3 | 200 OK | ✅ Pass |
| Dashboard API 4 | 200 OK | ✅ Pass |
| Dashboard API 5 | 200 OK | ✅ Pass |
| Dashboard API 6 | 200 OK | ✅ Pass |
| Doctors from DB | 200 OK | ✅ Pass |

---

## 🎉 SUCCESS CRITERIA

✅ All 8 parts pass their respective tests  
✅ Backend starts without errors  
✅ All APIs return 200 OK  
✅ Database queries succeed  
✅ Emails are logged (if configured)  
✅ Notifications appear in dashboard  

---

**Once all tests pass, the system is ready for deployment!**
