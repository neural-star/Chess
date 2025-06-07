from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..services.clock import ChessClock

router = APIRouter()
# ゲームセッション管理 (メモリ or Redis)
_games = {}  # game_id → { board, clock, move_stack }

@router.post("/create", response_model=schemas.GameCreate)
def create_game(req: schemas.CreateReq, db: Session = Depends(database.get_db)):
    game = models.Game(
        id=req.game_id, 
        white_id=req.user_id, 
        time_control=req.time_control
    )
    db.add(game); db.commit()
    # セッション側にも
    _games[req.game_id] = {
        "board": chess.Board(), 
        "clock": ChessClock(*parse_tc(req.time_control)),
        "stack": []
    }
    return { "game_id": req.game_id, "fen": "startpos" }

@router.post("/move", response_model=schemas.MoveRes)
def make_move(req: schemas.MoveReq):
    session = _games[req.game_id]
    board   = session["board"]
    if req.offer_draw:
        session["draw_offered"] = req.player_color
    if req.resign:
        board.clear()  # 投了扱い
    # UNDO
    if req.undo and session["stack"]:
        board.pop()
        session["stack"].pop()
    # 通常手
    move = chess.Move.from_uci(req.uci)
    board.push(move)
    session["stack"].append(move)
    session["clock"].switch()
    return { "fen": board.fen(), "times": session["clock"].get_times() }
