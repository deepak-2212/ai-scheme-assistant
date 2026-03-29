from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from chatbot import process_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Chat memory (session-based)
sessions = {}

@app.get("/")
def home():
    return {"message": "AI Scheme Assistant Running 🚀"}

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_input = data.get("message", "")
        session_id = data.get("session_id", "default")

        if session_id not in sessions:
            sessions[session_id] = []

        history = sessions[session_id]

        # store user message
        history.append({"role": "user", "content": user_input})

        result = process_query(user_input, history)

        # store bot response
        history.append({"role": "assistant", "content": result["text"]})

        return result

    except Exception as e:
        print("🔥 ERROR OCCURRED:", e)
        return {"text": "Something went wrong", "schemes": []}