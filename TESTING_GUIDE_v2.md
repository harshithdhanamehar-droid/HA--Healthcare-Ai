# Testing Guide - HA! Healthcare AI v2

## Pre-Testing Setup

### Start Backend Server
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Server should start at `http://127.0.0.1:8000`

### Database Reset (if needed)
```bash
# Backup current database
cp ha_healthcare.db ha_healthcare.db.backup

# Delete database (next startup will recreate)
rm ha_healthcare.db

# Run backend - will create fresh database and run migrations
python main.py
```

---

## PART 1: OTP FIRST ATTEMPT FAILURE FIX

### Test Case 1.1: Sequential OTP Requests
**Objective:** Verify that requesting OTP twice uses the latest OTP

**Steps:**
1. Go to http://localhost:3000 (or frontend index.html)
2. Click "Patient" tab
3. Enter email: `test@example.com`
4. Click "Continue"
5. Wait for OTP to be sent
6. **Note the OTP sent** (check console or dev mode if available)
7. Without entering the first OTP, request a new one:
   - Click "Back" button
   - Enter same email: `test@example.com`
   - Click "Continue"
   - Wait for new OTP to be sent
   - **Note the new OTP** (should be different)
8. Enter the **new OTP** in the OTP field
9. Click "Verify OTP & Login"

**Expected Result:** ✅ Login succeeds with new OTP
- Old OTP is deleted from database
- Email field is cleared
- _pendingEmail is reset in frontend
- Can proceed to profile setup

**Verification Points:**
- Check console logs: "OTP verified successfully"
- Check console logs: "OTP deleted from database"
- Email input field is empty after successful verification

---

### Test Case 1.2: OTP Expiration
**Objective:** Verify expired OTP is rejected

**Steps:**
1. Request OTP for `test2@example.com`
2. Wait 15+ minutes (OTP expires after 15 minutes)
3. Enter the old OTP
4. Click "Verify OTP & Login"

**Expected Result:** ✅ Error message: "Invalid or expired OTP. Please request a new one."

---

### Test Case 1.3: Reuse Prevention
**Objective:** Verify used OTP cannot be reused

**Steps:**
1. Request OTP for `test3@example.com`
2. Enter OTP and click "Verify OTP & Login"
3. Complete profile setup (if needed) and login
4. Logout
5. Go back to login page
6. Try to use the same OTP again (if still within 15 min window)

**Expected Result:** ✅ Error message: "Invalid or expired OTP. Please request a new one."

---

## PART 2: REAL GOOGLE OAUTH INTEGRATION

### Test Case 2.1: Google OAuth Status Check
**Objective:** Verify backend returns correct Google OAuth configuration status

**Steps:**
1. Open browser console (F12)
2. Make API call:
   ```javascript
   fetch('http://127.0.0.1:8000/auth/google/status')
     .then(r => r.json())
     .then(d => console.log(d))
   ```

**Expected Result:** ✅ Returns:
```json
{
  "configured": false,
  "client_id": ""
}
```
(If placeholder credentials in .env, `configured` will be false)

---

### Test Case 2.2: Google Button State
**Objective:** Verify Google login button is disabled when not configured

**Steps:**
1. Go to http://localhost:3000
2. Look for "Continue with Google" button

**Expected Result:** ✅
- Button is DISABLED (grayed out)
- Tooltip says "Google login is not configured."

### Test Case 2.3: Google OAuth Configuration (With Real Credentials)
**Steps (Only if you have real Google credentials):**
1. Update `.env` with real `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
2. Restart backend server
3. Refresh frontend
4. Google button should now be ENABLED
5. Click "Continue with Google"
6. Complete Google Sign-In flow
7. Should create user account and redirect to profile setup or chat

**Expected Result:** ✅
- User account created with google_sub
- Location setup modal appears (if first login)
- Can proceed to chat after completing profile

---

## PART 3: DOCTOR DASHBOARD

### Test Case 3.1: Doctor Dashboard Loading
**Objective:** Verify doctor dashboard loads correctly

**Prerequisites:**
- Doctor account must exist in database
- Doctor must be logged in

**Steps:**
1. As admin, create a doctor account (or login as doctor if exists)
2. Navigate to `http://localhost:3000/doctor-dashboard.html`
3. Dashboard should display:
   - Doctor name in header
   - Doctor email in header
   - Today's appointments section
   - Upcoming appointments section
   - Notification badge

**Expected Result:** ✅
- Page loads without errors
- Dashboard data displayed
- Sidebar navigation visible and functional

---

### Test Case 3.2: Appointment Filtering
**Objective:** Verify appointment filtering works

**Steps:**
1. On doctor dashboard, go to "Appointments" section
2. Click filter buttons: All, Today, Upcoming, Completed, Cancelled
3. Each filter should show corresponding appointments

**Expected Result:** ✅
- Appointments filtered correctly
- Correct count displayed for each filter
- Status badges show correct colors:
  - Pending: Blue (#3b82f6)
  - Confirmed: Green (#10b981)
  - Completed: Green (#10b981)
  - Cancelled: Red (#ef4444)

---

### Test Case 3.3: Notifications Section
**Objective:** Verify notifications display correctly

**Steps:**
1. Go to "Notifications" section
2. Should see list of doctor notifications
3. Unread notifications highlighted with different background
4. Click on notification to mark as read

**Expected Result:** ✅
- Notifications list displayed
- Unread count shown
- Marking as read updates styling immediately
- Timestamps displayed for each notification

---

### Test Case 3.4: Profile Section
**Objective:** Verify doctor profile displays and can be updated

**Steps:**
1. Go to "Profile" section
2. Should see doctor info: name, email, specialty, location, hospital, experience, fee, rating
3. (If update functionality added) Edit profile fields
4. Save changes

**Expected Result:** ✅
- Profile information displayed correctly
- All fields populated from database
- Updates persist after page refresh

---

### Test Case 3.5: Mobile Responsiveness
**Objective:** Verify dashboard is mobile-friendly

**Steps:**
1. Open dashboard in browser
2. Press F12 (DevTools)
3. Click device toggle (mobile view)
4. Select iPhone 12 / iPad / other device
5. Test navigation:
   - Sidebar collapses
   - Hamburger menu appears
   - Click menu items
   - Dashboard sections load correctly

**Expected Result:** ✅
- Sidebar collapses on mobile
- Hamburger menu functional
- All sections accessible
- Text readable at mobile size
- No horizontal scrolling

---

## PART 4: EXCEL DOCTOR UPLOAD

### Test Case 4.1: Create Sample Excel File
**File:** `doctors_upload.xlsx`

**Content:**
```
doctor_name | email | specialty | location | hospital | experience | fee | photo_url | password
Dr. Amit Patel | amit.patel@hospital.com | Cardiologist | Mumbai | Apollo Hospital | 10 years | 1000 | | AmitPass123
Dr. Priya Singh | priya.singh@hospital.com | Pediatrician | Delhi | Delhi Clinic | 8 years | 700 | | PriyaPass123
Dr. Rajesh Kumar | rajesh.kumar@hospital.com | Neurologist | Bangalore | Manipal Hospital | 12 years | 1200 | | RajeshPass123
```

---

### Test Case 4.2: Upload Excel File
**Objective:** Verify Excel doctor upload works

**Steps:**
1. Open admin dashboard
2. (If UI exists) Click "Upload Doctors" button
3. Or use API call:
   ```bash
   curl -X POST \
     -H "Authorization: Bearer <admin-token>" \
     -F "file=@doctors_upload.xlsx" \
     http://127.0.0.1:8000/admin/doctors/upload
   ```

**Expected Result:** ✅ Response:
```json
{
  "success": true,
  "inserted": 3,
  "skipped": 0,
  "errors": [],
  "total": 3
}
```

**Verification:**
- Check database: `SELECT COUNT(*) FROM doctors` → should increase by 3
- Check database: `SELECT COUNT(*) FROM doctor_accounts` → should increase by 3
- Verify passwords are hashed: `SELECT password_hash FROM doctor_accounts` → should be bcrypt hashes (not plain text)

---

### Test Case 4.3: Duplicate Email Handling
**Objective:** Verify duplicate emails are skipped

**Steps:**
1. Create second Excel file with duplicate email from Test 4.2
2. Upload the file

**Expected Result:** ✅ Response:
```json
{
  "success": true,
  "inserted": 0,
  "skipped": 3,
  "errors": [
    "Row 2: Email already exists (amit.patel@hospital.com)",
    ...
  ],
  "total": 3
}
```

---

### Test Case 4.4: Missing Required Fields
**Objective:** Verify missing fields are handled

**Steps:**
1. Create Excel with some missing doctor_name or email fields
2. Upload the file

**Expected Result:** ✅ Response includes errors for rows with missing fields:
```json
{
  "success": true,
  "inserted": 0,
  "skipped": 1,
  "errors": ["Row 2: Missing required fields"],
  "total": 1
}
```

---

## PART 5: DOCTOR NOTIFICATIONS TABLE

### Test Case 5.1: Notification Created on Appointment Booking
**Objective:** Verify notification created when appointment booked

**Steps:**
1. As patient, book appointment with a doctor
2. Check database:
   ```sql
   SELECT * FROM doctor_notifications WHERE doctor_id = '<doctor_id>' ORDER BY created_at DESC LIMIT 1;
   ```

**Expected Result:** ✅ New row in doctor_notifications:
- `title`: "New appointment booked: {patient_name}"
- `message`: "Appointment on {date} at {time} with {patient_name}"
- `is_read`: 0
- `created_at`: Current timestamp

---

### Test Case 5.2: Doctor Receives Notification
**Objective:** Verify doctor sees notification in dashboard

**Steps:**
1. Book appointment (from Test 5.1)
2. Login as doctor
3. Go to doctor dashboard
4. Click "Notifications" section

**Expected Result:** ✅
- Notification appears in list
- Notification shows: Title + Message + Timestamp
- Unread badge shows count

---

## PART 6: CANCELLATION NOTIFICATIONS

### Test Case 6.1: Appointment Cancellation
**Objective:** Verify appointment can be cancelled and emails sent

**Steps:**
1. Get appointment_id from database or previous test
2. Make API call:
   ```bash
   curl -X DELETE http://127.0.0.1:8000/appointments/<appointment_id>
   ```

**Expected Result:** ✅ Response:
```json
{
  "success": true,
  "appointment_id": "APT...",
  "message": "Appointment cancelled successfully"
}
```

**Verification:**
- Database: `SELECT status FROM appointments WHERE appointment_id = '<apt_id>'` → should be 'cancelled'
- Check email logs: `SELECT * FROM email_logs WHERE email_type = 'appointment_cancellation_patient'` → should have entry
- Check email logs: `SELECT * FROM email_logs WHERE email_type = 'appointment_cancellation_doctor'` → should have entry

---

### Test Case 6.2: Doctor Notification on Cancellation
**Objective:** Verify doctor notification created on cancellation

**Steps:**
1. Cancel appointment (from Test 6.1)
2. Check database:
   ```sql
   SELECT * FROM doctor_notifications WHERE doctor_id = '<doctor_id>' ORDER BY created_at DESC LIMIT 1;
   ```

**Expected Result:** ✅ New notification:
- `title`: "Appointment Cancelled: {patient_name}"
- `message`: "Patient appointment on {date} at {time} has been cancelled."
- `is_read`: 0

---

### Test Case 6.3: Email Failure Resilience
**Objective:** Verify cancellation succeeds even if email fails

**Steps:**
1. Temporarily remove Gmail credentials from .env:
   ```
   GMAIL_USER=
   GMAIL_APP_PASSWORD=
   ```
2. Restart backend
3. Cancel appointment

**Expected Result:** ✅
- Appointment status changes to 'cancelled'
- API returns success (even if email failed)
- Error logged but doesn't fail the cancellation
- Doctor notification still created

---

## PART 7: DASHBOARD APIs

### Test Case 7.1: GET /doctor/dashboard
**Objective:** Verify dashboard API returns correct data

**Steps:**
```bash
curl -X GET \
  -H "Authorization: Bearer <doctor-token>" \
  http://127.0.0.1:8000/doctor/dashboard
```

**Expected Result:** ✅ Response includes:
```json
{
  "doctor_id": "d001",
  "doctor_name": "Dr. Name",
  "email": "doctor@email.com",
  "today_appointments": [...],
  "upcoming_appointments": [...],
  "today_count": 2,
  "unread_notifications": 1,
  "timestamp": "2024-01-10T10:30:00"
}
```

---

### Test Case 7.2: GET /doctor/appointments?filter=today
**Objective:** Verify appointment filtering API

**Steps:**
```bash
curl -X GET \
  -H "Authorization: Bearer <doctor-token>" \
  "http://127.0.0.1:8000/doctor/appointments?filter=today"
```

**Expected Result:** ✅ Response:
```json
{
  "filter": "today",
  "count": 2,
  "appointments": [
    {
      "appointment_id": "APT123",
      "patient_name": "John Doe",
      "patient_phone": "9876543210",
      "appointment_date": "2024-01-10",
      "appointment_time": "10:00 AM",
      "symptoms": "Headache",
      "status": "pending"
    }
  ]
}
```

**Test other filters:** upcoming, completed, cancelled

---

### Test Case 7.3: GET /doctor/notifications
**Objective:** Verify notifications API

**Steps:**
```bash
curl -X GET \
  -H "Authorization: Bearer <doctor-token>" \
  http://127.0.0.1:8000/doctor/notifications
```

**Expected Result:** ✅ Response:
```json
{
  "doctor_id": "d001",
  "unread_count": 1,
  "total_count": 5,
  "notifications": [
    {
      "id": 1,
      "title": "New appointment booked: John Doe",
      "message": "Appointment on 2024-01-10 at 10:00 AM",
      "is_read": false,
      "created_at": "2024-01-10T09:00:00"
    }
  ]
}
```

---

### Test Case 7.4: POST /doctor/notifications/{id}/read
**Objective:** Verify notification can be marked as read

**Steps:**
```bash
curl -X POST \
  -H "Authorization: Bearer <doctor-token>" \
  http://127.0.0.1:8000/doctor/notifications/1/read
```

**Expected Result:** ✅ Response:
```json
{
  "success": true,
  "notification_id": 1,
  "message": "Notification marked as read"
}
```

**Verification:**
- Database: `SELECT is_read FROM doctor_notifications WHERE id = 1` → should be 1

---

### Test Case 7.5: GET /doctor/profile
**Objective:** Verify doctor profile API

**Steps:**
```bash
curl -X GET \
  -H "Authorization: Bearer <doctor-token>" \
  http://127.0.0.1:8000/doctor/profile
```

**Expected Result:** ✅ Response:
```json
{
  "doctor_id": "d001",
  "doctor_name": "Dr. Amit Kumar",
  "email": "amit@hospital.com",
  "specialty": "Cardiologist",
  "location": "Mumbai",
  "hospital": "Apollo Hospital",
  "experience": "10 years",
  "fee": 1000,
  "rating": 4.8,
  "photo_url": ""
}
```

---

### Test Case 7.6: PUT /doctor/profile
**Objective:** Verify doctor profile can be updated

**Steps:**
```bash
curl -X PUT \
  -H "Authorization: Bearer <doctor-token>" \
  -H "Content-Type: application/json" \
  -d '{"fee": 1200, "location": "Bangalore"}' \
  http://127.0.0.1:8000/doctor/profile
```

**Expected Result:** ✅ Response:
```json
{
  "success": true,
  "doctor_id": "d001",
  "message": "Profile updated successfully"
}
```

**Verification:**
- Make GET request to verify fee = 1200
- Database check: `SELECT fee, location FROM doctors WHERE id = 'd001'` → should show updates

---

## PART 8: REMOVED HARDCODED DOCTORS

### Test Case 8.1: Admin Dashboard Shows Database Doctors
**Objective:** Verify admin dashboard fetches doctors from database

**Steps:**
1. Login as admin
2. Go to admin.html (or admin dashboard)
3. Click "Doctors" page
4. View doctors table

**Expected Result:** ✅
- Doctors list populated from database (not hardcoded)
- Shows actual doctor count from database
- Can upload new doctors and see them appear immediately
- No hardcoded doctors list visible

---

### Test Case 8.2: Doctor Migration on Startup
**Objective:** Verify hardcoded doctors migrated to database on first run

**Steps:**
1. Delete database: `rm ha_healthcare.db`
2. Start backend: `python main.py`
3. Check logs for migration message
4. Query database:
   ```sql
   SELECT COUNT(*) FROM doctors;
   ```

**Expected Result:** ✅
- Logs show: "Migrating hardcoded DOCTORS to database..."
- Logs show: "Successfully migrated X doctors to database"
- Database has doctors (count > 0)
- Doctors table populated with hardcoded doctor data

---

### Test Case 8.3: Idempotent Migration
**Objective:** Verify migration can be run multiple times safely

**Steps:**
1. Restart backend (without deleting database)
2. Check logs

**Expected Result:** ✅
- Logs show: "Doctors table already populated (8 doctors)"
- No duplicate insertions
- Database count remains the same

---

### Test Case 8.4: Get Doctors API Uses Database
**Objective:** Verify /doctors endpoint uses database

**Steps:**
```bash
curl -X GET http://127.0.0.1:8000/doctors
```

**Expected Result:** ✅ Response:
```json
{
  "doctors": [
    {
      "id": "d001",
      "name": "Dr. Priya Sharma",
      "specialty": "General Physician",
      "location": "Hyderabad",
      "hospital": "HA! City Medical Center",
      "experience": "12 years",
      "rating": 4.9,
      "fee": 500,
      "photo_url": "",
      "image": "https://api.dicebear.com/...",
      "is_online": true,
      "available_slots": [...]
    }
  ],
  "count": 8
}
```

---

## INTEGRATION TEST: End-to-End Doctor Workflow

### Complete Workflow
1. **Admin uploads doctors** via Excel (Part 4)
2. **Doctors receive notification** when patient books appointment (Part 5)
3. **Doctor views dashboard** with appointments (Part 3)
4. **Patient cancels appointment** (Part 6)
5. **Doctor receives cancellation notification** (Part 6)
6. **Doctor marks notification as read** (Part 7)

### Steps:
1. Admin: Upload 3 doctors via Excel
2. Patient: Book appointment with Dr. #1
3. Check: Doctor notification created
4. Doctor: Login and view dashboard
5. Doctor: Go to Notifications section, see new booking notification
6. Patient: Cancel appointment
7. Check: Doctor notification for cancellation created
8. Doctor: Refresh dashboard, see cancellation notification
9. Doctor: Click notification to mark as read
10. Verify: Notification marked as read in database

### Expected Result: ✅ All steps complete without errors

---

## Database Verification Commands

```sql
-- Check doctors table
SELECT COUNT(*) FROM doctors;
SELECT * FROM doctors LIMIT 1;

-- Check doctor accounts
SELECT COUNT(*) FROM doctor_accounts;
SELECT doctor_id, email FROM doctor_accounts LIMIT 1;

-- Check doctor notifications
SELECT COUNT(*) FROM doctor_notifications;
SELECT * FROM doctor_notifications ORDER BY created_at DESC LIMIT 5;

-- Check email logs
SELECT * FROM email_logs WHERE email_type LIKE '%cancellation%' ORDER BY created_at DESC;

-- Check appointments
SELECT * FROM appointments WHERE status = 'cancelled' LIMIT 1;
```

---

## Error Scenarios to Test

### E1: Missing Authorization Header
```bash
curl -X GET http://127.0.0.1:8000/doctor/dashboard
```
**Expected:** 401 Unauthorized

### E2: Invalid Token
```bash
curl -X GET \
  -H "Authorization: Bearer invalid-token" \
  http://127.0.0.1:8000/doctor/dashboard
```
**Expected:** 401 Unauthorized

### E3: Non-Doctor Role
```bash
# Use patient token instead of doctor token
curl -X GET \
  -H "Authorization: Bearer <patient-token>" \
  http://127.0.0.1:8000/doctor/dashboard
```
**Expected:** 401 Invalid token

### E4: Doctor Not Found
```bash
curl -X GET \
  -H "Authorization: Bearer <doctor-token>" \
  http://127.0.0.1:8000/doctor/profile
```
**Expected:** 404 Doctor profile not found (if doctor doesn't exist)

---

## Performance Checklist

- [ ] Doctor dashboard loads in <2 seconds
- [ ] Appointment filtering responds in <500ms
- [ ] Excel upload of 100+ doctors completes in <10 seconds
- [ ] Notification creation is non-blocking (doesn't slow down appointment booking)
- [ ] Email sending is non-blocking (cancellation API returns immediately)

---

## Cleanup After Testing

```bash
# Backup test database
cp ha_healthcare.db ha_healthcare.db.test

# Restore original
cp ha_healthcare.db.backup ha_healthcare.db

# Or delete for fresh start
rm ha_healthcare.db
```

---

**Last Updated:** 2024
**Status:** Ready for QA Testing
