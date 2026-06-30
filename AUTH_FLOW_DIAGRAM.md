# Authentication Flow Diagrams

## 1. Patient Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      PATIENT LOGIN FLOW                          │
└─────────────────────────────────────────────────────────────────┘

  FRONTEND                          BACKEND                    DATABASE
  ────────                          ───────                    ────────
  
  [Login Page]
      │
      ├─ Click "Patient" tab
      │
      ├─ Enter: Name, Phone, Location
      │
      ├─ Click "Continue"
      │
      │─────────────────────────────────────────────────────────┐
      │ POST /auth/register                                       │
      │ { name, phone, location }                               │
      │─────────────────────────────────────────────────────────→ Check if exists
      │                                                           │
      │                                 ←─ Create new user or────┼── → users table
      │                                   return existing        │
      │
      │← Return { user_id, name }
      │
      ├─ Save to localStorage:
      │   • ha_logged_in = true
      │   • ha_name = name
      │   • ha_phone = phone
      │   • ha_location = location
      │
      └─→ Redirect to chat.html


ALTERNATIVE: Email OTP
  ┌────────────────────────────────────────────────────────┐
  │                                                          │
  ├─ Click "Use Email OTP"                                │
  │                                                          │
  ├─ Enter Email                                           │
  │                                                          │
  ├─ Click "Send OTP to Email"                            │
  │                                                          │
  │─────────────────────────────────────────────────────┐  │
  │ POST /auth/user/otp/request                          │  │
  │ { email, purpose: "verification" }                  │  │
  │─────────────────────────────────────────────────────→  │
  │                                  Generate OTP          │  │
  │                                  Send via Gmail         │  │
  │                                  Store in DB ──→ otp_store│
  │                                                          │  │
  │← Return { success: true }                              │  │
  │                                                          │
  ├─ Enter OTP code from email                            │
  │                                                          │
  ├─ Click "Verify OTP & Login"                           │
  │                                                          │
  │─────────────────────────────────────────────────────┐  │
  │ POST /auth/user/otp/verify                          │  │
  │ { email, otp_code }                                │  │
  │─────────────────────────────────────────────────────→  │
  │                                  Check OTP validity      │
  │                                  Create JWT token        │
  │                                  Store token ──→ auth_tokens│
  │                                                          │
  │← Return { token, user_id, role, expires_in }          │
  │                                                          │
  ├─ Save token to localStorage:                           │
  │   • ha_auth_token = token                             │
  │   • ha_user_id = user_id                             │
  │   • ha_user_role = "user"                            │
  │   • ha_token_expires = timestamp                     │
  │                                                          │
  └─→ Redirect to chat.html
```

---

## 2. Doctor Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCTOR LOGIN FLOW                            │
└─────────────────────────────────────────────────────────────────┘

  FRONTEND                          BACKEND                    DATABASE
  ────────                          ───────                    ────────

  [Login Page]
      │
      ├─ Click "Doctor" tab
      │
      ├─ Enter: Email, Password
      │
      ├─ Click "Login to Dashboard"
      │
      │─────────────────────────────────────────────────────────┐
      │ POST /auth/doctor/login                                  │
      │ { email: "priya@hospital.com", password: "SecurePass" } │
      │─────────────────────────────────────────────────────────→
      │                                  Query: SELECT from doctor_accounts
      │                                  WHERE email = ?         │
      │                                                          ├─→ doctor_accounts
      │                                                          │   table
      │                                  Result:                │
      │                                  ✓ Found email          │
      │                                  ✓ Verify password      │
      │                                  ✓ Account active       │
      │                                                          │
      │                                  Generate JWT with:     │
      │                                  • doctor_id            │
      │                                  • doctor_name          │
      │                                  • role: "doctor"       │
      │                                  • exp: timestamp       │
      │                                                          │
      │                                  Store JWT ──→ auth_tokens
      │                                                          │
      │← Return { token, user_id, role, expires_in }          │
      │
      ├─ Save token to localStorage:
      │   • ha_auth_token = token
      │   • ha_user_id = doctor_id
      │   • ha_user_role = "doctor"
      │   • ha_token_expires = timestamp
      │   • ha_email = email (for tracking)
      │
      └─→ Redirect to chat.html (doctor dashboard later)


ERROR CASES:
  
  Case 1: Email not found
  │─────────────────────────────────────────────────────────┐
  │ POST /auth/doctor/login                                  │
  │─────────────────────────────────────────────────────────→
  │                                  Query: SELECT from doctor_accounts
  │                                  WHERE email = ?         ├─→ NO MATCH
  │                                  
  │                                  Return 401:
  │                                  "Doctor account not found"
  │
  │← Error message displayed
  
  Case 2: Wrong password
  │─────────────────────────────────────────────────────────┐
  │ POST /auth/doctor/login                                  │
  │─────────────────────────────────────────────────────────→
  │                                  Query: SELECT from doctor_accounts
  │                                  WHERE email = ?         ├─→ FOUND
  │                                  
  │                                  Verify password:
  │                                  verify_password(input, hash)
  │                                  → False
  │                                  
  │                                  Return 401:
  │                                  "Incorrect password"
  │
  │← Error message displayed
```

---

## 3. Admin Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADMIN LOGIN FLOW                             │
└─────────────────────────────────────────────────────────────────┘

  FRONTEND                          BACKEND                    .env
  ────────                          ───────                    ────

  [Login Page]
      │
      ├─ Click "Admin" tab
      │
      ├─ Enter: Admin Password (any length, any characters)
      │   Example: admin2024, SecurePass123!, P@ss2024
      │
      ├─ Click "Access Dashboard"
      │
      │─────────────────────────────────────────────────────────┐
      │ POST /auth/admin/login                                   │
      │ { pin: "admin2024" }                                   │
      │─────────────────────────────────────────────────────────→
      │                                  Load .env
      │                                  ADMIN_PIN = "admin2024" ──
      │                                                          │
      │                                  Compare:
      │                                  pin == ADMIN_PIN?
      │                                                          │
      │                                  ✓ Match!
      │                                                          │
      │                                  Generate JWT with:
      │                                  • admin_id: "admin"
      │                                  • role: "admin"
      │                                  • exp: timestamp
      │                                                          │
      │                                  Store JWT ──→ auth_tokens
      │                                                          │
      │← Return { token, user_id, role, expires_in }          │
      │
      ├─ Save token to localStorage:
      │   • ha_auth_token = token
      │   • ha_user_id = "admin"
      │   • ha_user_role = "admin"
      │   • ha_token_expires = timestamp
      │
      └─→ Redirect to admin.html


ERROR CASE: Wrong PIN
  │─────────────────────────────────────────────────────────┐
  │ POST /auth/admin/login                                   │
  │ { pin: "wrongpin" }                                    │
  │─────────────────────────────────────────────────────────→
  │                                  Load .env
  │                                  ADMIN_PIN = "admin2024"
  │                                  
  │                                  Compare:
  │                                  "wrongpin" == "admin2024"?
  │                                  → False
  │                                  
  │                                  Return 401:
  │                                  "Invalid admin PIN"
  │
  │← Error message displayed
```

---

## 4. Admin: Create Doctor Account Flow

```
┌──────────────────────────────────────────────────────────────────┐
│              ADMIN: CREATE DOCTOR ACCOUNT FLOW                    │
└──────────────────────────────────────────────────────────────────┘

  ADMIN PANEL (Future)              BACKEND                    DATABASE
  ───────────────────               ───────                    ────────

  [Admin Dashboard]
      │
      ├─ Navigate to "Doctor Accounts" section
      │
      ├─ Click "Create New Account"
      │
      ├─ Fill form:
      │   • Doctor ID: d001
      │   • Name: Dr. Priya Sharma
      │   • Email: priya@hospital.com
      │   • Password: SecurePass123
      │
      ├─ Click "Create"
      │
      │──────────────────────────────────────────────────────────┐
      │ POST /admin/doctors/accounts/create                      │
      │ {                                                        │
      │   "doctor_id": "d001",                                  │
      │   "doctor_name": "Dr. Priya Sharma",                   │
      │   "email": "priya@hospital.com",                       │
      │   "password": "SecurePass123"                          │
      │ }                                                        │
      │──────────────────────────────────────────────────────────→
      │                              
      │                              Check if email exists
      │                              └─→ Query doctor_accounts ├─→ NOT FOUND ✓
      │                              
      │                              Hash password:
      │                              hash_password("SecurePass123")
      │                              → "$2b$12$..."
      │                              
      │                              INSERT INTO doctor_accounts:
      │                              • doctor_id: d001
      │                              • doctor_name: Dr. Priya Sharma
      │                              • email: priya@hospital.com
      │                              • password_hash: $2b$12$...
      │                              • is_active: 1
      │                              • verified: 0
      │                              • created_at: 2026-06-13T...
      │                              ├──────────────────────────→ doctor_accounts
      │                              
      │← Return {
      │   "success": true,
      │   "message": "Account created successfully",
      │   "doctor_id": "d001",
      │   "email": "priya@hospital.com"
      │ }
      │
      ├─ Show success message
      │
      └─ Refresh doctor list


API ENDPOINT USAGE:
  
  curl -X POST http://127.0.0.1:8000/admin/doctors/accounts/create \
    -H "Content-Type: application/json" \
    -d '{
      "doctor_id": "d001",
      "doctor_name": "Dr. Priya Sharma",
      "email": "priya@hospital.com",
      "password": "SecurePass123"
    }'
```

---

## 5. Admin: List Doctor Accounts Flow

```
┌──────────────────────────────────────────────────────────────────┐
│              ADMIN: LIST DOCTOR ACCOUNTS FLOW                     │
└──────────────────────────────────────────────────────────────────┘

  ADMIN PANEL (Future)              BACKEND                    DATABASE
  ───────────────────               ───────                    ────────

  [Admin Dashboard]
      │
      ├─ Navigate to "Doctor Accounts"
      │
      ├─ Page loads
      │
      │──────────────────────────────────────────────────────────┐
      │ GET /admin/doctors/accounts                              │
      │──────────────────────────────────────────────────────────→
      │                              
      │                              Query:
      │                              SELECT id, doctor_id, doctor_name,
      │                                     email, is_active, verified, created_at
      │                              FROM doctor_accounts
      │                              ORDER BY created_at DESC
      │                              ├──────────────────────────→ doctor_accounts
      │                              
      │                              Result:
      │                              [
      │                                {
      │                                  "id": 1,
      │                                  "doctor_id": "d001",
      │                                  "doctor_name": "Dr. Priya Sharma",
      │                                  "email": "priya@hospital.com",
      │                                  "is_active": true,
      │                                  "verified": false,
      │                                  "created_at": "2026-06-13T10:30:00"
      │                                },
      │                                ...
      │                              ]
      │
      │← Return { "success": true, "accounts": [...], "count": 1 }
      │
      ├─ Display table:
      │   ┌────────────────────────────────────────────────────┐
      │   │ Doctor Accounts (1 total)                          │
      │   ├────────────────────────────────────────────────────┤
      │   │ Name           │ Email            │ Active │ Verify │
      │   ├────────────────────────────────────────────────────┤
      │   │ Dr. Priya...   │ priya@hospi...   │ Yes    │ No     │
      │   │ [Edit] [Reset] [Deactivate]                        │
      │   └────────────────────────────────────────────────────┘
      │
      └─ Ready for other actions
```

---

## 6. JWT Token Structure & Usage

```
┌──────────────────────────────────────────────────────────────────┐
│                      JWT TOKEN STRUCTURE                          │
└──────────────────────────────────────────────────────────────────┘

ENCODED (what's stored):
  eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
  eyJzdWIiOiJkMDAxIiwicm9sZSI6ImRvY3RvciIsImRvY3Rvcl9pZCI6ImQwMDEiLCJkb2N0b3JfbmFtZSI6IkRyLiBQcml5YSBTaGFybWEiLCJleHAiOjE3MTgzNjgwMDB9.
  kE5aR3kL8pQxV2mN4qW9...


DECODED:

  Header:
  {
    "typ": "JWT",
    "alg": "HS256"
  }

  Payload (DOCTOR):
  {
    "sub": "d001",              ← doctor_id (required)
    "role": "doctor",           ← role (required)
    "doctor_id": "d001",        ← for easy access
    "doctor_name": "Dr. Priya Sharma",  ← for display
    "exp": 1718368000           ← expiration timestamp
  }

  Payload (ADMIN):
  {
    "sub": "admin",
    "role": "admin",
    "exp": 1718368000
  }

  Payload (USER/PATIENT):
  {
    "sub": "user123",
    "role": "user",
    "exp": 1718368000
  }

  Signature (verified with JWT_SECRET):
  HMACSHA256(
    base64UrlEncode(header) + "." +
    base64UrlEncode(payload),
    JWT_SECRET
  )


USAGE IN FRONTEND:

  // Store token
  localStorage.setItem('ha_auth_token', token);
  
  // Retrieve token
  const token = localStorage.getItem('ha_auth_token');
  
  // Decode token (no library needed)
  const parts = token.split('.');
  const payload = JSON.parse(atob(parts[1]));
  
  // Access doctor info
  console.log(payload.doctor_id);     // "d001"
  console.log(payload.doctor_name);   // "Dr. Priya Sharma"
  
  // Check if expired
  const now = Math.floor(Date.now() / 1000);
  if (payload.exp < now) {
    console.log("Token expired");
  }


USAGE IN BACKEND:

  // Include in API requests
  fetch('/api/appointments', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  // Backend verifies
  verify_token(token) → TokenPayload
  
  // Backend uses doctor metadata
  token_payload.doctor_id
  token_payload.doctor_name
  token_payload.role
```

---

## 7. Error Handling Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                            │
└──────────────────────────────────────────────────────────────────┘

DOCTOR LOGIN ERRORS:

┌─────────────────────────┐
│ Try to Login            │
└────────────┬────────────┘
             │
             ├─ Email empty?
             │  └─→ "Please enter your email."
             │
             ├─ Password empty?
             │  └─→ "Please enter your password."
             │
             └─ Call API: POST /auth/doctor/login
                │
                ├─ API Response: 401
                │  │
                │  ├─ error detail: "Doctor account not found"
                │  │  └─→ Display: "Doctor account not found"
                │  │       (Email doesn't exist in system)
                │  │
                │  ├─ error detail: "Incorrect password"
                │  │  └─→ Display: "Incorrect password"
                │  │       (Email exists but password wrong)
                │  │
                │  └─ Other 5xx error
                │     └─→ Display: "Network error. Please try again."
                │
                └─ API Response: 200 OK
                   └─→ Redirect to dashboard


ADMIN PIN ERRORS:

┌─────────────────────────┐
│ Try to Login            │
└────────────┬────────────┘
             │
             ├─ PIN empty?
             │  └─→ "Please enter your admin password."
             │
             └─ Call API: POST /auth/admin/login
                │
                ├─ API Response: 401
                │  │
                │  └─ error detail: "Invalid admin PIN"
                │     └─→ Display: "Invalid password."
                │
                └─ API Response: 200 OK
                   └─→ Redirect to admin.html


GOOGLE BUTTON ERRORS:

  Current state: Placeholder
  Message: "Google OAuth will be enabled after configuring 
            Google Cloud credentials."
  
  Next phase: Full integration with Google credentials


EMAIL OTP ERRORS:

┌──────────────────────┐
│ Request OTP          │
└─────────┬────────────┘
          │
          ├─ Email empty?
          │  └─→ "Please enter your email address."
          │
          ├─ Email invalid format?
          │  └─→ "Invalid email format."
          │
          └─ Call API: POST /auth/user/otp/request
             │
             ├─ Gmail not configured
             │  └─→ "Failed to send OTP."
             │
             ├─ Email error (invalid etc)
             │  └─→ "Failed to send OTP."
             │
             └─ Success
                └─→ "OTP sent to email@example.com. Check your email."
                    (Show OTP input field)

┌──────────────────────┐
│ Verify OTP           │
└─────────┬────────────┘
          │
          ├─ OTP empty?
          │  └─→ "Please enter a valid 6-digit OTP."
          │
          ├─ OTP wrong length?
          │  └─→ "Please enter a valid 6-digit OTP."
          │
          └─ Call API: POST /auth/user/otp/verify
             │
             ├─ OTP expired (>10 minutes)
             │  └─→ "Invalid or expired OTP."
             │
             ├─ OTP doesn't match
             │  └─→ "Invalid OTP. Please try again."
             │
             └─ OTP valid
                └─→ Create JWT + Redirect to chat.html
```

---

## Summary Flowchart

```
┌───────────────────────────────────────────────────────────────┐
│                    LOGIN PAGE                                 │
└───────────────────────────────────────────────────────────────┘
                          │
                ┌─────────┼─────────┐
                │         │         │
            ┌───▼───┐ ┌───▼───┐ ┌──▼────┐
            │Patient│ │Doctor │ │ Admin │
            └───┬───┘ └───┬───┘ └──┬───┘
                │         │        │
        ┌───────┼───┐     │    ┌───▼─────┐
        │            │     │    │         │
     ┌──▼──┐ ┌─────▼─┐   │    │ Enter   │
     │Name │ │Email  │   │    │ Admin   │
     │Phone│ │Passwrd│   │    │ PIN     │
     │Loc. │ │       │   │    └────┬────┘
     └──┬──┘ └─────┬─┘   │         │
        │          │     │         │
        │     ┌────▼──┐  │    ┌────▼────┐
        │     │Or OTP │  │    │Verify   │
        │     └────┬──┘  │    │ADMIN_PIN│
        │          │     │    └────┬────┘
        │    ┌─────▼──┐  │         │
        │    │Or OAuth│  │         │
        │    └────┬───┘  │    Success?
        │         │      │    ├─ Yes → admin.html
        │         │      │    └─ No → Error msg
        │         │      │
        │    Save │      │  Check
        │    JWT  │      │  doctor_accounts
        │    to   │      │  ├─ Email found?
        │    LS   │      │  │ ├─ Yes: Check password
        │         │      │  │ │ ├─ Match?
        │         │      │  │ │ │ ├─ Yes → Save JWT
        │         │      │  │ │ │ └─ No → "Incorrect password"
        │         │      │  │ │ └─ No match → Error
        │         │      │  │ └─ No: "Doctor account not found"
        │         │      │  
        │    ┌────▼──┐   │
        │    │All    │   │
        │    │tabs   │   │
        │    │redirect
        │    │to     │   │
        │    │chat.  │   │
        │    │html   │   │
        │    └────┬──┘   │
        │         │      │
        └────┬────┴──┬───┘
             │       │
          ┌──▼───┬───▼──┐
          │      │      │
      [Chat] [Admin] [Dashboard]
       Page   Page   (Future)
```

---

*Flow diagrams complete. All authentication paths documented.*
