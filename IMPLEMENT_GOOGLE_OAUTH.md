# Google OAuth Implementation Guide

**Status**: Ready to Implement  
**Complexity**: Medium  

---

## Overview

This guide shows how to add Google OAuth to the existing login page with the new location-aware flow.

---

## Step 1: Get Google OAuth Credentials

### Prerequisites
1. Google account
2. Access to Google Cloud Console

### Steps
1. Go to: https://console.cloud.google.com/
2. Create new project (or use existing)
3. Enable OAuth 2.0
4. Create OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs:
     - `http://localhost:3000/callback`
     - `http://localhost:8000/callback`
     - `https://your-domain.com/callback`
5. Copy `Client ID` and `Client Secret`

### Store in .env
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/callback
```

---

## Step 2: Frontend Implementation

### 1. Update Login Page (index.html)

Add Google OAuth library to login page:
```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

Add Google OAuth container to patient tab:
```html
<!-- In patient login form, after "Continue with Google" button -->
<div id="g_id_onload"
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleGoogleLogin">
</div>
<div class="g_id_signin" data-type="standard"></div>
```

### 2. Update login.js

Add Google OAuth handler:
```javascript
// Handle Google OAuth callback
async function handleGoogleLogin(response) {
  const credential = response.credential;
  
  // Decode JWT token from Google
  const decoded = jwt_decode(credential);
  const { sub: googleSub, email, name } = decoded;
  
  console.log('Google login:', { googleSub, email, name });
  
  // Step 1: Check if user exists
  try {
    const checkResponse = await fetch(`${API_BASE}/auth/google/check-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ google_sub: googleSub, email })
    });
    
    const checkData = await checkResponse.json();
    
    if (checkData.exists) {
      // Returning user - auto login
      console.log('Returning Google user');
      
      saveAuthToken(
        generateToken(checkData.user_id),
        checkData.user_id,
        'user',
        3600
      );
      
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_name', checkData.name);
      localStorage.setItem('ha_email', checkData.email);
      localStorage.setItem('ha_location', checkData.location);
      
      // Immediate redirect
      window.location.href = 'chat.html';
    } else {
      // New user - show location selector
      console.log('New Google user - ask for location');
      showGoogleLocationSelector(googleSub, email, name);
    }
  } catch (error) {
    console.error('Error checking user:', error);
    showError('error-msg', 'Google login failed');
  }
}

// Show location selector for new Google users
function showGoogleLocationSelector(googleSub, email, name) {
  const locationSelector = document.getElementById('google-location-selector');
  if (!locationSelector) {
    // Create it if it doesn't exist
    const html = `
      <div id="google-location-selector" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
      ">
        <div style="
          background: var(--bg-card);
          padding: 32px;
          border-radius: 12px;
          max-width: 400px;
          text-align: center;
        ">
          <h3>Welcome to HA! 🏥</h3>
          <p>Select your location</p>
          <select id="google-location-select" style="
            width: 100%;
            padding: 10px;
            margin: 16px 0;
            border-radius: 6px;
          ">
            <option value="">-- Select Location --</option>
            <option value="Hyderabad">Hyderabad</option>
            <option value="Bangalore">Bangalore</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Chennai">Chennai</option>
            <option value="Delhi">Delhi</option>
          </select>
          <button onclick="completeGoogleRegistration('${googleSub}', '${email}', '${name}')" style="
            width: 100%;
            padding: 12px;
            background: var(--accent);
            border: none;
            color: #0f1117;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
          ">
            Continue
          </button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
  }
}

// Complete Google registration after location selection
async function completeGoogleRegistration(googleSub, email, name) {
  const location = document.getElementById('google-location-select').value;
  
  if (!location) {
    alert('Please select a location');
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE}/auth/google/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        google_sub: googleSub,
        email: email,
        name: name,
        location: location
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      saveAuthToken(
        generateToken(data.user_id),
        data.user_id,
        'user',
        3600
      );
      
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_name', data.name);
      localStorage.setItem('ha_email', data.email);
      localStorage.setItem('ha_location', data.location);
      
      window.location.href = 'chat.html';
    } else {
      showError('error-msg', data.message || 'Registration failed');
    }
  } catch (error) {
    console.error('Error completing registration:', error);
    showError('error-msg', 'Registration failed');
  }
}

// Helper to generate fake JWT (use real JWT from backend in production)
function generateToken(userId) {
  const payload = {
    sub: userId,
    role: 'user',
    exp: Math.floor(Date.now() / 1000) + 3600
  };
  
  return btoa(JSON.stringify(payload)); // Simple encoding for now
}
```

### 3. Add JWT Decoder Library

Add to index.html `<head>`:
```html
<script src="https://cdn.jsdelivr.net/npm/jwt-decode@3.1.2/build/jwt-decode.min.js"></script>
```

---

## Step 3: Backend Implementation (Already Done!)

### Check Implementation
The backend already has:
- ✅ POST `/auth/google/check-user`
- ✅ POST `/auth/google/register`
- ✅ Enhanced `/doctors` endpoint with location sorting
- ✅ Updated database schema

### Verify Setup
```bash
# Check if google endpoints exist
curl http://127.0.0.1:8000/docs

# Should show:
# - POST /auth/google/check-user
# - POST /auth/google/register
```

---

## Step 4: Update Login.html Structure

### Current Google Button
```html
<button type="button" class="auth-btn google-btn" id="googleLoginBtn">
  <svg class="google-icon" viewBox="0 0 24 24" ...></svg>
  Continue with Google
</button>
```

### Enhanced with OAuth
```html
<div id="g_id_onload"
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleGoogleLogin"
     data-auto_prompt="false">
</div>
<div class="g_id_signin" data-type="standard"></div>
```

---

## Step 5: Testing

### Test 1: New Google User Flow
```
1. Open login page
2. Click Google sign-in
3. Authenticate with Google account
4. Should see location selector
5. Select location
6. Should redirect to chat.html
7. Check localStorage for ha_location
```

### Test 2: Returning Google User
```
1. Use same Google account again
2. Click Google sign-in
3. Should bypass location selector
4. Immediate redirect to chat.html
```

### Test 3: Doctor Recommendation
```
1. Go to Doctors page
2. Should see "📍 Showing doctors near [location]"
3. First doctors should be from selected location
4. Other doctors sorted by rating
```

### API Tests
```bash
# Test new user check
curl -X POST http://127.0.0.1:8000/auth/google/check-user \
  -H "Content-Type: application/json" \
  -d '{
    "google_sub": "test-google-123",
    "email": "test@gmail.com"
  }'

# Test registration
curl -X POST http://127.0.0.1:8000/auth/google/register \
  -H "Content-Type: application/json" \
  -d '{
    "google_sub": "test-google-123",
    "email": "test@gmail.com",
    "name": "Test User",
    "location": "Hyderabad"
  }'

# Test location-aware doctors
curl 'http://127.0.0.1:8000/doctors?user_location=Hyderabad'
```

---

## Configuration Checklist

- [ ] Get Google OAuth Client ID
- [ ] Get Google OAuth Client Secret
- [ ] Add credentials to .env
- [ ] Add Google Sign-In library to index.html
- [ ] Add JWT decoder library
- [ ] Update login.js with Google handler
- [ ] Add location selector modal
- [ ] Update doctors.js to use user_location
- [ ] Test new user flow
- [ ] Test returning user flow
- [ ] Test doctor recommendation

---

## Files to Update

### Frontend
1. **`frontend/index.html`**
   - Add Google SDK
   - Add JWT decoder
   - Add location selector HTML

2. **`frontend/js/login.js`**
   - Add `handleGoogleLogin()`
   - Add `showGoogleLocationSelector()`
   - Add `completeGoogleRegistration()`

3. **`frontend/js/doctors.js`** ✅ ALREADY DONE

4. **`frontend/css/pages.css`** ✅ ALREADY DONE

### Backend
- **`backend/main.py`** ✅ ALREADY DONE

---

## Environment Setup

### .env File
```
# Existing
GROQ_API_KEY=...
JWT_SECRET=...
ADMIN_PIN=...

# Add these
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=yyy
GOOGLE_REDIRECT_URI=http://localhost:8000/callback
```

---

## Production Deployment

### Before Going Live
1. ✅ Update Google OAuth redirect URIs (use production domain)
2. ✅ Update `.env` with production credentials
3. ✅ Test full flow in staging
4. ✅ Verify database schema on production
5. ✅ Monitor logs for errors

### Google Console Settings
- Add production domain to authorized redirect URIs
- Update client ID/secret if needed
- Enable OAuth consent screen

---

## Troubleshooting

### Issue: Google button not appearing
- Check Google SDK is loaded: `window.google` should exist
- Check client ID is correct
- Check CORS settings

### Issue: "needs_location" always true
- Clear browser localStorage
- Check database schema has google_sub field
- Verify registration created user correctly

### Issue: Doctor location not showing
- Ensure doctors.js has new code
- Check ha_location is set in localStorage
- Verify backend returns doctors with location field

### Issue: Token not saving to localStorage
- Check browser allows localStorage
- Check JWT decoder is loaded
- Check saveAuthToken function

---

## Success Criteria

✅ **New Google User**:
- Sees location selector after Google auth
- Location saved to database
- Redirects to chat.html

✅ **Returning Google User**:
- Auto-logs in (no location prompt)
- Immediate redirect to chat.html

✅ **Doctor Recommendations**:
- Doctors from user's location appear first
- "📍 Near You" badges on matching doctors
- Other doctors sorted by rating

✅ **Backward Compatibility**:
- Normal login still works
- Existing users unaffected
- Phone login still available

---

## Next Steps

1. Implement Google OAuth button (follow Step 2 above)
2. Test with Google test account
3. Deploy to staging
4. Get production Google credentials
5. Deploy to production

---

*Implementation guide for Google OAuth with location-aware doctor recommendations.*
