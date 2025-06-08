from .db import _conn
import pandas as pd

def user_stats(user):
    # 過去ゲームで user が white/black の勝率を算出
    df = pd.read_sql_query("""
      SELECT players, result FROM games
      WHERE result IS NOT NULL
    """, _conn)
    # players カラムは JSON 文字列
    df["players"] = df["players"].apply(json.loads)
    wins = losses = draws = 0
    total = 0
    for _, row in df.iterrows():
        p = row["players"]
        res = row["result"]
        if p.get("white")==user or p.get("black")==user:
            total += 1
            if (p.get("white")==user and res=="1-0") or (p.get("black")==user and res=="0-1"):
                wins += 1
            elif res=="1/2-1/2":
                draws += 1
            else:
                losses += 1
    return {"total": total, "wins": wins, "losses": losses, "draws": draws}

