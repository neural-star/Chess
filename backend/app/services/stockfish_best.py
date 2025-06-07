import subprocess
from typing import Dict, Any

def best_eval_moves(fen: str, depth: int = 15) -> Dict[str, Any]:
    """
    指定した FEN 文字列に対して Stockfish で解析を行い、
    最善手と評価 (centipawn またはメイトスコア) を返します。

    :param fen: 分析対象の局面を表す FEN 文字列
    :param depth: 探索深度（省略時は 15）
    :return: {
        "best_move": str,        # 例: "e2e4"
        "evaluation": {          # 例: {"type": "cp", "value": 34} or {"type": "mate", "value": 2}
            "type": "cp"|"mate",
            "value": int
        }
    }
    """
    # Stockfish の実行ファイル名 or フルパスを指定
    engine_cmd = ["stockfish"]

    # プロセスを立ち上げ
    proc = subprocess.Popen(
        engine_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # Python 3.7+ では universal_newlines=True と同じ
    )

    # UCI モードに切り替え
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    # ここでは応答待ちを省略しますが、実装環境によっては "uciok" の待機を入れてください

    # 局面設定
    proc.stdin.write(f"position fen {fen}\n")
    proc.stdin.write(f"go depth {depth}\n")
    proc.stdin.flush()

    best_move = None
    evaluation = {"type": None, "value": None}

    # エンジンからの出力を逐次パース
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        # スコア情報をキャッチ
        if line.startswith("info") and "score" in line:
            tokens = line.split()
            # score の直後に type (cp/mate) と値が続く
            try:
                idx = tokens.index("score")
                score_type = tokens[idx + 1]
                score_val = int(tokens[idx + 2])
                evaluation = {"type": score_type, "value": score_val}
            except (ValueError, IndexError):
                pass
        # 最終的な bestmove
        if line.startswith("bestmove"):
            parts = line.split()
            if len(parts) >= 2:
                best_move = parts[1]
            break

    # プロセス終了
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.terminate()

    return {
        "best_move": best_move,
        "evaluation": evaluation
    }
