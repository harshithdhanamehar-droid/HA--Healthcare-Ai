# Authentication System - Quick Start Guide

## Setup & Testing

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment

Edit `backend/.env`:

```env
# JWT
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Admin PIN
ADMIN_PIN=admin2024

# Gmail (for OTP emails)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
```

### 3. Start Backend

```bash
cd backend
python main.py
```

Server runs at: `http://localhost:8000`

### 4. Access Login Portal

Open in browser: `http://localhost:3000/auth-login.html`

(Or use your frontend server URL)

## Testing Authentication Flows

### Patient/User - Email OTP

1. **Click "Patient" tab**
2. **Select "Email OTP" method**
3. **Enter email**: `test@example.com`
4. **Click "Send OTP"**
   - Check email (or server logs) for OTP code
   - Code looks like: `123456`
5. **Enter OTP**: Paste the 6-digit code
6. **Click "Verify OTP & Login"**
7. **Success** → Redirects to `/index.html`

### Patient/User - Google OAuth

1. **Click "Patient" tab**
2. **Select "Google" method**
3. **Click "Login with Google"**
4. **Sign in with Google account**
5. **Success** → Redirects to `/index.html`

*Note: Requires GOOGLE_CLIENT_ID configuration*

### Doctor - Email & Password

#### First-time setup:

Register doctor account via API:

```bash
curl -X POST http://localhost:8000/auth/doctor/register \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "d001",
    "email": "doctor@hospital.com",
    "password": "secure_password_123"
  }'
```

#### Then login:

1. **Click "Doctor" tab**
2. **Select "Email & Password" method**
3. **Enter email**: `doctor@hospital.com`
4. **Enter password**: `secure_password_123`
5. **Click "Login to Dashboard"**
6. **Success** → Redirects to `/doctor-dashboard.html`

### Doctor - Email OTP

1. **Click "Doctor" tab**
2. **Select "Email OTP" method**
3. **Enter email**: `doctor@hospital.com`
4. **Click "Send OTP"**
5. **Enter OTP code** from email
6. **Click "Verify OTP & Login"**
7. **Success** → Redirects to `/doctor-dashboard.html`

### Admin - PIN Login

1. **Click "Admin" tab**
2. **Enter PIN**: `admin2024` (from .env)
3. **Click "Access Dashboard"**
4. **Success** → Redirects to `/admin.html`

## API Testing with cURL

### Test User OTP Request

```bash
curl -X POST http://localhost:8000/auth/user/otp/request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "purpose": "verification"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent to user@example.com",
  "email": "user@example.com"
}
```

### Test User OTP Verification

```bash
curl -X POST http://localhost:8000/auth/user/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp_code": "123456"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "abc12345",
  "role": "user",
  "expires_in": 86400
}
```

### Test Doctor Login

```bash
curl -X POST http://localhost:8000/auth/doctor/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "secure_password_123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "d001",
  "role": "doctor",
  "expires_in": 86400
}
```

### Test Admin Login

```bash
curl -X POST http://localhost:8000/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "pin": "admin2024"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "admin",
  "role": "admin",
  "expires_in": 86400
}
```

### Test Token Verification

```bash
curl -X GET http://localhost:8000/auth/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "valid": true,
  "user_id": "abc12345",
  "role": "user",
  "expires_at": 1718347200
}
```

### Test Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Postman Collection

Import this into Postman for easy testing:

```json
{
  "info": {
    "name": "HA! Healthcare Auth API",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "User OTP Request",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/user/otp/request",
        "header": {"Content-Type": "application/json"},
        "body": {"email": "test@example.com", "purpose": "verification"}
      }
    },
    {
      "name": "User OTP Verify",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/user/otp/verify",
        "header": {"Content-Type": "application/json"},
        "body": {"email": "test@example.com", "otp_code": "123456"}
      }
    },
    {
      "name": "Doctor Login",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/doctor/login",
        "header": {"Content-Type": "application/json"},
        "body": {"email": "doctor@hospital.com", "password": "password123"}
      }
    },
    {
      "name": "Admin Login",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/admin/login",
        "header": {"Content-Type": "application/json"},
        "body": {"pin": "admin2024"}
      }
    },
    {
      "name": "Verify Token",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/auth/verify",
        "header": {"Authorization": "Bearer {{token}}"}
      }
    }
  ]
}
```

Set Postman variables:
- `base_url`: `http://localhost:8000`
- `token`: Your JWT token from login response

## Checking Logs

### Backend Logs

```bash
# View logs
tail -f backend/ha_healthcare.log

# Check for auth events
grep "logged in\|OTP\|verified" backend/ha_healthcare.log
```

### Database Queries

Check what was created:

```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('ha_healthcare.db')
cursor = conn.cursor()

# Check users
cursor.execute('SELECT * FROM users LIMIT 5')
print('USERS:', cursor.fetchall())

# Check doctor accounts
cursor.execute('SELECT * FROM doctor_accounts LIMIT 5')
print('DOCTORS:', cursor.fetchall())

# Check OTPs
cursor.execute('SELECT email, purpose, expires_at FROM otp_store LIMIT 5')
print('OTPS:', cursor.fetchall())

# Check tokens
cursor.execute('SELECT user_id, user_role FROM auth_tokens LIMIT 5')
print('TOKENS:', cursor.fetchall())

conn.close()
"
```

## Troubleshooting

### OTP Email Not Received

1. Check Gmail is configured
   ```bash
   echo $GMAIL_USER
   echo $GMAIL_APP_PASSWORD
   ```

2. Check logs
   ```bash
   grep "OTP email sent\|Failed to send OTP" backend/ha_healthcare.log
   ```

3. Try sending manual email
   ```bash
   python -c "from auth import send_otp_email; send_otp_email('test@gmail.com', '123456', 'Test')"
   ```

### Token Verification Failing

1. Check token format
   ```javascript
   // In browser console
   console.log(localStorage.getItem('ha_auth_token'));
   ```

2. Decode token at jwt.io
   - Check exp timestamp
   - Check role and user_id

3. Verify in backend
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:8000/auth/verify
   ```

### Doctor Login Failing

1. Verify doctor account exists
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('ha_healthcare.db')
   cursor = conn.cursor()
   cursor.execute(\"SELECT * FROM doctor_accounts WHERE email='doctor@hospital.com'\")
   print(cursor.fetchone())
   "
   ```

2. Test password hash
   ```bash
   python -c "
   from auth import verify_password
   import sqlite3
   conn = sqlite3.connect('ha_healthcare.db')
   cursor = conn.cursor()
   cursor.execute(\"SELECT password_hash FROM doctor_accounts WHERE email='doctor@hospital.com'\")
   row = cursor.fetchone()
   if row:
       print('Valid:', verify_password('password123', row[0]))
   "
   ```

### Google OAuth Not Working

1. Verify credentials
   ```bash
   echo $GOOGLE_CLIENT_ID
   echo $GOOGLE_CLIENT_SECRET
   ```

2. Check redirect URI in Google Console
   - Should match your frontend URL

3. Test token verification
   ```bash
   python -c "from auth import verify_google_token; print(verify_google_token('test_token'))"
   ```

## Next Steps

1. **Update Protected Routes**: Add `@require_auth` decorator to endpoints
2. **Implement Refresh Tokens**: Allow extending sessions
3. **Enable Rate Limiting**: Prevent brute force attacks
4. **Add Email Verification**: Send confirmation emails
5. **Create Password Reset**: Implement forgot password flow
6. **Add 2FA**: Multi-factor authentication for doctors

## Security Reminders

- ⚠️ Never commit `.env` to Git
- ⚠️ Use strong JWT_SECRET in production
- ⚠️ Rotate admin PIN regularly  
- ⚠️ Use HTTPS in production
- ⚠️ Implement rate limiting on auth endpoints
- ⚠️ Audit log all authentication events
- ⚠️ Implement account lockout after failed attempts

---

**Need help?** Check `AUTHENTICATION_SYSTEM.md` for detailed documentation.
