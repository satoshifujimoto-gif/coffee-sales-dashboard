"""Minimal AI chat backend for the coffee sales dashboard.

Exposes POST /api/chat, which forwards the user's message to OpenAI and
returns the reply. The OpenAI API key is read from the environment (via a
local .env file) and never sent to, or accepted from, the frontend.

Setup:
    pip install -r requirements.txt
    copy .env.example to .env and fill in OPENAI_API_KEY

Run:
    python chat_backend.py
Then it listens on:
    http://127.0.0.1:8001
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

_client = None
if OPENAI_API_KEY:
    from openai import OpenAI
    _client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "あなたはコーヒー売上ダッシュボードのアシスタントです。"
    "ユーザーの質問に日本語で簡潔に答えてください。"
)

app = FastAPI(title="Coffee Dashboard Chat Backend")

# Local dev tool: any origin may call this (the dashboard can be opened as a
# plain file:// page too, which has no fixed origin to allow explicitly).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def health():
    return {"status": "ok", "configured": _client is not None}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        return ChatResponse(reply="質問を入力してください。")

    if _client is None:
        return ChatResponse(
            reply="サーバーに OPENAI_API_KEY が設定されていません。.env を確認してください。"
        )

    try:
        completion = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        reply = completion.choices[0].message.content or "(空の応答でした)"
    except Exception as e:
        reply = f"AIへの問い合わせに失敗しました: {e}"

    return ChatResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
