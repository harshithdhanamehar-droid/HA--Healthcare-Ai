# Git Commands for Deployment

## Quick Deployment Guide

### 1. Check Current Status
```bash
git status
```

### 2. Add All Changes
```bash
git add .
```

### 3. Commit Changes
```bash
git commit -m "Add Chat History feature with SQLite database

- Implement SQLite database with users and chat_history tables
- Add chat history sidebar with load/delete functionality
- Create 3 new API endpoints for chat history management
- Update UI with Gemini-inspired glassmorphism design
- Add comprehensive documentation and deployment guide"
```

### 4. Push to GitHub
```bash
git push origin main
```

---

## If You Need to Initialize Git (First Time)

```bash
# Initialize repository
git init

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/yourusername/HA-Healthcare-AI.git

# Add all files
git add .

# First commit
git commit -m "Initial commit with Chat History feature"

# Push to GitHub
git push -u origin main
```

---

## Check What Changed

### See modified files
```bash
git status
```

### See detailed changes
```bash
git diff
```

### See changes in specific file
```bash
git diff backend/main.py
```

---

## Undo Changes (If Needed)

### Undo uncommitted changes in a file
```bash
git checkout -- filename
```

### Undo all uncommitted changes
```bash
git reset --hard
```

### Undo last commit (keep changes)
```bash
git reset --soft HEAD~1
```

---

## After Pushing to GitHub

### Backend Deployment (Render)
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** ha-healthcare-ai
   - **Branch:** main
   - **Root Directory:** (leave empty)
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:**
     - `GROQ_API_KEY` = your_groq_api_key_here
5. Click "Create Web Service"

### Frontend Deployment (Vercel)
1. Update `frontend/js/app.js`:
   ```javascript
   const API_BASE = "https://your-backend-url.onrender.com";
   ```
2. Commit and push:
   ```bash
   git add frontend/js/app.js
   git commit -m "Update API_BASE for production"
   git push origin main
   ```
3. Go to https://vercel.com
4. Click "Add New..." → "Project"
5. Import your GitHub repository
6. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Other
7. Click "Deploy"

---

## Verify Deployment

### Test Backend
```bash
# Check health
curl https://your-backend-url.onrender.com/health

# Test chat history (replace phone number)
curl https://your-backend-url.onrender.com/chat/history/1234567890
```

### Test Frontend
1. Open your Vercel URL in browser
2. Register/Login
3. Send a chat message
4. Check if history appears in sidebar
5. Try loading a previous chat
6. Try deleting a chat

---

## Common Issues

### Issue: "fatal: not a git repository"
**Solution:** Run `git init` first

### Issue: "remote origin already exists"
**Solution:** 
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/repo.git
```

### Issue: "failed to push some refs"
**Solution:**
```bash
git pull origin main --rebase
git push origin main
```

### Issue: Backend not starting on Render
**Solution:** Check these:
- Build command is correct
- Start command includes `cd backend`
- `GROQ_API_KEY` environment variable is set
- Check Render logs for errors

### Issue: Frontend can't connect to backend
**Solution:**
- Verify `API_BASE` in `app.js` matches your Render URL
- Check CORS settings in `backend/main.py`
- Check browser console for errors

---

## Files Changed in This Implementation

```
Modified:
- backend/main.py
- frontend/chat.html
- frontend/js/chat.js
- frontend/css/chat.css
- README.md

Created:
- DEPLOYMENT.md
- CHAT_HISTORY_SUMMARY.md
- GIT_COMMANDS.md
```

---

## Quick Reference

```bash
# See what changed
git status

# Add everything
git add .

# Commit
git commit -m "Your message"

# Push
git push origin main

# Pull latest
git pull origin main

# View commit history
git log --oneline

# Create new branch
git checkout -b feature-name

# Switch branch
git checkout main
```

---

**Ready to deploy! 🚀**
