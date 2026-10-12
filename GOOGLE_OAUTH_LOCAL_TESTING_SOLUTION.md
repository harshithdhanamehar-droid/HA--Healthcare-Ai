# Google OAuth: Local Testing + Production Setup

## TL;DR
- **Local Testing:** Use mock Google OAuth endpoint (no external setup needed)
- **Production:** Follow 6-step Google Cloud Console setup (15 minutes)

---

## PART 1: LOCAL TESTING SOLUTION (Development Mode)

### Why This Approach?
- Test complete OAuth flow locally without Google Cloud credentials
- No external API dependencies
- Identical code path to production (just different token source)
- Easily switch to production by setting `GOOGLE_CLIENT_ID`

### Setup: Enable Development Mode

**Step 1: Add environment variable**
```bash
# In backend/.env
DEV_MODE=true
GOOGLE_CLIENT_ID=local-development
JWT_SECRET=your-super-secret-local-jwt-key-at-least-32-chars
ADMIN_PIN=1234
GROQ_API_KEY=your-groq-key
```

**Step 2: Update backend/auth.py to support dev mode**

At the top of the file (after imports), add:
```python
# ─── DEVELOPMENT MODE ───────────────────────────────────────────────────────
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

def generate_mock_google_token(user_email: str) -> str:
    """Generate a mock Google OAuth ID token for development/testing."""
    if not DEV_MODE:
        return None
    
    import json
    import base64
    from datetime import datetime, timedelta
    
    # Mock payload (mimics real Google ID token structure)
    payload = {
        "iss": "https://accounts.google.com",
        "sub": f"mock_{user_email.replace('@', '_at_')}",  # Unique sub per email
        "aud": GOOGLE_CLIENT_ID,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "email": user_email,
        "email_verified": True,
        "name": user_email.split("@")[0].title(),
        "picture": "https://lh3.googleusercontent.com/a/default-user-avatar",
    }
    
    # Create a simple JWT-like string for testing
    # Format: header.payload.signature (signature is fake for dev)
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = base64.urlsafe_b64encode(b"dev_signature").decode()
    
    return f"{header}.{body}.{signature}"
```

**Step 3: Update verify_google_token() for dev mode**

Replace the `verify_google_token()` function in `backend/auth.py`:
```python
def verify_google_token(token: str) -> Optional[Dict]:
    """Verify Google OAuth token and return user info."""
    
    # ─── DEV MODE: Mock verification ─────────────────────────────────────
    if DEV_MODE:
        try:
            import json
            import base64
            
            # Parse the mock token
            parts = token.split(".")
            if len(parts) != 3:
                logger.warning("Invalid mock token format")
                return None
            
            # Decode the payload (part 1)
            payload_json = base64.urlsafe_b64decode(parts[1] + "==")
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
        logger.warning("Google OAuth not configured")
        return None
    
    try:
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
```

**Step 4: Add mock token generation endpoint**

In `backend/main.py`, add this endpoint after your existing auth routes:
```python
@app.get("/auth/google/dev-token")
async def get_dev_token(email: str = "testuser@example.com"):
    """
    DEV MODE ONLY: Generate a mock Google OAuth token for testing.
    This endpoint is ONLY available when DEV_MODE=true.
    Remove or disable in production!
    """
    if not DEV_MODE:
        raise HTTPException(status_code=403, detail="Dev mode not enabled")
    
    from auth import generate_mock_google_token
    token = generate_mock_google_token(email)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "scope": "openid email profile",
        "expires_in": 3600,
        "dev_mode": True,
    }
```

**Step 5: Update frontend to use dev token**

In `frontend/js/login.js`, update the `authenticateWithGoogle()` function to support dev mode:

```javascript
async function authenticateWithGoogle() {
    try {
        // Check if we're in dev mode by trying to fetch a dev token
        let token = null;
        let isDevMode = false;
        
        try {
            // Try to get a dev token first
            const devResponse = await fetch('/auth/google/dev-token?email=testuser@example.com');
            if (devResponse.ok) {
                const devData = await devResponse.json();
                token = devData.access_token;
                isDevMode = true;
                console.log("✓ Dev mode enabled - using mock Google token");
            }
        } catch (e) {
            // Dev endpoint not available, try production Google flow
            console.log("Dev mode not available, using production Google OAuth");
        }
        
        // If not in dev mode, use production Google OAuth flow
        if (!isDevMode) {
            // Check if Google library is loaded
            if (typeof window.google === 'undefined' || !window.google.accounts) {
                showError("Google Sign-In not available. Please try again.");
                return;
            }
            
            // Trigger Google Sign-In popup
            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: handleGoogleResponse,
            });
            
            window.google.accounts.id.renderButton(
                document.getElementById('google-signin-btn'),
                { theme: 'outline', size: 'large' }
            );
            
            document.getElementById('google-signin-btn').click();
            return;
        }
        
        // Send token to backend (works for both dev and production)
        const response = await fetch('/auth/user/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            showError(errorData.detail || 'Login failed');
            return;
        }
        
        const data = await response.json();
        localStorage.setItem('token', data.token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('role', data.role);
        
        // Redirect to chat
        window.location.href = 'chat.html';
        
    } catch (error) {
        console.error('Google auth error:', error);
        showError('An error occurred during login');
    }
}
```

### Testing Local Dev Mode

**Test 1: Generate a mock token**
```bash
curl "http://localhost:8000/auth/google/dev-token?email=alice@example.com"
```

Expected output:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "dev_mode": true
}
```

**Test 2: Log in with mock token**
```bash
# 1. Get a mock token
TOKEN=$(curl -s "http://localhost:8000/auth/google/dev-token?email=alice@example.com" | jq -r '.access_token')

# 2. Use it to authenticate
curl -X POST "http://localhost:8000/auth/user/google" \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"
```

Expected output:
```json
{
  "token": "eyJhbGc...",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Alice",
  "role": "user"
}
```

**Test 3: Test via browser**
1. Start the backend: `python backend/main.py`
2. Open `frontend/test-login.html` or `frontend/index.html`
3. Click "Sign in with Google"
4. You should see "Dev mode enabled" in browser console
5. User should be logged in automatically

---

## PART 2: PRODUCTION SETUP (Real Google OAuth)

### Prerequisites
- Google Cloud account (free tier works)
- 15 minutes
- Browser access to Google Cloud Console

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project:
   - Click project dropdown (top-left)
   - Click "NEW PROJECT"
   - Name: `HA Healthcare AI` (or your choice)
   - Click "CREATE"
3. Wait for project to initialize (2-3 minutes)

### Step 2: Enable Google OAuth 2.0 API

1. In the console, go to **APIs & Services** → **Library**
2. Search for `Google+ API` or `OAuth 2.0`
3. Click on **Google+ API**
4. Click **ENABLE**
5. Wait for it to enable (30 seconds)

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
3. You'll be prompted to "Configure OAuth Consent Screen" first:
   - Choose **External** (unless you're in an organization)
   - Click **CREATE**
   - Fill in the form:
     - App name: `HA Healthcare AI`
     - User support email: Your email
     - Developer contact: Your email
   - Click **SAVE AND CONTINUE**
   - Add scopes: Select `email`, `profile`, `openid`
   - Click **SAVE AND CONTINUE**
   - Add test users: Add your test email addresses
   - Click **SAVE AND CONTINUE**
   - Review and click **BACK TO DASHBOARD**

4. Now create the OAuth Client:
   - Go to **Credentials** again
   - Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Name: `HA Healthcare Web`
   - Authorized JavaScript origins:
     - `http://localhost:8000` (local testing)
     - `http://localhost:3000` (if you use React dev server)
     - `https://yourdomain.com` (production domain)
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/google/callback`
     - `https://yourdomain.com/auth/google/callback`
   - Click **CREATE**

5. Copy the credentials:
   - **Client ID**: Save this
   - **Client Secret**: Save this (keep it SECRET!)

### Step 4: Configure Backend Environment

1. Update `backend/.env`:
```bash
# Remove DEV_MODE or set to false
DEV_MODE=false

# Add real Google OAuth credentials
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE

# Other required variables
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_PIN=your-strong-pin-here
GROQ_API_KEY=your-groq-api-key
```

2. Restart the backend:
```bash
cd backend
python main.py
```

### Step 5: Update Frontend for Production

1. In `frontend/index.html` or where you initialize Google Sign-In, ensure:
```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
  window.onload = function() {
    google.accounts.id.initialize({
      client_id: 'YOUR_CLIENT_ID_HERE'
    });
  };
</script>
```

2. Or if using the automatic button rendering:
```html
<div id="google-signin-btn"></div>
<script>
  google.accounts.id.renderButton(
    document.getElementById('google-signin-btn'),
    { theme: 'outline', size: 'large' }
  );
</script>
```

### Step 6: Test Production OAuth

1. **Local testing with production credentials:**
   - Set `GOOGLE_CLIENT_ID` in `backend/.env`
   - Keep `DEV_MODE=false`
   - Frontend must match `GOOGLE_CLIENT_ID` in HTML
   - Click "Sign in with Google"
   - You'll be redirected to Google Sign-In
   - Accept permissions
   - You should be logged in

2. **Test with curl:**
```bash
# 1. Get authorization code (in browser, Google redirects here)
# https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_ID&redirect_uri=http://localhost:8000/auth/google/callback&response_type=code&scope=openid+email+profile

# 2. Exchange code for token (backend does this)
curl -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://localhost:8000/auth/google/callback"
```

---

## TROUBLESHOOTING

### "Invalid Client" Error
- ✓ Check GOOGLE_CLIENT_ID is correct in both backend `.env` and frontend HTML
- ✓ Check redirect URI matches in Google Cloud Console exactly

### "Unauthorized" Error
- ✓ Ensure you added your test email to "Test Users" in OAuth Consent Screen
- ✓ Check your email is in the right Google account

### Dev Mode Token Invalid
- ✓ Ensure `DEV_MODE=true` in backend `.env`
- ✓ Ensure `auth.py` has the `generate_mock_google_token()` function
- ✓ Check browser console for error messages

### Google Sign-In Button Not Appearing
- ✓ Ensure Google library is loaded: `<script src="https://accounts.google.com/gsi/client" async defer></script>`
- ✓ Check browser console for CORS errors
- ✓ Add debug logs: `console.log("Google API loaded:", window.google)`

### Production Deployment Issues
- ✓ Ensure HTTPS is enabled
- ✓ Update Google OAuth redirect URIs to production domain
- ✓ Set GOOGLE_CLIENT_ID to production value
- ✓ Check backend logs: `python backend/main.py 2>&1 | grep -i google`

---

## SWITCHING BETWEEN DEV AND PRODUCTION

### Enable Dev Mode (Local Testing)
```bash
# backend/.env
DEV_MODE=true
GOOGLE_CLIENT_ID=local-development
```

Then restart backend and visit `/auth/google/dev-token` to test.

### Enable Production Mode
```bash
# backend/.env
DEV_MODE=false
GOOGLE_CLIENT_ID=YOUR_REAL_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_REAL_SECRET
```

Then restart backend and test with real Google OAuth.

---

## SECURITY NOTES

1. **Never commit secrets** to git:
   ```bash
   echo "backend/.env" >> .gitignore
   ```

2. **Use environment variables in production:**
   - Render, Vercel, AWS: Set in dashboard, not `.env`
   - Docker: Pass via `-e` flag or `.env` file

3. **Dev token endpoint should be disabled in production:**
   - The `@app.get("/auth/google/dev-token")` endpoint checks `DEV_MODE`
   - If `DEV_MODE=false`, endpoint returns 403 Forbidden
   - Never allow this endpoint in production!

4. **Google Client Secret must be kept secret:**
   - Only backend should have access
   - Never expose in frontend code
   - Never commit to git

---

## QUICK REFERENCE

| Scenario | Environment | Steps |
|----------|-------------|-------|
| **Local Testing (No Setup)** | DEV_MODE=true | 1. Set env var<br>2. Restart backend<br>3. Add dev functions to auth.py<br>4. Click "Sign in with Google" |
| **Production** | DEV_MODE=false | 1. Create Google Cloud project<br>2. Generate Client ID/Secret<br>3. Set environment variables<br>4. Update frontend GOOGLE_CLIENT_ID<br>5. Test with real Google account |
| **Switch from Dev to Prod** | Both exist | 1. Change DEV_MODE=false<br>2. Set GOOGLE_CLIENT_ID to real value<br>3. Restart backend<br>4. Frontend must use same GOOGLE_CLIENT_ID |

