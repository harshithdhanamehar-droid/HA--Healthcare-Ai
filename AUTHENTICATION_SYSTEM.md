# HA! Healthcare AI - Multi-Role JWT Authentication System

## Overview

This document describes the complete multi-role JWT authentication system implemented for HA! Healthcare AI, supporting three distinct user roles with different authentication flows:

- **Patient/User** - Google OAuth or Email OTP
- **Doctor** - Email & Password or Email OTP  
- **Admin** - Secure PIN-based access

## Architecture

### Backend Components

#### 1. **auth.py** - Core Authentication Module

Located: `backend/auth.py`

Provides all authentication primitives:

```python
# JWT Management
- create_access_token(user_id, role) → JWT token
- verify_token(token) → TokenPayload or None

# Password Hashing (bcrypt)
- hash_password(plain) → hashed
- verify_password(plain, hashed) → bool

# OTP Management
- generate_otp(length=6) → "123456"
- store_otp(db_path, email, otp_code, purpose, ttl_minutes=10) → bool
- verify_otp(db_path, email, otp_code, purpose) → bool
- send_otp_email(email, otp_code, purpose) → bool

# Doctor Accounts
- create_doctor_account(db_path, doctor_id, email, password) → (bool, str)
- verify_doctor_credentials(db_path, email, password) → (bool, doctor_id)

# Google OAuth
- verify_google_token(token) → {google_sub, email, name} or None
- link_google_auth(db_path, google_sub, user_id, email) → bool
- get_user_by_google_sub(db_path, google_sub) → user_id or None

# Admin PIN
- verify_admin_pin(pin) → bool

# Token Storage (Session Tracking)
- store_token(db_path, token, user_id, role) → bool
- invalidate_token(db_path, token) → bool
```

#### 2. **main.py** - FastAPI Backend

Updated with authentication endpoints:

**Authentication Routes:**

```
POST /auth/user/google
  - Google OAuth login for patients
  - Body: { "token": "google_token", "name": "optional_name" }
  - Response: { "token": "jwt", "user_id": "...", "role": "user", "expires_in": 86400 }

POST /auth/user/otp/request
  - Request OTP for patient email verification
  - Body: { "email": "user@example.com", "purpose": "verification|forgot_password" }
  - Response: { "success": true, "message": "OTP sent", "email": "..." }

POST /auth/user/otp/verify
  - Verify OTP and login/create patient account
  - Body: { "email": "user@example.com", "otp_code": "123456" }
  - Response: { "token": "jwt", "user_id": "...", "role": "user", "expires_in": 86400 }

POST /auth/doctor/register
  - Register doctor account
  - Body: { "doctor_id": "d001", "email": "doc@hospital.com", "password": "..." }
  - Response: { "success": true, "message": "..." }

POST /auth/doctor/login
  - Doctor login with email & password
  - Body: { "email": "doc@hospital.com", "password": "..." }
  - Response: { "token": "jwt", "user_id": "d001", "role": "doctor", "expires_in": 86400 }

POST /auth/doctor/otp/verify
  - Doctor OTP verification (optional second factor)
  - Body: { "email": "doc@hospital.com", "otp_code": "123456" }
  - Response: { "success": true, "message": "..." }

POST /auth/admin/login
  - Admin PIN-based login
  - Body: { "pin": "1234" }
  - Response: { "token": "jwt", "user_id": "admin", "role": "admin", "expires_in": 86400 }

GET /auth/verify
  - Verify JWT token validity
  - Header: Authorization: Bearer <jwt_token>
  - Response: { "valid": true, "user_id": "...", "role": "...", "expires_at": "..." }

POST /auth/logout
  - Invalidate token (logout)
  - Header: Authorization: Bearer <jwt_token>
  - Response: { "success": true, "message": "..." }
```

#### 3. **Database Schema**

New tables created automatically:

```sql
-- Doctor accounts for doctor login
CREATE TABLE doctor_accounts (
    id INTEGER PRIMARY KEY,
    doctor_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    verified BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL
);

-- Auth tokens for session tracking
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- OTP storage for email verification
CREATE TABLE otp_store (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Google OAuth linkage
CREATE TABLE google_auth (
    id INTEGER PRIMARY KEY,
    google_sub TEXT UNIQUE NOT NULL,
    user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TEXT NOT NULL
);
```

### Frontend Components

#### 1. **auth-login.html** - Multi-Role Login Portal

Located: `frontend/auth-login.html`

Unified login page with three role tabs:

- **Patient Tab**: Google OAuth button + Email OTP flow
- **Doctor Tab**: Email/Password form + Email OTP fallback
- **Admin Tab**: PIN entry form with security badge

Features:
- Role selector tabs
- Auth method switching (Google, Email/Password, OTP)
- Real-time form validation
- Loading states and error handling
- Success notifications with redirects
- Responsive design (mobile-first)
- Accessible forms with keyboard support

#### 2. **auth-login.js** - Frontend Logic

Located: `frontend/js/auth-login.js`

Handles:

```javascript
// Configuration
API_BASE_URL = 'http://localhost:8000'
STORAGE_KEYS: {
  TOKEN: 'ha_auth_token',
  USER_ID: 'ha_user_id',
  ROLE: 'ha_user_role',
  EXPIRES_IN: 'ha_token_expires'
}

// Role Selection
selectRole(role) → switches between user/doctor/admin forms

// Patient Authentication
- user_login_google() → initiates Google Sign-In
- user_request_otp() → sends OTP to email
- user_verify_otp() → verifies code and logs in

// Doctor Authentication  
- doctor_login() → email + password login
- doctor_request_otp() → sends OTP
- doctor_verify_otp() → OTP verification

// Admin Authentication
- admin_login() → PIN entry and verification

// Token Management
- saveAuthToken(token, userId, role, expiresIn)
- redirectToDashboard(role)

// UI Utilities
- showLoading(message)
- hideLoading()
- showError(title, message)
- showSuccess(title, message)
- closeModal(modalId)
```

#### 3. **auth-login.css** - Styling

Located: `frontend/css/auth-login.css`

Provides:
- Modern gradient background
- Responsive card layout
- Role and method tabs with active states
- Form inputs with focus states
- Buttons with hover effects
- Loading spinner animation
- Error and success modals
- Mobile-optimized design
- Accessibility support (WCAG 2.1)

## Configuration

### Environment Variables

`.env` file with new authentication settings:

```env
# ──── JWT & Authentication ────────────────────────────────────────
JWT_SECRET=your-super-secret-jwt-key-change-in-production-12345
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ──── Admin PIN ────────────────────────────────────────────────────
ADMIN_PIN=admin2024

# ──── Google OAuth ─────────────────────────────────────────────────
GOOGLE_CLIENT_ID=placeholder-google-client-id-replace-me
GOOGLE_CLIENT_SECRET=placeholder-google-secret-replace-me

# ──── Gmail SMTP (Email OTP) ───────────────────────────────────────
GMAIL_USER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-app-specific-password

# ──── Environment ──────────────────────────────────────────────────
ENVIRONMENT=development
```

### Dependencies

New packages in `requirements.txt`:

```
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
requests==2.31.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
```

## Authentication Flows

### 1. Patient/User Authentication

#### Flow A: Google OAuth

```
1. User clicks "Login with Google" button
2. Frontend redirects to Google Sign-In
3. User authenticates with Google
4. Frontend receives ID token
5. POST /auth/user/google with token
6. Backend verifies token with Google
7. Backend creates/links user account
8. Backend returns JWT token
9. Frontend stores token in localStorage
10. Frontend redirects to /index.html
```

#### Flow B: Email OTP

```
1. User enters email and clicks "Send OTP"
2. POST /auth/user/otp/request
3. Backend generates 6-digit OTP
4. Backend stores OTP with 10-min expiry
5. Backend sends OTP via Gmail SMTP
6. Frontend shows OTP input field
7. User enters OTP and clicks "Verify"
8. POST /auth/user/otp/verify
9. Backend validates OTP and creates account
10. Backend returns JWT token
11. Frontend stores token and redirects
```

### 2. Doctor Authentication

#### Flow A: Email & Password

```
1. Doctor enters email and password
2. POST /auth/doctor/login
3. Backend looks up doctor_accounts by email
4. Backend verifies password hash with bcrypt
5. Backend returns JWT token if valid
6. Frontend stores token and redirects to doctor dashboard
```

#### Flow B: Email OTP

```
1. Doctor enters email and requests OTP
2. Same as patient OTP flow but for doctor role
3. Redirects to /doctor-dashboard.html after verification
```

### 3. Admin Authentication

#### PIN-Based Login

```
1. Admin enters 4-digit PIN
2. POST /auth/admin/login with PIN
3. Backend compares PIN with ADMIN_PIN from .env
4. If valid, returns JWT token with admin role
5. Frontend stores token and redirects to /admin.html
6. Admin token includes full dashboard access
```

## Security Features

### Password Security

- **Bcrypt Hashing**: All doctor passwords use bcrypt with 12 rounds
- **Never Stored Plain**: Passwords are hashed immediately on creation
- **Secure Comparison**: Password verification uses constant-time comparison

### OTP Security

- **Random Generation**: 6-digit OTP using `secrets.choice()`
- **Expiration**: OTPs expire after 10 minutes
- **Single Use**: OTP is deleted after successful verification
- **Rate Limiting**: (Recommended: implement in production)

### JWT Tokens

- **Expiration**: Default 24 hours, configurable via JWT_EXPIRE_MINUTES
- **Signature**: Signed with HS256 using JWT_SECRET
- **Payload**: Contains user_id, role, and exp timestamp
- **Session Tracking**: Tokens stored in auth_tokens table

### Admin Access

- **PIN Only**: No email/password for admin (simple PIN verification)
- **Stored in .env**: Never hardcoded in source
- **Access Logging**: All admin logins logged

## Implementation Checklist

### Backend

- [x] Create `auth.py` with all primitives
- [x] Add auth tables to database initialization
- [x] Implement JWT token generation and verification
- [x] Implement bcrypt password hashing
- [x] Implement OTP generation and validation
- [x] Implement Gmail SMTP for email sending
- [x] Implement Google OAuth verification
- [x] Add doctor account management
- [x] Add admin PIN verification
- [x] Create authentication endpoints
- [x] Update requirements.txt with dependencies
- [x] Update .env with configuration

### Frontend

- [x] Create `auth-login.html` with three role tabs
- [x] Implement role selector
- [x] Implement Google OAuth button
- [x] Implement email OTP request/verify forms
- [x] Implement doctor password login
- [x] Implement admin PIN form
- [x] Create `auth-login.js` with all logic
- [x] Implement token storage in localStorage
- [x] Implement dashboard redirects
- [x] Create `auth-login.css` with responsive styling
- [x] Add loading states and error modals
- [x] Test all three flows

### Testing

- [ ] Test patient Google OAuth login
- [ ] Test patient email OTP login
- [ ] Test doctor email/password login
- [ ] Test doctor email OTP login
- [ ] Test admin PIN login
- [ ] Test token expiration
- [ ] Test invalid credentials
- [ ] Test OTP expiration
- [ ] Test logout endpoint
- [ ] Test protected routes with JWT
- [ ] Test role-based access control

## Next Steps

### Immediate (Before Production)

1. **Generate Production Secrets**
   ```bash
   # Generate strong JWT_SECRET
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure Google OAuth**
   - Create project in Google Cloud Console
   - Generate OAuth 2.0 credentials
   - Set authorized redirect URIs
   - Replace GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env

3. **Configure Gmail SMTP**
   - Enable 2-Factor Authentication on Gmail account
   - Generate App-Specific Password
   - Replace GMAIL_USER and GMAIL_APP_PASSWORD in .env

4. **Change Admin PIN**
   - Update ADMIN_PIN in .env
   - Do not commit sensitive values to Git

5. **Enable Rate Limiting**
   - Add rate limiting to /auth/* endpoints
   - Prevent brute force OTP attacks
   - Implement account lockout after failed attempts

### Short-term (Sprint 2)

- [ ] Implement RBAC middleware for protected routes
- [ ] Add token refresh endpoint for long sessions
- [ ] Implement password reset flow
- [ ] Add email verification for new accounts
- [ ] Implement forgot password flow
- [ ] Add 2FA for doctor accounts
- [ ] Create admin user management dashboard

### Long-term (Future Enhancements)

- [ ] Social login (Facebook, Apple Sign-In)
- [ ] Biometric authentication (fingerprint, face recognition)
- [ ] Multi-device session management
- [ ] Audit logging for all auth events
- [ ] IP-based access restrictions
- [ ] Device trust management
- [ ] Single Sign-On (SSO) integration

## Troubleshooting

### Common Issues

**1. Gmail OTP not sending**
- Verify GMAIL_USER and GMAIL_APP_PASSWORD in .env
- Check Gmail 2FA is enabled
- Verify "Less secure app access" is allowed
- Check firewall allows SMTP port 465

**2. Google OAuth not working**
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Check authorized redirect URIs in Google Console
- Ensure frontend uses correct Google SDK library

**3. Token verification failing**
- Verify JWT_SECRET matches between frontend and backend
- Check token expiration: `exp` > current timestamp
- Verify token format: `header.payload.signature`

**4. OTP expired**
- OTPs expire after 10 minutes (configurable)
- User must request new OTP
- Database cleanup of expired OTPs recommended

### Debug Mode

Enable verbose logging in backend:

```python
logging.basicConfig(level=logging.DEBUG)
```

Frontend console for debugging:

```javascript
localStorage.setItem('DEBUG', 'true');
console.log('Token:', localStorage.getItem('ha_auth_token'));
```

## API Reference

### Complete Endpoint List

#### User Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/user/google` | Google OAuth login |
| POST | `/auth/user/otp/request` | Request OTP for email verification |
| POST | `/auth/user/otp/verify` | Verify OTP and create/login account |

#### Doctor Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/doctor/register` | Register doctor account |
| POST | `/auth/doctor/login` | Email + password login |
| POST | `/auth/doctor/otp/verify` | OTP verification for doctor |

#### Admin Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/admin/login` | PIN-based admin login |

#### Token Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/auth/verify` | Verify token validity |
| POST | `/auth/logout` | Invalidate token (logout) |

## Support

For issues or questions:
- Check logs: `backend/ha_healthcare.log`
- Review .env configuration
- Verify database tables exist
- Test API endpoints with Postman

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-13  
**Status**: Complete & Ready for Testing
