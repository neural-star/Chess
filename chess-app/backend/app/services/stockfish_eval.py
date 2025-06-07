import chess
from stockfish import Stockfish

STOCKFISH_PATH = "/usr/games/stockfish"

def eval_moves(moves: list[str], depth: int = 15) -> list[float]:
    """
    指し手リストから局面ごとの Stockfish の評価（ポーン換算）を返す.
    """
    sf = Stockfish(path=STOCKFISH_PATH, depth=depth)
    board = chess.Board()
    evals = [0.0]  # 初期局面を 0 としておく
    for uci in moves:
        board.push(chess.Move.from_uci(uci))
        sf.set_fen_position(board.fen())
        info = sf.get_evaluation()  # {'type':'cp','value':...} or mate
        if info["type"] == "cp":
            evals.append(info["value"] / 100.0)
        else:
            # チェックメイトまでの手数 → 大きな正負値で代替
            sign = 1 if info["value"] > 0 else -1
            evals.append(sign * (50 - abs(info["value"])))
    return evals