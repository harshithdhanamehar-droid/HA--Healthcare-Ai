# HA! Healthcare AI — API Reference v3

## Email Service Endpoints

### POST /appointments/book
**Updated** — Now sends emails automatically

```json
POST /appointments/book
{
  "patient_name": "John Doe",
  "patient_phone": "9876543210",
  "patient_location": "Hyderabad",
  "doctor_id": "d001",
  "date": "2026-06-20",
  "time_slot": "10:00 AM",
  "reason": "Regular checkup"
}

Response:
{
  "success": true,
  "appointment": {
    "id": "APTABC123",
    "patient_name": "John Doe",
    "doctor_name": "Dr. Priya Sharma",
    "specialty": "General Physician",
    "date": "2026-06-20",
    "time_slot": "10:00 AM",
    "fee": 500,
    "status": "pending"
  },
  "message": "Appointment booked with Dr. Priya Sharma..."
}
```

**Emails Sent:**
1. Confirmation → Patient email (if available)
2. Notification → Doctor email (if available)

---

## Chat Session Management Endpoints

### GET /chat/history/{phone}
Get recent active chats (most recent first)

```
GET /chat/history/9876543210

Response:
{
  "sessions": [
    {
      "chat_id": "chat_1718281234_abc123def",
      "title": "Headache and fever consultation",
      "preview": "I have a headache and fever...",
      "created_at": "2026-06-13T10:30:00",
      "updated_at": "2026-06-13T14:45:00"
    }
  ],
  "count": 1
}
```

**Notes:**
- Excludes archived chats
- Sorted by `updated_at DESC` (most recent first)
- Limit: 50 chats per user
- Preview automatically truncated to 60 characters

---

### GET /chat/session/{chat_id}
Load all messages from a specific chat

```
GET /chat/session/chat_1718281234_abc123def

Response:
{
  "chat_id": "chat_1718281234_abc123def",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "message": "I have a headache and fever",
      "created_at": "2026-06-13T10:30:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "message": "Based on your symptoms...",
      "created_at": "2026-06-13T10:31:00"
    }
  ],
  "count": 2
}
```

---

### DELETE /chat/session/{chat_id}
Delete a chat and all its messages

```
DELETE /chat/session/chat_1718281234_abc123def

Response:
{
  "success": true,
  "message": "Chat session deleted successfully"
}
```

**Note:** Deletes from both `chat_history` and `chat_sessions` tables

---

### PUT /chat/session/{chat_id}/rename
Rename a chat session

```json
PUT /chat/session/chat_1718281234_abc123def/rename
{
  "title": "My Allergy Symptoms"
}

Response:
{
  "success": true,
  "message": "Chat renamed successfully",
  "title": "My Allergy Symptoms"
}
```

**Validation:**
- Title cannot be empty
- Whitespace trimmed automatically
- Returns 404 if chat not found

---

### PUT /chat/session/{chat_id}/archive
Toggle archive status of a chat

```json
PUT /chat/session/chat_1718281234_abc123def/archive
{}

Response:
{
  "success": true,
  "message": "Chat archived successfully",
  "is_archived": true
}
```

**Behavior:**
- Toggle: unarchived → archived OR archived → unarchived
- Archived chats excluded from `GET /chat/history`
- Can be retrieved via `GET /chat/archived/{phone}`
- Archived status persists in `chat_sessions.is_archived` column

---

### GET /chat/archived/{phone}
Get all archived chats for a user

```
GET /chat/archived/9876543210

Response:
{
  "sessions": [
    {
      "chat_id": "chat_old_...",
      "title": "Old archived chat",
      "preview": "This was from last month...",
      "created_at": "2026-05-15T...",
      "updated_at": "2026-05-20T..."
    }
  ],
  "count": 3
}
```

---

## Email Logging & Audit

### Query email_logs table (Database)

**See all email attempts:**
```sql
SELECT recipient, email_type, status, error_message, created_at 
FROM email_logs 
ORDER BY created_at DESC 
LIMIT 20;
```

**Filter by status:**
```sql
-- All successful emails
SELECT * FROM email_logs WHERE status = 'sent';

-- All failed attempts
SELECT * FROM email_logs WHERE status = 'failed';

-- Skipped (credentials missing)
SELECT * FROM email_logs WHERE status = 'skipped';
```

**Filter by type:**
```sql
-- All appointment confirmations
SELECT * FROM email_logs WHERE email_type = 'appointment_confirmation';

-- All doctor notifications
SELECT * FROM email_logs WHERE email_type = 'doctor_notification';

-- OTP emails
SELECT * FROM email_logs WHERE email_type = 'otp_email';
```

**Email statistics:**
```sql
SELECT email_type, status, COUNT(*) as count 
FROM email_logs 
GROUP BY email_type, status;
```

---

## Frontend Helper Functions

### JavaScript API Functions (app.js)

```javascript
// POST request
await apiPost('/appointments/book', { ... })

// GET request
await apiGet('/chat/history/9876543210')

// PUT request (NEW)
await apiPut('/chat/session/chat_id/rename', { title: '...' })

// DELETE request
await apiDelete('/chat/session/chat_id')
```

### Chat Management Functions (chat.js)

```javascript
// Search chats
searchChats('headache')

// Rename chat (with prompt dialog)
renameChat('chat_id', event)

// Archive chat (toggle)
archiveChat('chat_id', event)
```

---

## Configuration Reference

### Environment Variables (.env)

```env
# Gmail SMTP Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Example (NOT real credentials)
GMAIL_USER=myapp@gmail.com
GMAIL_APP_PASSWORD=qwer tyui asdf ghjk
```

### Setup Gmail App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and your device type
3. Copy 16-character password
4. Paste into `.env` as `GMAIL_APP_PASSWORD`

### Error Handling

**If credentials missing:**
```
⚠️ Email disabled: GMAIL_USER or GMAIL_APP_PASSWORD not configured
```
- Appointment still created
- Email marked as "skipped" in logs
- Application continues normally

**If SMTP fails:**
```
❌ Email send failed to user@example.com: Connection timeout
```
- Error logged to database
- Appointment still created
- User can retry manually or admin can resend

---

## Database Schema

### email_logs table

```sql
CREATE TABLE email_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient        TEXT NOT NULL,           -- email address
    email_type       TEXT NOT NULL,           -- 'appointment_confirmation', 'otp_email', etc.
    subject          TEXT,                    -- email subject
    status           TEXT NOT NULL,           -- 'sent', 'failed', 'skipped'
    error_message    TEXT,                    -- error details if failed
    created_at       TEXT NOT NULL            -- ISO 8601 timestamp
)
```

### chat_sessions table

```sql
CREATE TABLE chat_sessions (
    chat_id          TEXT PRIMARY KEY,        -- unique chat ID
    user_phone       TEXT NOT NULL,           -- patient phone number
    title            TEXT,                    -- user-provided or auto-generated
    preview          TEXT,                    -- first message preview (60 chars)
    is_archived      BOOLEAN DEFAULT 0,       -- 0 = active, 1 = archived
    created_at       TEXT NOT NULL,           -- when chat created
    updated_at       TEXT NOT NULL,           -- when last message added
    FOREIGN KEY (user_phone) REFERENCES users(phone)
)
```

---

## Status Codes

| Code | Meaning | Scenario |
|------|---------|----------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid title (empty) |
| 404 | Not Found | Chat/doctor not found |
| 409 | Conflict | Duplicate appointment ID |
| 500 | Server Error | Database error |

---

## Example Workflows

### Workflow 1: Book Appointment & Receive Confirmation
```javascript
1. User selects doctor and date
2. Frontend: POST /appointments/book
3. Backend:
   - Creates appointment in DB
   - Sends confirmation email
   - Sends doctor notification
4. User receives email confirmation
```

### Workflow 2: Manage Chat Sessions
```javascript
1. User opens chat page
2. Frontend: GET /chat/history/{phone}
3. Shows recent chats, sorted by activity
4. User clicks rename icon
5. Frontend: PUT /chat/session/{id}/rename
6. User sees updated title
7. User clicks archive icon
8. Frontend: PUT /chat/session/{id}/archive
9. Chat moves to archived list
```

### Workflow 3: Debug Email Issues
```sql
1. User reports not receiving email
2. Query: SELECT * FROM email_logs 
          WHERE recipient = 'user@example.com' 
          ORDER BY created_at DESC LIMIT 5
3. Check status: 'sent', 'failed', or 'skipped'
4. If 'failed': read error_message
5. If 'sent': email was sent (check spam folder)
6. If 'skipped': GMAIL credentials not configured
```

---

## Notes for Developers

### Non-blocking Email
- Email errors do NOT block appointment creation
- All SMTP failures are logged to database
- Admins can review failures and resend if needed

### Chat Session Persistence
- Chat titles/archives persist across sessions
- Recent activity updates automatically
- No manual cache invalidation needed

### API Consistency
- All endpoints return JSON
- All timestamps in ISO 8601 format
- All errors include descriptive message in `detail` field

---

**Last Updated:** June 13, 2026
