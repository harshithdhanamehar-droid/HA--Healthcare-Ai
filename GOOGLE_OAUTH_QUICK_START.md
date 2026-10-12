# Google OAuth: 5-Minute Quick Start

Choose your path:

---

## PATH 1: Local Testing (No Google Cloud Setup) ⚡

### Goal
Test Google OAuth login locally without any external setup.

### Time: 5 minutes

### Steps

**1. Update backend/.env**
```bash
DEV_MODE=true
GOOGLE_CLIENT_ID=local-development
JWT_SECRET=your-secret-key-here
ADMIN_PIN=1234
GROQ_API_KEY=your-groq-key
```

**2. Add dev mode to backend/auth.py**

Open `backend/auth.py`, add after imports (before `# ─── CONFIGURATION ───`):

```python
# ─── DEVELOPMENT MODE ───────────────────────────────────────────────────────
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

def generate_mock_google_token(user_email: str) -> str:
    """Generate a mock Google OAuth ID token for development/testing."""
    if not DEV_MODE:
        return None
    try:
        import json, base64
        from datetime import datetime, timedelta
        payload = {
            "iss": "https://accounts.google.com",
            "sub": f"mock_{user_email.replace('@', '_at_')}",
            "aud": GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID else "local-development",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "email": user_email,
            "email_verified": True,
            "name": user_email.split("@")[0].title(),
            "picture": "https://lh3.googleusercontent.com/a/default-user-avatar",
        }
        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode()
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = base64.urlsafe_b64encode(b"dev_signature").decode()
        return f"{header}.{body}.{signature}"
    except Exception as e:
        logger.error("Failed to generate mock Google token: %s", e)
        return None
```

**3. Update verify_google_token() in backend/auth.py**

Find the `verify_google_token()` function (around line 200-250), replace it:

```python
def verify_google_token(token: str) -> Optional[Dict]:
    """Verify Google OAuth token and return user info."""
    
    # ─── DEV MODE ───────────────────────────────────────────────────────
    if DEV_MODE:
        try:
            import json, base64
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            logger.info("Dev mode: Mock Google token verified for %s", payload.get("email"))
            return {
                "google_sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
            }
        except Exception as e:
            logger.error("Dev mode: Mock token verification failed: %s", e)
            return None
    
    # ─── PRODUCTION MODE ────────────────────────────────────────────────
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.warning("Google OAuth not configured")
        return None
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": token},
            timeout=10,
        )
        if response.status_code != 200:
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
```

**4. Add dev endpoint to backend/main.py**

Find the existing Google auth routes section, add this endpoint:

```python
@app.get("/auth/google/dev-token")
async def get_dev_token(email: str = "testuser@example.com"):
    """DEV MODE ONLY: Generate a mock Google OAuth token for testing."""
    from auth import DEV_MODE, generate_mock_google_token
    
    if not DEV_MODE:
        raise HTTPException(status_code=403, detail="Dev mode not enabled")
    
    try:
        token = generate_mock_google_token(email)
        if not token:
            raise HTTPException(status_code=500, detail="Failed to generate dev token")
        logger.info("Generated dev token for email: %s", email)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "scope": "openid email profile",
            "expires_in": 3600,
            "dev_mode": True,
        }
    except Exception as e:
        logger.error("Error generating dev token: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

**5. Restart backend**
```bash
cd backend
python main.py
```

**6. Test**
```bash
# Terminal: Get a dev token
curl "http://localhost:8000/auth/google/dev-token?email=alice@example.com"

# Browser: Open frontend/index.html
# Click "Sign in with Google"
# Should see "Dev mode enabled" in console
# Should be logged in!
```

---

## PATH 2: Production Setup (Real Google OAuth) 🌍

### Goal
Set up real Google OAuth for production deployment.

### Time: 15 minutes

### Steps

**1. Create Google Cloud Project**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create new project: `HA Healthcare AI`
- Wait for initialization

**2. Enable OAuth API**
- Go to **APIs & Services** → **Library**
- Search `Google+ API`
- Click **ENABLE**

**3. Create OAuth Credentials**
- Go to **APIs & Services** → **Credentials**
- Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**

**4. Configure OAuth Consent Screen** (if prompted)
- Choose **External**
- Fill in:
  - App name: `HA Healthcare AI`
  - User support email: your@email.com
  - Developer contact: your@email.com
- Add scopes: `email`, `profile`, `openid`
- Add test users: your@email.com
- Save

**5. Create OAuth Client**
- Application type: **Web application**
- Name: `HA Healthcare Web`
- Authorized JavaScript origins:
  - `http://localhost:8000`
  - `https://yourdomain.com` (for production)
- Authorized redirect URIs:
  - `http://localhost:8000/auth/google/callback`
  - `https://yourdomain.com/auth/google/callback`
- Click **CREATE**
- Save **Client ID** and **Client Secret**

**6. Update backend/.env**
```bash
DEV_MODE=false
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
JWT_SECRET=your-secret-key
ADMIN_PIN=1234
GROQ_API_KEY=your-groq-key
```

**7. Restart backend**
```bash
cd backend
python main.py
```

**8. Test**
```bash
# Browser: Open frontend/index.html
# Click "Sign in with Google"
# You should be redirected to Google Sign-In
# Accept permissions
# Should be logged in to your app!
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "Dev mode not enabled" | Check `DEV_MODE=true` in `.env` and restart backend |
| Google button doesn't appear | Check browser console for CORS errors; ensure Google library loaded |
| "Invalid client" error | Check GOOGLE_CLIENT_ID is correct in both `.env` and frontend |
| "Unauthorized" error | Add your test email to "Test Users" in Google OAuth Consent Screen |
| Mock token generation fails | Verify `generate_mock_google_token()` function exists in `auth.py` |

---

## NEXT STEPS

1. **Local Dev:** Use PATH 1 for immediate testing
2. **Before Deployment:** Follow PATH 2 for production credentials
3. **Deploy:** Set environment variables on your hosting platform (Render, Vercel, etc.)
4. **Test:** Verify login works with real Google account

---

## FILES TO MODIFY

**Path 1 (Local Dev):**
- [ ] `backend/.env` - Add DEV_MODE=true
- [ ] `backend/auth.py` - Add generate_mock_google_token() and update verify_google_token()
- [ ] `backend/main.py` - Add /auth/google/dev-token endpoint

**Path 2 (Production):**
- [ ] Create Google Cloud project + OAuth credentials (15 min)
- [ ] Update `backend/.env` with real credentials
- [ ] Ensure frontend uses correct GOOGLE_CLIENT_ID

---

## VERIFY EACH PATH

### Verify Path 1 Works
```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Test endpoint
curl "http://localhost:8000/auth/google/dev-token?email=test@example.com"

# Browser: Open frontend/index.html, click "Sign in with Google"
# Expected: Logged in without Google sign-in popup
```

### Verify Path 2 Works
```bash
# Terminal 1: Start backend with production config
cd backend
python main.py

# Browser: Open frontend/index.html, click "Sign in with Google"
# Expected: Redirected to Google, then logged in
```

---

## SECURITY CHECKLIST

- [ ] backend/.env is in .gitignore (never commit secrets)
- [ ] DEV_MODE=false in production
- [ ] /auth/google/dev-token endpoint returns 403 when DEV_MODE=false
- [ ] GOOGLE_CLIENT_SECRET stored only in environment (not in code)
- [ ] Production domain added to authorized URIs in Google Cloud

