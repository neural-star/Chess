import chess, chess.pgn
from stockfish import Stockfish
import io
import csv

STOCKFISH_PATH = "/usr/games/stockfish"

def run_batch_ai_vs_ai(level_w, level_b, num_games):
    stats = {"white_win":0, "black_win":0, "draw":0}
    detailed = []
    for i in range(num_games):
        board = chess.Board()
        sfw = Stockfish(path=STOCKFISH_PATH)
        sfb = Stockfish(path=STOCKFISH_PATH)
        sfw.set_skill_level(level_w)
        sfb.set_skill_level(level_b)
        while not board.is_game_over():
            mover = sfw if board.turn == chess.WHITE else sfb
            mover.set_fen_position(board.fen())
            mv = mover.get_best_move()
            board.push(chess.Move.from_uci(mv))
        res = board.result()
        stats["white_win"] += res == "1-0"
        stats["black_win"] += res == "0-1"
        stats["draw"]      += res == "1/2-1/2"
        detailed.append({"game": i+1, "result": res, "moves": board.fullmove_number})
    summary = f"White wins: {stats['white_win']}, Black wins: {stats['black_win']}, Draws: {stats['draw']}"
    # CSV 作成
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["game","result","moves"])
    writer.writeheader()
    writer.writerows(detailed)
    csv_data = output.getvalue()
    return summary, csv_data
