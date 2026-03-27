from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import json

from chatbot import process_query, speech_to_text

app = FastAPI()

# CORS (Frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schemes
with open("schemes.json", encoding="utf-8") as f:
    schemes_data = json.load(f)


# -----------------------
# ROOT API (for testing)
# -----------------------
@app.get("/")
def home():
    return {"message": "AI Scheme Assistant Backend Running 🚀"}


# -----------------------
# CHAT API
# -----------------------
@app.get("/chat")
def chat(query: str):
    try:
        response = process_query(query)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


# -----------------------
# VOICE API
# -----------------------
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


# -----------------------
# SCHEMES API
# -----------------------
@app.get("/schemes")
def get_schemes():
    return schemes_data["schemes"]