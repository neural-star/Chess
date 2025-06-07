from fastapi import FastAPI, WebSocket
from .routers import auth, pvp, ai, analysis, puzzles, matchmaking
from .database import init_db

app = FastAPI()

# DB 初期化
init_db()

# REST API ルーター
app.include_router(auth.router,    prefix="/auth",    tags=["auth"])
app.include_router(pvp.router,     prefix="/pvp",     tags=["pvp"])
app.include_router(ai.router,      prefix="/ai",      tags=["ai"])
app.include_router(analysis.router,prefix="/analysis",tags=["analysis"])
app.include_router(puzzles.router, prefix="/puzzles", tags=["puzzles"])
app.include_router(matchmaking.router,prefix="/match", tags=["matchmaking"])

# WebSocket エンドポイント (対局／チャット用)
@app.websocket("/ws/game/{game_id}")
async def game_ws(websocket: WebSocket, game_id: str):
    await websocket.accept()
    # …接続管理／メッセージブロードキャスト…

@app.websocket("/ws/chat/{game_id}")
async def chat_ws(websocket: WebSocket, game_id: str):
    await websocket.accept()
    # …チャットメッセージの送受信…
