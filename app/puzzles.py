import random
import chess
import chess.svg
from stockfish import Stockfish
from io import BytesIO
import cairosvg
from PIL import Image
from xml.dom import minidom
import json
from .app import STOCKFISH_PATH

with open("puzzle.json", "r", encoding="utf-8") as f:
    data = json.load(f)
puzzles = [data]

current_puzzle = None

def render_board(board: chess.Board,
                 hints_legal: list[int]=None,
                 hints_theoretical: list[int]=None,
                 last_move: chess.Move=None) -> Image.Image:
    """
    board → SVG → PNG → PIL.Image の変換を行い、
    必要に応じて合法手 (緑丸)、理論上の移動先 (青丸)、最後の手 (黄四角) をオーバーレイします。
    """
    size = 350
    svg_board = chess.svg.board(board=board, size=size, coordinates=True)
    square = size / 8
    margin = square * 0.5

    # SVG を DOM 解析
    doc = minidom.parseString(svg_board)
    svg = doc.documentElement

    # 合法手ヒント (緑丸)
    if hints_legal:
        for sq in hints_legal:
            f = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            cx = margin + f * square + square / 2
            cy = margin + r * square + square / 2
            circle = doc.createElement('circle')
            circle.setAttribute('cx', str(cx))
            circle.setAttribute('cy', str(cy))
            circle.setAttribute('r', str(square / 6))
            circle.setAttribute('fill', 'rgba(0, 255, 0, 0.5)')
            circle.setAttribute('stroke', 'black')
            circle.setAttribute('stroke-width', '1')
            svg.appendChild(circle)

    # 理論上の移動先ヒント (青丸)
    if hints_theoretical:
        for sq in hints_theoretical:
            f = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            cx = margin + f * square + square / 2
            cy = margin + r * square + square / 2
            circle = doc.createElement('circle')
            circle.setAttribute('cx', str(cx))
            circle.setAttribute('cy', str(cy))
            circle.setAttribute('r', str(square / 6))
            circle.setAttribute('fill', 'rgba(0, 0, 255, 0.3)')
            circle.setAttribute('stroke', 'black')
            circle.setAttribute('stroke-width', '1')
            svg.appendChild(circle)

    # 最後の手ハイライト (黄四角)
    if last_move:
        for sq in (last_move.from_square, last_move.to_square):
            f = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            rect = doc.createElement('rect')
            rect.setAttribute('x', str(margin + f * square))
            rect.setAttribute('y', str(margin + r * square))
            rect.setAttribute('width', str(square))
            rect.setAttribute('height', str(square))
            rect.setAttribute('fill', 'rgba(255, 255, 0, 0.3)')
            svg.appendChild(rect)

    # SVG → PNG に変換
    png = cairosvg.svg2png(bytestring=doc.toxml().encode('utf-8'))
    return Image.open(BytesIO(png))


def next_puzzle():
    """
    手動定義の puzzles からランダムに選択して出題。
    """
    global current_puzzle
    current_puzzle = random.choice(puzzles)
    board = chess.Board(current_puzzle["fen"])
    img = render_board(board)
    msg = f"Puzzle ID {current_puzzle['id']}：テーマ {current_puzzle['theme']}"
    return img, msg


def check_puzzle_move(move_uci: str):
    """
    ユーザーの解答手をチェックし、正解かどうかを返します。
    """
    board = chess.Board(current_puzzle["fen"])
    try:
        mv = chess.Move.from_uci(move_uci.strip())
    except:
        return render_board(board), "⚠️ 入力エラー（例：e2e4）"
    if mv not in board.legal_moves:
        return render_board(board), "⚠️ 合法手ではありません"
    if move_uci in current_puzzle["solutions"]:
        return render_board(board), "✅ 正解！"
    else:
        return render_board(board), "❌ 不正解。もう一度考えてみて！"


def generate_puzzle(moves_from_start: int = 20,
                    eval_threshold: float = 1.0) -> dict:
    """
    ランダムなオープニングから moves_from_start 手進めた局面を生成し、
    Stockfish で最善手を求め、その評価差が eval_threshold を
    超えていれば自動的にパズルとして返します。
    """
    sf = Stockfish(path=STOCKFISH_PATH)
    sf.set_depth(15)

    board = chess.Board()
    # ランダムに moves_from_start 手分だけ進める
    for _ in range(moves_from_start):
        legal = list(board.legal_moves)
        board.push(random.choice(legal))

    # 現在局面の最善手とその評価
    sf.set_fen_position(board.fen())
    best_move = sf.get_best_move()
    sf.set_fen_position(board.fen())
    info = sf.get_evaluation()  # {'type': 'cp', 'value': ...}
    base_eval = info['value']

    # 1手進めた後の評価
    board.push(chess.Move.from_uci(best_move))
    sf.set_fen_position(board.fen())
    info2 = sf.get_evaluation()
    next_eval = info2['value']

    # 評価差を cp 単位で計算（cp=centipawn）
    eval_diff = abs(next_eval - base_eval) / 100.0

    if eval_diff >= eval_threshold:
        # この局面をパズルとして登録
        pid = max([p["id"] for p in puzzles], default=0) + 1
        fen = board.fen()  # 最善手を指す前の局面 FEN
        puzzle = {
            "id": pid,
            "fen": board.transform(chess.Move.from_uci(best_move)).fen(),
            "solutions": [best_move],
            "theme": f"eval swing {eval_diff:.2f}"
        }
        puzzles.append(puzzle)
        return puzzle
    else:
        # 条件を満たさなければ再帰的に再生成
        return generate_puzzle(moves_from_start, eval_threshold)
