# HA! Healthcare AI - Deployment Guide

## Chat History Feature Implementation ✅

This guide covers the complete Chat History feature that has been implemented.

---

## What's New

### Backend Changes

1. **SQLite Database Integration**
   - `users` table for user management
   - `chat_history` table for storing conversations
   - Automatic database initialization on startup

2. **New API Endpoints**
   - `GET /chat/history/{phone}` - Get all chat sessions for a user
   - `GET /chat/session/{chat_id}` - Get messages from a specific chat
   - `DELETE /chat/session/{chat_id}` - Delete a chat session

3. **Enhanced Chat Endpoint**
   - `/chat` now accepts `user_phone` and `chat_id` parameters
   - Automatically saves user messages and AI responses to database

### Frontend Changes

1. **Chat History Sidebar**
   - Displays recent chat sessions
   - Shows message preview and timestamp
   - Click to load previous conversations
   - Delete button for each chat

2. **Session Management**
   - Each new chat creates a unique `chat_id`
   - "New Chat" button starts fresh session
   - Active chat highlighted in history

3. **UI Enhancements**
   - Gemini AI-inspired glassmorphism design
   - Smooth animations and transitions
   - Mobile-responsive history sidebar

---

## Local Testing

### 1. Start Backend

```bash
cd backend

# Activate virtual environment (if not already active)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Make sure .env file exists with GROQ_API_KEY
# If not, create it:
echo GROQ_API_KEY=your_groq_api_key_here > .env

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The database file `ha_healthcare.db` will be created automatically in the `backend` folder.

### 2. Update Frontend for Local Testing

Edit `frontend/js/app.js` and change:
```javascript
const API_BASE = "http://localhost:8000";
```

### 3. Serve Frontend

```bash
cd frontend
python -m http.server 3000
```

Open http://localhost:3000 in your browser.

### 4. Test the Feature

1. **Register/Login** - Use any name, phone, and location
2. **Start Chat** - Send a message to the AI
3. **Check History** - Your chat should appear in the sidebar
4. **New Chat** - Click "New Chat" to start a new session
5. **Load Chat** - Click on a previous chat to load it
6. **Delete Chat** - Hover over a chat and click the delete icon

---

## Deployment

### Backend Deployment (Render)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add chat history feature with SQLite"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to https://render.com
   - Connect your GitHub repository
   - Create a new Web Service
   - Select your repository
   - Configure:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables:** Add `GROQ_API_KEY`

3. **Database Persistence**
   - Render provides persistent disk storage
   - The SQLite database will persist across deployments
   - No additional configuration needed

### Frontend Deployment (Vercel)

1. **Update API_BASE**
   
   Edit `frontend/js/app.js`:
   ```javascript
   const API_BASE = "https://your-backend-url.onrender.com";
   ```

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Update API_BASE for production"
   git push origin main
   ```

3. **Deploy on Vercel**
   - Go to https://vercel.com
   - Import your GitHub repository
   - Configure:
     - **Root Directory:** `frontend`
     - **Framework Preset:** Other
   - Deploy

4. **Verify vercel.json**
   
   Make sure your `vercel.json` looks like this:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "frontend/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/",
         "dest": "/frontend/index.html"
       },
       {
         "src": "/(.*)",
         "dest": "/frontend/$1"
       }
     ]
   }
   ```

---

## Database Management

### View Database Contents

```bash
cd backend
sqlite3 ha_healthcare.db

# List all tables
.tables

# View users
SELECT * FROM users;

# View chat history
SELECT * FROM chat_history LIMIT 10;

# Count chats per user
SELECT user_phone, COUNT(DISTINCT chat_id) as chat_count 
FROM chat_history 
GROUP BY user_phone;

# Exit
.quit
```

### Backup Database

```bash
# Create backup
cp ha_healthcare.db ha_healthcare_backup_$(date +%Y%m%d).db

# Or export to SQL
sqlite3 ha_healthcare.db .dump > backup.sql
```

### Reset Database

```bash
# Delete database file (will be recreated on next startup)
rm ha_healthcare.db
```

---

## API Testing

### Test Chat History Endpoints

```bash
# Get chat history for a user
curl http://localhost:8000/chat/history/1234567890

# Get specific chat session
curl http://localhost:8000/chat/session/chat_1234567890_abc123

# Delete chat session
curl -X DELETE http://localhost:8000/chat/session/chat_1234567890_abc123

# Send chat message with history
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache",
    "username": "John",
    "user_phone": "1234567890",
    "chat_id": "chat_1234567890_abc123"
  }'
```

---

## Troubleshooting

### Database Not Created

**Problem:** `ha_healthcare.db` file not found

**Solution:**
- Make sure the backend is running
- Check file permissions in the backend folder
- The database is created automatically on first startup

### Chat History Not Loading

**Problem:** History sidebar shows "No chat history yet"

**Solution:**
- Check browser console for errors
- Verify `user_phone` is stored in localStorage
- Check if API_BASE is correct in `app.js`
- Test the API endpoint directly: `GET /chat/history/{phone}`

### Messages Not Saving

**Problem:** Chat works but history doesn't save

**Solution:**
- Verify you're logged in (phone number in localStorage)
- Check that `user_phone` and `chat_id` are being sent in chat requests
- Check backend logs for database errors
- Verify database tables exist: `sqlite3 ha_healthcare.db ".tables"`

### CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:**
- Backend CORS is set to allow all origins (`allow_origins=["*"]`)
- For production, update to specific origins:
  ```python
  allow_origins=["https://your-frontend.vercel.app"]
  ```

---

## Feature Checklist

- ✅ SQLite database with `users` and `chat_history` tables
- ✅ User registration saves to database
- ✅ Chat messages automatically saved to database
- ✅ Chat history sidebar in UI
- ✅ Load previous conversations
- ✅ Delete chat sessions
- ✅ New chat creates new session
- ✅ Active chat highlighting
- ✅ Mobile-responsive design
- ✅ Timestamp formatting (relative time)
- ✅ Message preview truncation
- ✅ Empty state handling
- ✅ Smooth animations

---

## Next Steps (Optional Enhancements)

1. **Search Chat History**
   - Add search bar to filter chats
   - Search by message content

2. **Chat Titles**
   - Auto-generate chat titles from first message
   - Allow users to rename chats

3. **Export Chats**
   - Download chat as PDF
   - Export to text file

4. **Chat Analytics**
   - Show total chats count
   - Most discussed topics
   - Chat frequency graph

5. **User Authentication**
   - Add password/PIN for security
   - JWT token-based auth
   - Session management

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review backend logs: `uvicorn main:app --reload --log-level debug`
- Check browser console for frontend errors
- Verify database contents with SQLite commands

---

**Implementation Complete! 🎉**

The Chat History feature is now fully functional and ready for deployment.
