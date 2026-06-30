# HA! Healthcare AI — Testing Checklist v3

## Pre-Testing Setup

- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file updated with GMAIL credentials (or blank for testing)
- [ ] SQLite database exists and initialized (`ha_healthcare.db`)
- [ ] Backend running on `http://127.0.0.1:8000`
- [ ] Frontend accessible (file:// or http://localhost:3000)

---

## Feature 1: Email Service

### 1.1 Email Sending (with credentials)

**Setup:**
- [ ] Configure `.env` with valid Gmail credentials
- [ ] Ensure `GMAIL_USER` is set
- [ ] Ensure `GMAIL_APP_PASSWORD` is set (16-character app password, NOT regular password)

**Test: Send Appointment Confirmation Email**
```
1. [ ] Login to frontend
2. [ ] Go to "Find Doctors"
3. [ ] Click "Book Appointment" on any doctor
4. [ ] Fill in: name, phone, date, time
5. [ ] Click "Confirm Booking"
6. EXPECTED: 
   - Appointment created successfully
   - Confirmation message displayed
   - Backend logs: "Email sent to..." (check console)
   - Check your email inbox (or spam folder)
7. [ ] Email received with appointment details
8. [ ] Email includes doctor name, date, time, location
```

**Test: Doctor Notification Email**
```
1. [ ] Same as above (book appointment)
2. EXPECTED:
   - Doctor receives separate email
   - Email includes patient details
   - Email includes appointment time and symptoms
```

**Database Verification:**
```sql
-- Run in SQLite
SELECT recipient, email_type, status, created_at 
FROM email_logs 
WHERE email_type = 'appointment_confirmation'
ORDER BY created_at DESC LIMIT 5;

Expected output:
- recipient: patient email (if available in system)
- email_type: 'appointment_confirmation'
- status: 'sent'
- created_at: recent timestamp
```

---

### 1.2 Email Failure Handling (simulate missing credentials)

**Setup:**
- [ ] Remove `GMAIL_USER` from `.env` (comment it out)
- [ ] Restart backend

**Test: Appointment without SMTP credentials**
```
1. [ ] Login to frontend
2. [ ] Go to "Find Doctors"
3. [ ] Book an appointment
4. EXPECTED:
   - Appointment created successfully
   - Backend logs warning: "Email disabled..."
   - No email sent
   - Application continues normally
5. [ ] Check database:
```

**Database Verification:**
```sql
SELECT recipient, email_type, status, error_message 
FROM email_logs 
WHERE status = 'skipped'
ORDER BY created_at DESC LIMIT 5;

Expected output:
- status: 'skipped'
- error_message: "GMAIL_USER or GMAIL_APP_PASSWORD not configured"
```

---

### 1.3 Email Logging Audit Trail

**Test: Verify all email attempts logged**
```sql
-- Count emails by type
SELECT email_type, COUNT(*) as total,
       SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
       SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
FROM email_logs
GROUP BY email_type;

Expected output: Rows for each email type sent
```

---

## Feature 2: Chat Session Management

### 2.1 Create Chat Session

**Test: New chat creates session entry**
```
1. [ ] Login to frontend
2. [ ] Go to "Chat" page
3. [ ] Type a message: "I have a headache"
4. [ ] Press Send
5. EXPECTED:
   - AI responds normally
   - Message persists
6. [ ] Go back to Chat page (refresh if needed)
7. EXPECTED:
   - "Recent Chats" sidebar shows your chat
   - Title shows: "I have a headache" (or first message preview)
   - Chat appears at top of list
```

**Database Verification:**
```sql
SELECT chat_id, title, preview, updated_at 
FROM chat_sessions 
WHERE user_phone = '9876543210'  -- replace with your phone
ORDER BY updated_at DESC;

Expected output: One or more chat sessions
```

---

### 2.2 Recent Chats Sorting

**Test: Most recent chat appears first**
```
1. [ ] Start 3 different conversations
   - Chat 1: "I have a cold"
   - Chat 2: "Anxiety symptoms"
   - Chat 3: "Sleep problems"
2. [ ] Send messages in random order:
   - Send message to Chat 1
   - Send message to Chat 2
   - Send message to Chat 3
   - Send another message to Chat 1
3. [ ] Look at "Recent Chats"
4. EXPECTED: Chat 1 appears at top (most recently updated)
```

**Database Verification:**
```sql
SELECT chat_id, title, updated_at 
FROM chat_sessions 
WHERE user_phone = '9876543210'
ORDER BY updated_at DESC;

Expected: Chat 1 should be first (most recent updated_at)
```

---

### 2.3 Load Previous Chat

**Test: Opening old chat loads all messages**
```
1. [ ] Start a new chat with message: "headache"
2. [ ] AI responds
3. [ ] Send another message: "it's been 3 days"
4. [ ] AI responds
5. [ ] Go to different page (Doctors, Appointments, etc.)
6. [ ] Go back to Chat
7. [ ] Click on your recent chat in sidebar
8. EXPECTED:
   - All 4 messages (2 from you, 2 from AI) load
   - Messages in correct order
   - No messages missing
9. [ ] Send a new message: "should I see a doctor?"
10. [ ] AI responds
11. EXPECTED: Now 6 total messages visible
```

---

## Feature 3: Recent Chats UI (No Overlap)

### 3.1 Desktop: Chat History Scrolling

**Test: Sidebar scrolls independently**
```
1. [ ] Create 10+ chats
2. [ ] Look at "Recent Chats" section in sidebar
3. [ ] Scroll within the chat history area
4. EXPECTED:
   - Chat list scrolls smoothly
   - Navigation menu (AI Chat, Symptom Checker, etc.) stays fixed
   - NO overlap between chat list and navigation
   - Scrollbar appears in chat section only
5. [ ] Scroll down to bottom chat
6. [ ] Scroll back up to top
7. EXPECTED: All chats visible, no cut-off content
```

---

### 3.2 Mobile: Sidebar Behavior

**Test: Mobile sidebar (window < 768px)**
```
1. [ ] Open browser DevTools (F12)
2. [ ] Set viewport to 375px × 667px (iPhone SE)
3. [ ] Refresh page
4. [ ] Look at hamburger menu
5. [ ] Click hamburger
6. EXPECTED: Sidebar slides in from left
7. [ ] Scroll within Recent Chats
8. EXPECTED:
   - Chat history scrolls independently
   - NO text cutoff
   - NO overlap with menu items
9. [ ] Click a chat
10. EXPECTED: Chat loads, sidebar closes
```

---

## Feature 4: Chat Operations

### 4.1 Rename Chat

**Test: User can rename chat**
```
1. [ ] Create a chat: "I have a cough"
2. [ ] Look for rename option (hover/right-click on chat)
3. [ ] Click rename
4. EXPECTED: Prompt dialog appears
5. [ ] Type new title: "My persistent cough"
6. [ ] Press OK
7. EXPECTED:
   - Chat renamed in sidebar
   - Title updated immediately
8. [ ] Refresh page
9. EXPECTED: Title persists
```

**Database Verification:**
```sql
SELECT chat_id, title 
FROM chat_sessions 
WHERE title LIKE '%persistent cough%';

Expected: Chat found with new title
```

---

### 4.2 Archive Chat

**Test: User can archive chats**
```
1. [ ] Create 2 chats
2. [ ] Archive the first one
3. EXPECTED:
   - Chat disappears from Recent list
   - Still visible in sidebar but grayed out (if implemented)
4. [ ] Check if "View Archived" option exists
5. [ ] If yes, click it
6. EXPECTED: Archived chat shown in separate section
7. [ ] Unarchive it
8. EXPECTED: Chat returns to Recent list
```

**Database Verification:**
```sql
SELECT chat_id, is_archived, title 
FROM chat_sessions 
WHERE user_phone = '9876543210'
ORDER BY is_archived DESC;

Expected: Active chats (is_archived=0) and archived chats (is_archived=1)
```

---

### 4.3 Delete Chat

**Test: User can delete chat**
```
1. [ ] Create a chat: "test delete"
2. [ ] Send a message
3. [ ] Look for delete option on chat
4. [ ] Click delete
5. EXPECTED: Confirmation dialog appears
6. [ ] Click OK to confirm
7. EXPECTED:
   - Chat removed from sidebar
   - New chat screen shown (welcome screen)
   - Chat list updated
8. [ ] Check that other chats still visible
9. EXPECTED: Other chats unaffected
```

**Database Verification:**
```sql
-- Verify chat_history and chat_sessions both deleted
SELECT COUNT(*) FROM chat_history WHERE chat_id = 'chat_to_delete';
SELECT COUNT(*) FROM chat_sessions WHERE chat_id = 'chat_to_delete';

Expected: Both return 0 (deleted)
```

---

## Feature 5: Chat Content Persistence

### 5.1 Refresh Doesn't Lose Data

**Test: Messages persist after page refresh**
```
1. [ ] Start a chat: "What is diabetes?"
2. [ ] AI responds with detailed explanation
3. [ ] Send follow-up: "What are the symptoms?"
4. [ ] AI responds
5. [ ] Press F5 (refresh page)
6. EXPECTED:
   - Chat loaded automatically (if chat_id remembered)
   - All 4 messages visible
   - No message loss
7. [ ] Scroll up/down through messages
8. EXPECTED: All messages intact
```

---

### 5.2 Session Switching

**Test: Switching between chats loads correct history**
```
1. [ ] Create Chat A: "headache" + response
2. [ ] Create Chat B: "fever" + response
3. [ ] Click Chat A in sidebar
4. EXPECTED:
   - Only Chat A messages visible (headache/response)
   - Chat B messages hidden
5. [ ] Click Chat B
6. EXPECTED:
   - Only Chat B messages visible (fever/response)
   - Chat A messages hidden
7. [ ] Click Chat A again
8. EXPECTED:
   - Chat A messages restored correctly
   - Message content unchanged
```

---

## Feature 6: Backward Compatibility

### 6.1 Existing Functionality Works

**Test: All existing features still work**
```
- [ ] Chat (AI responses) — Works normally
- [ ] Symptom Checker — Still responsive
- [ ] Doctor Booking — Appointments save
- [ ] Appointments page — Shows past appointments
- [ ] Emergency SOS — Emergency alerts work
- [ ] Login/Logout — Authentication works
- [ ] User profile — Location persists
```

---

### 6.2 No Breaking Changes

**Test: Frontend compatibility**
```
1. [ ] Old browsers/devices still work
2. [ ] API response format unchanged
3. [ ] Appointment data structure same
4. [ ] Doctor list displays correctly
5. [ ] User info persists in localStorage
```

---

## Feature 7: Error Recovery

### 7.1 Network Error Handling

**Test: Handle network disconnection gracefully**
```
1. [ ] Open DevTools Network tab
2. [ ] Throttle to "Offline"
3. [ ] Try to send chat message
4. EXPECTED:
   - Error message displayed
   - App doesn't crash
   - User can retry when online
5. [ ] Go back to "Normal" throttle
6. [ ] Try again
7. EXPECTED: Message sends successfully
```

---

### 7.2 Database Error Recovery

**Test: Handle DB errors gracefully**
```
1. [ ] Stop backend
2. [ ] Try to load chat history
3. EXPECTED:
   - Error message shown
   - App doesn't hang
4. [ ] Restart backend
5. [ ] Try again
6. EXPECTED: Data loads successfully
```

---

## Final Verification

### ✅ All Tests Passed?

- [ ] Email service sends/logs correctly
- [ ] Chat sessions created and persist
- [ ] Recent chats list displays properly
- [ ] No overlapping UI elements
- [ ] Chat operations (rename, archive, delete) work
- [ ] Mobile responsive
- [ ] Backward compatibility maintained
- [ ] Error handling graceful
- [ ] Database integrity (no corruption)

---

## Known Issues / Limitations

- [ ] Gmail may take 5-10 seconds to deliver emails
- [ ] Spam filters may block test emails
- [ ] Chat preview truncated to 80 characters
- [ ] Archive feature visual feedback minimal (can improve)
- [ ] No email resend feature yet (manual retry available)

---

## Sign-Off

**Tester Name:** _________________

**Date:** _________________

**Overall Status:**
- [ ] ALL TESTS PASSED
- [ ] TESTS PASSED WITH NOTES (see above)
- [ ] TESTS FAILED - BLOCKERS FOUND

**Comments:**

_____________________________________________

_____________________________________________

_____________________________________________

---

**Test Environment:**
- OS: Windows 10/11 or Linux/Mac
- Browser: Chrome, Firefox, Safari, Edge
- Backend: Python 3.8+
- Database: SQLite 3
- Email: Gmail SMTP

