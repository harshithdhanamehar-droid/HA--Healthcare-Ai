@echo off
echo.
echo  HA! Healthcare AI - Starting Backend...
echo  ==========================================
echo.
cd backend
if not exist venv (
    echo  Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo  Installing dependencies...
pip install -r requirements.txt -q
echo.
echo  Starting FastAPI server on http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo  Make sure Ollama is running: ollama serve
echo  Make sure phi3 is pulled:   ollama pull phi3
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
