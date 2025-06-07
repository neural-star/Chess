from pydantic import BaseModel
from typing import List, Optional, Dict

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    elo: int

# --- PvP API ---
class CreateReq(BaseModel):
    game_id: str
    time_control: str
    user_id: int

class GameCreate(BaseModel):
    game_id: str
    fen: str

class MoveReq(BaseModel):
    game_id: str
    uci: Optional[str]
    resign: Optional[bool] = False
    offer_draw: Optional[bool] = False
    undo: Optional[bool] = False
    player_color: str  # "white" or "black"

class MoveRes(BaseModel):
    fen: str
    times: Dict[str, int]

# --- Analysis ---
class AnalysisReq(BaseModel):
    moves: List[str]

# --- Puzzles ---
class PuzzleOut(BaseModel):
    fen: str
    solution: List[str]
