from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "HA Backend Running Successfully 🚀"}

@app.post("/chat")
async def chat(data: dict):
    user_message = data.get("message")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": user_message,
            "stream": False
        }
    )

    result = response.json()
    return {"response": result["response"]}