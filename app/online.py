import uuid
import threading
import chess
from .db import save_game_state, load_game_state, list_active_games, add_chat_message, get_chat_log

games = {}  # in-memory キャッシュ（DBと同期）

def create_room(user_white, user_black=None):
    gid = str(uuid.uuid4())[:8]
    games[gid] = {
        "board": chess.Board(),
        "lock": threading.Lock(),
        "history": [],
        "players": {"white": user_white, "black": user_black},
    }
    save_game_state(gid, [chess.Board().fen()], games[gid]["players"])
    return gid

def join_room(gid, user, as_white=False):
    if gid not in games:
        return False
    with games[gid]["lock"]:
        role = "white" if as_white else "black"
        games[gid]["players"][role] = user
        save_game_state(gid,
                        [move.board().fen() for move in games[gid]["history"]],
                        games[gid]["players"])
    return True

def list_rooms():
    return list_active_games()

def make_move(gid, user, uci):
    entry = games.get(gid)
    if not entry:
        return None, "❌ 無効なゲームIDです"
    with entry["lock"]:
        board = entry["board"]
        mv = chess.Move.from_uci(uci.strip())
        if mv not in board.legal_moves:
            return board, "❌ 不正手です"
        board.push(mv)
        entry["history"].append(board.fen())
        # ゲーム終了時には DB に結果書き込み
        res = board.result() if board.is_game_over() else None
        save_game_state(gid, entry["history"], entry["players"], result=res)
        return board, f"✅ {res or '手を指しました'}"

def get_room_chat(gid):
    return get_chat_log(gid)

def post_room_chat(gid, user, text):
    add_chat_message(gid, user, text)
    return get_chat_log(gid)
