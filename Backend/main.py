from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import json

from chatbot import process_query, speech_to_text

app = FastAPI()

# ─────────────────────────────────────────────
# CORS (Frontend connection)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schemes once
with open("schemes.json", encoding="utf-8") as f:
    schemes_data = json.load(f)


# ─────────────────────────────────────────────
# ROOT API
# ─────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "AI Scheme Assistant Backend Running 🚀"}


# ─────────────────────────────────────────────
# CHAT API (IMPORTANT)
# ─────────────────────────────────────────────
@app.post("/chat")
def chat(data: dict):
    user_input = data.get("message", "").strip()

    if not user_input:
        return {"reply": "Please enter a valid message."}

    try:
        response = process_query(user_input)
        return {"reply": response}

    except Exception as e:
        print("Error:", e)
        return {"reply": "Something went wrong. Please try again."}


# ─────────────────────────────────────────────
# VOICE API (OPTIONAL BUT GOOD)
# ─────────────────────────────────────────────
@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        text = speech_to_text(audio_bytes)
        response = process_query(text)

        return {
            "transcribed_text": text,
            "response": response
        }

    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# SCHEMES API (FOR CARDS UI)
# ─────────────────────────────────────────────
@app.get("/schemes")
def get_schemes():
    return schemes_data["schemes"]