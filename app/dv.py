import sqlite3
import threading
import json
from datetime import datetime

_lock = threading.Lock()
_conn = sqlite3.connect("chess_app.db", check_same_thread=False)
_conn.row_factory = sqlite3.Row

def init_db():
    with _lock:
        c = _conn.cursor()
        # ゲーム情報
        c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            fen_history TEXT,
            players TEXT,
            result TEXT,
            created_at TEXT,
            finished_at TEXT
        )""")
        # チャットログ
        c.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            game_id TEXT,
            timestamp TEXT,
            user TEXT,
            message TEXT
        )""")
        _conn.commit()

def save_game_state(game_id, fen_history, players, result=None):
    with _lock:
        c = _conn.cursor()
        now = datetime.utcnow().isoformat()
        # upsert
        c.execute("""
        INSERT INTO games(id, fen_history, players, result, created_at)
          VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          fen_history=excluded.fen_history,
          players=excluded.players,
          result=excluded.result,
          finished_at=CASE WHEN excluded.result IS NOT NULL THEN ? ELSE finished_at END
        """, (
            game_id,
            json.dumps(fen_history),
            json.dumps(players),
            result,
            now,
            now
        ))
        _conn.commit()

def load_game_state(game_id):
    with _lock:
        c = _conn.cursor()
        c.execute("SELECT * FROM games WHERE id=?", (game_id,))
        row = c.fetchone()
        if not row:
            return None
        return {
            "fen_history": json.loads(row["fen_history"]),
            "players": json.loads(row["players"]),
            "result": row["result"]
        }

def list_active_games():
    with _lock:
        c = _conn.cursor()
        c.execute("SELECT id, players, result FROM games")
        rows = c.fetchall()
        return [
            {"id": r["id"], "players": json.loads(r["players"]), "result": r["result"]}
            for r in rows
        ]

def add_chat_message(game_id, user, message):
    with _lock:
        c = _conn.cursor()
        ts = datetime.utcnow().isoformat()
        c.execute("INSERT INTO chat(game_id, timestamp, user, message) VALUES(?,?,?,?)",
                  (game_id, ts, user, message))
        _conn.commit()

def get_chat_log(game_id):
    with _lock:
        c = _conn.cursor()
        c.execute("SELECT user, message, timestamp FROM chat WHERE game_id=? ORDER BY timestamp", (game_id,))
        return [{"user": r["user"], "message": r["message"], "timestamp": r["timestamp"]} for r in c.fetchall()]

# 初期化
init_db()
