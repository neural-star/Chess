import random
import chess
from .db import  # adjust import if needed
import chess.svg
from io import BytesIO
import cairosvg
from PIL import Image
from xml.dom import minidom

# サンプルパズル集
puzzles = [
    {
        "id": 1,
        "fen": "r1bqkbnr/ppp2ppp/2n5/3pp3/3P4/2N2N2/PPP1PPPP/R1BQKB1R w KQkq - 0 4",
        "solutions": ["d4e5"],
        "theme": "pawn tactics"
    },
    # ... 他の問題を追加
]

current_puzzle = None

def render_board(board, highlights=None, last_move=None):
    size = 350
    svg = chess.svg.board(board=board, size=size, coordinates=True)
    # 省略せずに SVG→PNG 変換ロジックを流用
    # （render_board_with_hints を移植するイメージ）
    # ...
    return board_image  # PIL.Image

def next_puzzle():
    global current_puzzle
    current_puzzle = random.choice(puzzles)
    board = chess.Board(current_puzzle["fen"])
    img = render_board(board)
    return img, f"Puzzle ID {current_puzzle['id']}：テーマ {current_puzzle['theme']}"

def check_puzzle_move(move_uci):
    board = chess.Board(current_puzzle["fen"])
    try:
        mv = chess.Move.from_uci(move_uci.strip())
        if mv not in board.legal_moves:
            return render_board(board), "⚠️ 合法手ではありません"
        if move_uci in current_puzzle["solutions"]:
            return render_board(board), "✅ 正解！"
        else:
            return render_board(board), "❌ 不正解。もう一度考えてみて！"
    except:
        return render_board(board), "⚠️ 入力エラー（例：e2e4）"
