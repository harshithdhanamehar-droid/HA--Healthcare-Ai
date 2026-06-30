# Authentication System - Testing Guide

## Issues Fixed

### ✅ Issue 1: Google Login Button UI
**Status**: FIXED
- **Changed from**: Blue circular emoji icon (🔵)
- **Changed to**: Official Google "G" logo using SVG
- **Files modified**: 
  - `frontend/index.html` - SVG icon included
  - `frontend/css/login.css` - Google button styling
- **Details**:
  - SVG displays official Google colors (#4285F4, #34A853, #FBBC05, #EA4335)
  - Button text: "Continue with Google"
  - Responsive design maintained
  - Works with HA! dark theme

### ✅ Issue 2: Email OTP
**Status**: NO CHANGES NEEDED
- Already working correctly
- OTP being sent and verified successfully
- No modifications required

### ✅ Issue 3: Admin Login PIN
**Status**: FIXED
- **Before**: Accepted only 4 digits
- **After**: Accepts any characters (letters, numbers, special chars)
- **Files modified**: 
  - `frontend/index.html` - Removed `inputmode="numeric"` and `maxlength="4"`
  - `frontend/js/login.js` - No validation restrictions on PIN length
- **Details**:
  - Reads ADMIN_PIN from `.env` (default: `admin2024`)
  - Example passwords now work: `admin2024`, `SecurePass123!`, etc.
  - Backend validates against .env value

### ✅ Issue 4: Doctor Login Flow
**Status**: FIXED WITH NEW ADMIN ENDPOINTS
- **Before**: Always showed "Invalid email or password"
- **After**: Shows specific error messages
  - "Doctor account not found" - Email not in system
  - "Incorrect password" - Email exists but password wrong
- **Files modified**:
  - `frontend/js/login.js` - Better error display
  - `backend/main.py` - Added 6 doctor account management endpoints
  - `backend/auth.py` - Already had verification logic
- **New Admin Endpoints**:
  1. POST `/admin/doctors/accounts/create` - Create doctor account
  2. GET `/admin/doctors/accounts` - List all doctor accounts
  3. GET `/admin/doctors/accounts/{doctor_id}` - Get specific account
  4. PATCH `/admin/doctors/accounts/{doctor_id}` - Update account
  5. POST `/admin/doctors/accounts/{doctor_id}/reset-password` - Reset password
  6. DELETE `/admin/doctors/accounts/{doctor_id}` - Deactivate account

### ✅ Issue 5: Doctor Dashboard Preparation
**Status**: FIXED
- **JWT Token now includes**:
  - `doctor_id` - From doctor_accounts table
  - `doctor_name` - From doctor_accounts table
  - `role: "doctor"` - User type
  - `exp` - Expiration timestamp
- **Files modified**:
  - `backend/auth.py` - Already configured (no changes)
  - `backend/main.py` - Doctor endpoints return full metadata
- **Details**:
  - Token available for: My Appointments, Patient History, Doctor Notes, Online Consultation
  - Stored in localStorage as `ha_auth_token`
  - Can be decoded by frontend to access doctor metadata

## Manual Testing Steps

### Test 1: Admin Login with PIN ✅
1. Open `http://localhost:8000/frontend/index.html` (or deployed URL)
2. Click "Admin" tab
3. Enter PIN: `admin2024`
4. Click "Access Dashboard →"
5. **Expected**: Redirect to `admin.html`
6. **Error Message Test**:
   - Try PIN: `wrongpin`
   - Expected error: "Invalid admin PIN"

### Test 2: Doctor Account Creation (API) ✅
Using curl or Postman:

```bash
curl -X POST http://127.0.0.1:8000/admin/doctors/accounts/create \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "d001",
    "doctor_name": "Dr. Priya Sharma",
    "email": "priya@hospital.com",
    "password": "SecurePass123"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Account created successfully",
  "doctor_id": "d001",
  "email": "priya@hospital.com"
}
```

### Test 3: Doctor Login - Success Case ✅
1. Open login page
2. Click "Doctor" tab
3. Enter email: `priya@hospital.com`
4. Enter password: `SecurePass123`
5. Click "Login to Dashboard →"
6. **Expected**: Redirect to `chat.html` with JWT token saved

### Test 4: Doctor Login - Error Cases ✅
**Case A: Non-existent Doctor**
1. Click "Doctor" tab
2. Enter email: `nonexistent@hospital.com`
3. Enter password: `AnyPassword123`
4. **Expected Error**: "Doctor account not found"

**Case B: Wrong Password**
1. Click "Doctor" tab
2. Enter email: `priya@hospital.com` (valid account)
3. Enter password: `WrongPassword123`
4. **Expected Error**: "Incorrect password"

### Test 5: Google Button Display ✅
1. Open login page
2. Click "Patient" tab
3. Look for "Continue with Google" button
4. **Expected**: 
   - Official Google "G" logo (colorful SVG)
   - Button text: "Continue with Google"
   - Professional appearance
   - Responsive on mobile

### Test 6: Email OTP ✅
1. Click "Patient" tab
2. Click "Use Email OTP" button
3. Enter email: `test@example.com`
4. Click "Send OTP to Email"
5. **Expected**: OTP email sent message
6. Enter OTP from email
7. Click "Verify OTP & Login"
8. **Expected**: Redirect to chat.html

### Test 7: Admin Account Management (API) ✅

**List all doctor accounts**:
```bash
curl -X GET http://127.0.0.1:8000/admin/doctors/accounts
```

**Get specific account**:
```bash
curl -X GET http://127.0.0.1:8000/admin/doctors/accounts/d001
```

**Update doctor account**:
```bash
curl -X PATCH http://127.0.0.1:8000/admin/doctors/accounts/d001 \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_name": "Dr. Priya Sharma (Updated)",
    "is_active": true
  }'
```

**Reset doctor password**:
```bash
curl -X POST http://127.0.0.1:8000/admin/doctors/accounts/d001/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewPassword123"
  }'
```

**Deactivate doctor account**:
```bash
curl -X DELETE http://127.0.0.1:8000/admin/doctors/accounts/d001
```

## Database Verification

### Check Doctor Accounts Table
```sql
SELECT * FROM doctor_accounts;
```

Expected columns:
- id (primary key)
- doctor_id (unique)
- doctor_name
- email (unique)
- password_hash (bcrypt)
- is_active (1 or 0)
- verified (1 or 0)
- created_at
- updated_at

## JWT Token Verification

### Decode Token (in browser console):
```javascript
// After doctor login, token is in localStorage
const token = localStorage.getItem('ha_auth_token');
const parts = token.split('.');
const payload = JSON.parse(atob(parts[1]));
console.log(payload);
```

Expected structure:
```json
{
  "sub": "d001",
  "role": "doctor",
  "doctor_id": "d001",
  "doctor_name": "Dr. Priya Sharma",
  "exp": 1718368000
}
```

## Configuration Files

### .env Settings
```
ADMIN_PIN=admin2024          # Read by backend
JWT_SECRET=your-secret       # JWT signing
JWT_EXPIRE_MINUTES=1440      # Token expiration
GMAIL_USER=***               # Email OTP
GMAIL_APP_PASSWORD=***       # Email OTP
```

### Database Schema (doctor_accounts)
```sql
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
);
```

## Troubleshooting

### Admin PIN Not Working
1. Check `.env` file has `ADMIN_PIN=admin2024`
2. Verify no trailing spaces in .env
3. Restart backend server
4. Try hardcoding PIN in auth.py temporarily

### Doctor Login Shows "Invalid Credentials"
1. Verify doctor account exists: `SELECT * FROM doctor_accounts WHERE email = 'email@test.com'`
2. Check email is spelled correctly (case-sensitive)
3. Verify password was set correctly during account creation
4. Try password reset: `/admin/doctors/accounts/{doctor_id}/reset-password`

### Google Button Not Displaying
1. Check SVG code in index.html (should have `<svg viewBox="0 0 24 24"...>`)
2. Check CSS has `.google-icon { display: inline-block; }`
3. Verify browser supports SVG (all modern browsers do)

### OTP Not Sending
1. Check Gmail credentials in `.env`: `GMAIL_USER` and `GMAIL_APP_PASSWORD`
2. Verify Gmail app password is correct (not regular password)
3. Enable "Less secure apps" or use app-specific password
4. Check email address format

### JWT Token Not Saving
1. Check localStorage permissions in browser
2. Verify browser allows localStorage
3. Check for console errors in browser developer tools
4. Clear localStorage and try again

## Summary Checklist

- [x] Admin PIN field accepts any characters
- [x] Admin PIN reads from .env ADMIN_PIN
- [x] Google button shows official SVG icon
- [x] Doctor login shows specific error messages
- [x] Doctor account creation API endpoint works
- [x] Doctor account management endpoints implemented
- [x] JWT token includes doctor_id and doctor_name
- [x] Email OTP working correctly
- [x] Tab switching working correctly
- [x] All forms visible when tabs are clicked

## Next Phase

1. **Admin Panel UI**: Create interface for doctor account management
2. **Doctor Dashboard**: Implement doctor-specific pages
3. **Google OAuth**: Full integration with Google credentials
4. **Production Security**: Add rate limiting, auth headers, password requirements
