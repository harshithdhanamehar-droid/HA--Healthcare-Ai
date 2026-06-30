# HA! Healthcare AI — Quick Start Guide v3

## 🚀 5-Minute Setup

### Step 1: Configure Gmail (Optional but Recommended)

**Why:** Enable email confirmations for appointments and OTP verification

**Steps:**

1. Open `backend/.env`
2. Find these lines:
   ```env
   GMAIL_USER=your-gmail@gmail.com
   GMAIL_APP_PASSWORD=your-app-specific-password
   ```

3. **Generate Gmail App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select **Mail** and your device
   - Copy the **16-character password** (spaces included)
   - Paste into `.env`:
   ```env
   GMAIL_USER=myemail@gmail.com
   GMAIL_APP_PASSWORD=qwer tyui asdf ghjk
   ```

4. Save `.env`

**Troubleshooting:**
- If "App passwords" option unavailable: Enable 2-Factor Authentication first
- If emails don't send: Check junk/spam folder
- If credentials invalid: Regenerate a new app password

---

### Step 2: Start Backend

```bash
cd backend
pip install -r requirements.txt  # First time only
python main.py
```

**Expected Output:**
```
INFO:ha_healthcare:Database initialised successfully with auth tables.
INFO:ha_healthcare:Successfully migrated 8 doctors to database
INFO:uvicorn.server:Application startup complete
Uvicorn running on http://127.0.0.1:8000
```

---

### Step 3: Start Frontend

**Option A: File-based (Quick)**
```bash
# Simply open in browser
file:///path/to/HA-Healthcare-AI/frontend/index.html
```

**Option B: Local server (Better for CORS)**
```bash
# From any directory
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

---

### Step 4: Login & Test

1. Open frontend
2. Click "Login"
3. Use test credentials:
   - **Email:** test@example.com
   - **Password:** password123 (or any password)

4. Set location: **Hyderabad** (matches doctor locations)

5. Done! ✅

---

## 📝 New Features to Try

### Feature 1: Book Appointment (with Email)

```
1. Click "Find Doctors"
2. Select a doctor
3. Click "Book Appointment"
4. Fill in details
5. RESULT: 
   - Appointment saved
   - Confirmation email sent (if Gmail configured)
   - Doctor notification sent
```

### Feature 2: Chat History (Recent Chats)

```
1. Click "AI Chat"
2. Send a message: "I have a headache"
3. Wait for AI response
4. Look at sidebar → "Recent Chats"
5. RESULT:
   - Chat appears in list
   - Title shows: "I have a headache"
   - Sorted by most recent
```

### Feature 3: Manage Chats

```
1. In Recent Chats, find a chat
2. Hover or right-click
3. Options:
   - Rename: Change title
   - Archive: Move to archive
   - Delete: Remove chat
4. Search: Use search box (if available)
```

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port not in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Mac/Linux
```

### Emails not sending
```bash
# Check .env configuration
cat backend/.env | grep GMAIL

# Expected:
# GMAIL_USER=your-email@gmail.com
# GMAIL_APP_PASSWORD=16-char-password

# Check email logs in database
sqlite3 backend/ha_healthcare.db
> SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 5;
```

### Chat history not showing
```bash
# Check browser console (F12)
# Look for red error messages

# Check backend logs
# Should see: "loadChatHistory: API response = ..."

# Verify chat_sessions table exists
sqlite3 backend/ha_healthcare.db
> SELECT COUNT(*) FROM chat_sessions;
```

### Frontend can't reach backend
```bash
# Ensure backend is running on port 8000
# Check frontend console (F12 → Console tab)
# Should see: "loading..." not errors

# If using file:// protocol:
# API_BASE is http://127.0.0.1:8000

# If using http://localhost:3000:
# API_BASE is http://127.0.0.1:8000
# (auto-detected from app.js)
```

---

## 📊 Database Inspection

### View Chat Sessions
```bash
sqlite3 backend/ha_healthcare.db

# List all chats
SELECT chat_id, title, preview, updated_at 
FROM chat_sessions 
ORDER BY updated_at DESC;

# List archived chats
SELECT * FROM chat_sessions WHERE is_archived = 1;

# Count chats per user
SELECT user_phone, COUNT(*) as chat_count 
FROM chat_sessions 
GROUP BY user_phone;
```

### View Email Logs
```bash
# All emails sent
SELECT recipient, email_type, status, created_at 
FROM email_logs 
ORDER BY created_at DESC;

# Failed emails
SELECT recipient, error_message, created_at 
FROM email_logs 
WHERE status = 'failed'
ORDER BY created_at DESC;

# Email statistics
SELECT email_type, status, COUNT(*) 
FROM email_logs 
GROUP BY email_type, status;
```

### View Appointments
```bash
# All appointments
SELECT appointment_id, patient_name, doctor_name, 
       appointment_date, status, created_at 
FROM appointments 
ORDER BY created_at DESC;

# Pending appointments (not yet confirmed)
SELECT * FROM appointments WHERE status = 'pending';
```

---

## 🎯 Common Workflows

### Workflow 1: Test Email Sending

```
1. Start backend with Gmail configured
2. Open frontend
3. Navigate to "Find Doctors"
4. Select "Dr. Priya Sharma"
5. Click "Book Appointment"
6. Fill in:
   - Patient: John
   - Phone: 9876543210
   - Date: 2026-06-20
   - Time: 10:00 AM
   - Reason: Regular checkup
7. Click "Confirm Booking"
8. SUCCESS: Appointment created
9. CHECK: Did you receive email?
10. CHECK database:
    sqlite3 backend/ha_healthcare.db
    SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 1;
```

### Workflow 2: Test Chat Session Management

```
1. Click "AI Chat"
2. Send: "I have a fever and cough"
3. Wait for AI response
4. Send: "Should I see a doctor?"
5. Wait for response
6. Look at Recent Chats sidebar
7. Hover over your chat
8. Click rename → "My cold symptoms"
9. Check: Title updated
10. Archive the chat
11. Check: Chat disappears from Recent list
12. Look for "View Archived" button
13. Click it
14. Verify: Chat appears in archived list
15. Unarchive it
16. Verify: Chat returns to Recent list
```

### Workflow 3: Test Backward Compatibility

```
1. Ensure all existing features work:
   - [ ] Chat AI responses normal
   - [ ] Symptom checker works
   - [ ] Doctor booking works
   - [ ] Appointments display
   - [ ] User profile persists
   - [ ] Logout/login works
```

---

## 📱 Mobile Testing

### Test on Mobile (iPhone/Android)

```
# Use local server (not file://)
cd frontend
python -m http.server 3000

# Find your computer's IP
ipconfig getifaddr en0  # Mac
ipconfig  # Windows
hostname -I  # Linux

# On phone, visit:
http://<your-ip>:3000

# Test:
- Chat works
- Recent chats scrolls (no overlap)
- Navigation menu stays fixed
- Buttons clickable
- Text readable
```

---

## 🔐 Security Checklist

- [ ] Gmail App Password used (NOT regular password)
- [ ] `.env` not committed to git
- [ ] No hardcoded credentials in code
- [ ] Backend CORS configured properly
- [ ] Database file has restricted permissions
- [ ] No sensitive data in browser console logs

---

## 📈 Performance Tips

### Optimize for Speed

```bash
# Backend
# Enable WAL mode (already in main.py)
# Create database indexes (already done)

# Frontend
# Use http://localhost:3000 (not file://)
# Enables proper caching headers
# Faster asset loading
```

### Monitor Performance

```
# Check database size
ls -lh backend/ha_healthcare.db

# If > 100MB, consider cleanup
# Archive old chats
# Delete old email logs
```

---

## 🚨 Emergency Scenarios

### Email Service Down

**What happens:**
- Appointments still save ✅
- Emails don't send ❌
- Errors logged to database ✅

**Recovery:**
```bash
# Check email_logs for failures
sqlite3 backend/ha_healthcare.db
SELECT error_message FROM email_logs 
WHERE status = 'failed' 
ORDER BY created_at DESC LIMIT 1;

# Restart backend with correct credentials
# Resend emails manually or wait for admin retry feature
```

### Chat Data Corrupted

**Backup & Recovery:**
```bash
# Backup database
cp backend/ha_healthcare.db backend/ha_healthcare.db.backup

# Verify integrity
sqlite3 backend/ha_healthcare.db "PRAGMA integrity_check;"

# Should return: "ok"
```

### Lost Email Credentials

**Recovery:**
```
1. Go to https://myaccount.google.com/apppasswords
2. Generate new app password
3. Update .env file
4. Restart backend
```

---

## 📚 Documentation

- **Full API Reference:** `API_REFERENCE_v3.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY_v3.md`
- **Testing Guide:** `TESTING_CHECKLIST.md`
- **Architecture:** `ARCHITECTURE.md`

---

## 🎓 Next Steps

After quickstart:

1. **Read Full Documentation:**
   - `IMPLEMENTATION_SUMMARY_v3.md` — All changes explained
   - `API_REFERENCE_v3.md` — API endpoints reference

2. **Run Full Test Suite:**
   - Use `TESTING_CHECKLIST.md`
   - Verify all features work
   - Check error handling

3. **Customize for Production:**
   - Set up proper domain
   - Configure prod email
   - Enable HTTPS
   - Set JWT_SECRET to random value

4. **Explore Advanced Features:**
   - Doctor dashboard (if implemented)
   - Patient health records
   - Telemedicine integration
   - Admin analytics

---

## 💡 Tips & Tricks

### Quickly Create Test Data

```bash
# Create multiple chats quickly
python << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('backend/ha_healthcare.db')
cursor = conn.cursor()

# Create 5 test chats
for i in range(5):
    chat_id = f"test_chat_{i}"
    cursor.execute("""
        INSERT INTO chat_sessions 
        (chat_id, user_phone, title, preview, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        chat_id,
        '9876543210',
        f'Test chat {i}',
        f'This is test message {i}',
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

conn.commit()
conn.close()
print("Created 5 test chats")
EOF
```

### View Real-time Logs

```bash
# Watch backend logs as they happen
tail -f backend/ha_healthcare.db.log  # If logging enabled

# Or use built-in logging
python main.py 2>&1 | tee backend/logs.txt
```

### Debug Frontend Issues

```javascript
// In browser console (F12)

// Check API base URL
console.log(API_BASE)

// Check stored data
console.log(localStorage)

// Check chat data
fetch('http://127.0.0.1:8000/chat/history/9876543210')
  .then(r => r.json())
  .then(d => console.log(JSON.stringify(d, null, 2)))
```

---

## ✅ Ready?

```bash
# Start backend
cd backend && python main.py

# In new terminal, start frontend
cd frontend && python -m http.server 3000

# Open browser
http://localhost:3000

# Login and start testing!
```

**Happy coding! 🎉**

---

*Last Updated: June 13, 2026*
