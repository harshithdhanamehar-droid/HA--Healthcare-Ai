# Auth Dev Mode Implementation - Code Changes

## Overview
This guide provides exact code changes needed to enable local Google OAuth testing with mocks.

---

## File 1: backend/auth.py

### Change 1: Add DEV_MODE and mock token generation (after imports)

**Location:** Line ~30, after imports, before `# ─── CONFIGURATION ───`

**Add this code:**

```python
# ─── DEVELOPMENT MODE ───────────────────────────────────────────────────────
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

def generate_mock_google_token(user_email: str) -> str:
    """
    Generate a mock Google OAuth ID token for development/testing.
    
    Args:
        user_email: Email address to use in the mock token
        
    Returns:
        JWT-like string token for testing (not cryptographically valid)
    """
    if not DEV_MODE:
        return None
    
    try:
        import json
        import base64
        from datetime import datetime, timedelta
        
        # Mock payload (mimics real Google ID token structure)
        payload = {
            "iss": "https://accounts.google.com",
            "sub": f"mock_{user_email.replace('@', '_at_')}",  # Unique sub per email
            "aud": GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID else "local-development",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "email": user_email,
            "email_verified": True,
            "name": user_email.split("@")[0].title(),
            "picture": "https://lh3.googleusercontent.com/a/default-user-avatar",
        }
        
        # Create a simple JWT-like string for testing
        # Format: header.payload.signature (signature is fake for dev)
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
        ).decode()
        body = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()
        signature = base64.urlsafe_b64encode(b"dev_signature").decode()
        
        token = f"{header}.{body}.{signature}"
        logger.info("Generated mock Google token for %s", user_email)
        return token
        
    except Exception as e:
        logger.error("Failed to generate mock Google token: %s", e)
        return None
```

### Change 2: Replace verify_google_token() function

**Location:** Line ~200 (find the existing `def verify_google_token(token: str)` function)

**Replace entire function with:**

```python
def verify_google_token(token: str) -> Optional[Dict]:
    """
    Verify Google OAuth token and return user info.
    
    Supports both dev mode (mock tokens) and production mode (real Google verification).
    
    Args:
        token: Google OAuth token or mock token
        
    Returns:
        Dictionary with google_sub, email, name or None if invalid
    """
    
    # ─── DEV MODE: Mock verification ─────────────────────────────────────
    if DEV_MODE:
        try:
            import json
            import base64
            
            logger.info("Dev mode: Verifying mock Google token")
            
            # Parse the mock token
            parts = token.split(".")
            if len(parts) != 3:
                logger.warning("Invalid mock token format (expected 3 parts)")
                return None
            
            # Decode the payload (part 1)
            # Add padding if needed for base64 decoding
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
    
    # ─── PRODUCTION MODE: Real Google verification ──────────────────────
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.warning("Google OAuth not configured (missing CLIENT_ID or SECRET)")
        return None
    
    try:
        logger.info("Production mode: Verifying real Google token")
        
        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": token},
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.warning("Google token verification failed: status %d", response.status_code)
            return None
        
        data = response.json()
        logger.info("Production mode: Google token verified for %s", data.get("email"))
        
        return {
            "google_sub": data.get("user_id"),
            "email": data.get("email"),
            "name": data.get("name"),
        }
    except Exception as e:
        logger.error("Google token verification error: %s", e)
        return None
```

---

## File 2: backend/main.py

### Change: Add dev token endpoint

**Location:** Find the existing auth routes (around line 800-900), add this endpoint after the existing Google auth routes:

```python
@app.get("/auth/google/dev-token")
async def get_dev_token(email: str = "testuser@example.com"):
    """
    DEV MODE ONLY: Generate a mock Google OAuth token for testing.
    
    This endpoint is ONLY available when DEV_MODE=true in backend/.env.
    In production (DEV_MODE=false), this endpoint returns 403 Forbidden.
    
    Usage:
        curl "http://localhost:8000/auth/google/dev-token?email=alice@example.com"
        
    Returns:
        Mock Google OAuth token suitable for testing /auth/user/google endpoint
    """
    from auth import DEV_MODE, generate_mock_google_token
    
    if not DEV_MODE:
        logger.warning("Dev token endpoint accessed but DEV_MODE is disabled")
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
            "message": "This is a mock token for development only",
        }
    except Exception as e:
        logger.error("Error generating dev token: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## File 3: backend/.env

### Update environment variables:

```bash
# ─── DEVELOPMENT MODE ───────────────────────────────────────────────────────
# Set to 'true' for local testing with mock Google tokens
# Set to 'false' for production with real Google OAuth
DEV_MODE=true

# ─── GOOGLE OAUTH ────────────────────────────────────────────────────────────
# For DEV_MODE: Can be any value (e.g., 'local-development')
# For PRODUCTION: Get from Google Cloud Console
GOOGLE_CLIENT_ID=local-development
GOOGLE_CLIENT_SECRET=unused-in-dev-mode

# ─── JWT CONFIGURATION ───────────────────────────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ─── ADMIN ───────────────────────────────────────────────────────────────────
ADMIN_PIN=1234

# ─── GROQ AI ──────────────────────────────────────────────────────────────────
# Get from: https://console.groq.com
GROQ_API_KEY=your-groq-api-key-here
```

---

## Testing Workflow

### Step 1: Update Files
1. Add `generate_mock_google_token()` to `backend/auth.py`
2. Replace `verify_google_token()` in `backend/auth.py`
3. Add `@app.get("/auth/google/dev-token")` endpoint to `backend/main.py`
4. Update `backend/.env` with `DEV_MODE=true`

### Step 2: Start Backend
```bash
cd backend
python main.py
```

You should see:
```
[INFO] ha_healthcare: Application startup complete
[INFO] ha_healthcare: Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test Dev Endpoint
```bash
# Test with curl
curl "http://localhost:8000/auth/google/dev-token?email=alice@example.com"

# Expected output:
# {
#   "access_token": "eyJhbGc...",
#   "token_type": "Bearer",
#   "dev_mode": true
# }
```

### Step 4: Test Full Login Flow
```bash
# 1. Get a mock token
TOKEN=$(curl -s "http://localhost:8000/auth/google/dev-token?email=alice@example.com" | jq -r '.access_token')
echo "Token: $TOKEN"

# 2. Authenticate with the token
curl -X POST "http://localhost:8000/auth/user/google" \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"

# Expected output:
# {
#   "token": "eyJhbGc...",
#   "user_id": "123e4567...",
#   "name": "Alice",
#   "role": "user",
#   "message": "Logged in successfully"
# }
```

### Step 5: Test via Browser
1. Open `frontend/index.html` or `frontend/test-login.html`
2. Click "Sign in with Google"
3. Check browser console - should show "Dev mode enabled"
4. Should be automatically logged in
5. Redirect to `chat.html`

---

## Switching to Production

### Update backend/.env:
```bash
DEV_MODE=false
GOOGLE_CLIENT_ID=YOUR_REAL_CLIENT_ID_FROM_GOOGLE_CLOUD
GOOGLE_CLIENT_SECRET=YOUR_REAL_SECRET
```

### Restart backend:
```bash
python backend/main.py
```

Now OAuth flow will use real Google verification instead of mocks.

---

## Common Issues

### Issue: "Dev mode not enabled"
```
Error: HTTPException(status_code=403, detail="Dev mode not enabled")
```

**Fix:** Ensure `DEV_MODE=true` in `backend/.env` and restart backend

### Issue: "Token generation failed"
```
Error: Failed to generate mock Google token
```

**Fix:** 
- Check `GOOGLE_CLIENT_ID` is set in `.env`
- Check `generate_mock_google_token()` function is present in `auth.py`
- Check backend logs for detailed error

### Issue: "Invalid mock token format"
```
Error: Invalid mock token format (expected 3 parts)
```

**Fix:**
- Ensure token has 3 parts separated by dots (header.payload.signature)
- Regenerate token from `/auth/google/dev-token` endpoint

---

## Security Checklist

- [ ] DEV_MODE is set to `false` in production
- [ ] GOOGLE_CLIENT_SECRET is never logged or exposed
- [ ] `/auth/google/dev-token` endpoint is unreachable in production (returns 403)
- [ ] backend/.env is in .gitignore
- [ ] Real GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set via environment variables in production

