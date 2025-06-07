from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Game
from ..services.elo import update_ratings
import uuid

router = APIRouter()
_match_queue: list[dict] = []  # {user_id, skill, time_control}

@router.post("/join")
def join_queue(user_id: int, skill: int, time_control: str,
               db: Session = Depends(get_db)):
    # キューに追加
    _match_queue.append({
        "user_id": user_id,
        "skill": skill,
        "time_control": time_control
    })
    # 簡易マッチング：スキル差 ≤100 なら即マッチ
    for opponent in _match_queue:
        if opponent["user_id"] != user_id and abs(opponent["skill"] - skill) <= 100:
            # 相手発見
            _match_queue.remove(opponent)
            _match_queue.remove({"user_id": user_id, " skill": skill, "time_control": time_control})
            game_id = str(uuid.uuid4())
            # DB に Game レコード作成
            game = Game(id=game_id,
                        white_id=user_id,
                        black_id=opponent["user_id"],
                        time_control=time_control)
            db.add(game)
            db.commit()
            return {"game_id": game_id}
    return {"status": "waiting"}
