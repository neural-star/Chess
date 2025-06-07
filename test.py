import uuid
import threading
import chess
import chess.svg
from io import BytesIO
import cairosvg
from PIL import Image
from xml.dom import minidom
from stockfish import Stockfish
import gradio as gr
import chess.pgn

# Stockfish の実行ファイルパス
STOCKFISH_PATH = "/usr/games/stockfish"

def render_board_with_hints(board, hints_legal=None, hints_theoretical=None, last_move=None):
    """
    board → SVG → PNG → PIL.Image
      hints_legal: 合法手リスト(緑丸)
      hints_theoretical: 理論上の潜在移動先リスト(青丸)
      last_move: chess.Move 最後の手(黄四角)
    """
    size = 350
    svg_board = chess.svg.board(board=board, size=size, coordinates=True)
    square = size / 8
    margin = square * 0.5

    doc = minidom.parseString(svg_board)
    svg = doc.documentElement

    # 合法手ヒント (緑)
    if hints_legal:
        for sq in hints_legal:
            f = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            cx = margin + f * square + square/2
            cy = margin + r * square + square/2
            circle = doc.createElement('circle')
            circle.setAttribute('cx', str(cx))
            circle.setAttribute('cy', str(cy))
            circle.setAttribute('r', str(square/6))
            circle.setAttribute('fill', 'rgba(0, 255, 0, 0.5)')
            circle.setAttribute('stroke', 'black')
            circle.setAttribute('stroke-width', '1')
            svg.appendChild(circle)

    # 理論上の移動先ヒント (青)
    if hints_theoretical:
        for sq in hints_theoretical:
            f = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            cx = margin + f * square + square/2
            cy = margin + r * square + square/2
            circle = doc.createElement('circle')
            circle.setAttribute('cx', str(cx))
            circle.setAttribute('cy', str(cy))
            circle.setAttribute('r', str(square/6))
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

    png = cairosvg.svg2png(bytestring=doc.toxml().encode('utf-8'))
    return Image.open(BytesIO(png))


# ─── グローバルステート ───
board = chess.Board()
last_move = None
move_history = []
stockfish = Stockfish(path=STOCKFISH_PATH)
stockfish.set_skill_level(3)

ai_board = chess.Board()
games = {}  # game_id → {"board": Board(), "lock": Lock(), "history": []}


def update_history(history_list):
    """手番履歴(UCIリスト)から PGN ゲームオブジェクトを生成"""
    game = chess.pgn.Game()
    node = game
    for uci in history_list:
        node = node.add_main_variation(chess.Move.from_uci(uci))
    return game


# ─── あなた vs AI ───
def make_move(move_uci, ai_skill):
    global board, stockfish, last_move, move_history
    if board.is_game_over():
        return render_board_with_hints(board, last_move=last_move), f"✅ ゲーム終了: {board.result()}", move_history

    try:
        mv = chess.Move.from_uci(move_uci.strip())
        if mv in board.legal_moves:
            board.push(mv)
            last_move = mv
            move_history.append(move_uci.strip())
            # AI の手
            stockfish.set_skill_level(int(ai_skill))
            stockfish.set_fen_position(board.fen())
            ai_uci = stockfish.get_best_move()
            mv2 = chess.Move.from_uci(ai_uci)
            board.push(mv2)
            last_move = mv2
            move_history.append(ai_uci)

            status = f"✅ 結果: {board.result()}" if board.is_game_over() else "AI が指しました。あなたの番です。"
            return render_board_with_hints(board, last_move=last_move), status, move_history
        else:
            return render_board_with_hints(board, last_move=last_move), "❌ 不正な手です。", move_history
    except:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 入力エラー（例：e2e4）", move_history


def help_move(square_uci):
    global board, last_move
    sq = square_uci.strip().lower()
    if len(sq) != 2:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 2文字で入力（例：e2）"
    try:
        sqi = chess.parse_square(sq)
    except:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 無効マス（a1～h8）"

    piece = board.piece_at(sqi)
    if piece is None:
        return render_board_with_hints(board, last_move=last_move), f"⚠️ {sq} に駒がありません"

    # 合法手
    moves_legal = [m.to_square for m in board.legal_moves if m.from_square == sqi]

    # 理論上の移動先
    moves_theo = []
    pt = piece.piece_type

    # スライダー系（Bishop, Rook, Queen）
    dirs = []
    if pt in (chess.BISHOP, chess.QUEEN):
        dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
    if pt in (chess.ROOK, chess.QUEEN):
        dirs += [(1,0),(-1,0),(0,1),(0,-1)]
    for dx, dy in dirs:
        f0 = chess.square_file(sqi)
        r0 = chess.square_rank(sqi)
        f, r = f0+dx, r0+dy
        while 0 <= f < 8 and 0 <= r < 8:
            moves_theo.append(chess.square(f, r))
            f += dx; r += dy

    # ナイト
    if pt == chess.KNIGHT:
        for df, dr in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
            f0 = chess.square_file(sqi) + df
            r0 = chess.square_rank(sqi) + dr
            if 0 <= f0 < 8 and 0 <= r0 < 8:
                moves_theo.append(chess.square(f0, r0))

    # キング
    if pt == chess.KING:
        for df in (-1,0,1):
            for dr in (-1,0,1):
                if df == 0 and dr == 0: continue
                f0 = chess.square_file(sqi) + df
                r0 = chess.square_rank(sqi) + dr
                if 0 <= f0 < 8 and 0 <= r0 < 8:
                    moves_theo.append(chess.square(f0, r0))

    # ポーン (一歩・初期二歩)
    if pt == chess.PAWN:
        color = piece.color
        direction = 1 if color == chess.WHITE else -1
        f0 = chess.square_file(sqi)
        r0 = chess.square_rank(sqi)
        # 一歩
        if 0 <= r0 + direction < 8:
            moves_theo.append(chess.square(f0, r0 + direction))
        # 二歩 (初期ランク)
        if (color == chess.WHITE and r0 == 1) or (color == chess.BLACK and r0 == 6):
            moves_theo.append(chess.square(f0, r0 + 2*direction))

    return (
        render_board_with_hints(
            board,
            hints_legal=moves_legal,
            hints_theoretical=list(set(moves_theo)),
            last_move=last_move
        ),
        f"✅ {sq} のヒント表示 (緑:合法手, 青:理論上)"
    )


def undo_move():
    global board, last_move, move_history
    if len(move_history) >= 2:
        board.pop(); board.pop()
        move_history = move_history[:-2]
        last_move = chess.Move.from_uci(move_history[-1]) if move_history else None
        return render_board_with_hints(board, last_move=last_move), "♻️ 1手戻しました", move_history
    return render_board_with_hints(board, last_move=last_move), "⚠️ これ以上戻せません", move_history


def reset_board():
    global board, stockfish, last_move, move_history
    board = chess.Board()
    stockfish = Stockfish(path=STOCKFISH_PATH)
    stockfish.set_skill_level(3)
    last_move = None
    move_history = []
    return render_board_with_hints(board), "🔄 新しいゲームを開始しました。あなたが先手です。", move_history


def download_pgn(history_list):
    game = update_history(history_list)
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)


# ─── AI vs AI ───
def reset_ai_vs_ai():
    global ai_board
    ai_board = chess.Board()
    return render_board_with_hints(ai_board), "🤖 AI対AIモードを開始しました。"


def ai_vs_ai_step(skill_white, skill_black):
    global ai_board
    if ai_board.is_game_over():
        return render_board_with_hints(ai_board), f"✅ ゲーム終了: {ai_board.result()}"
    sfw = Stockfish(path=STOCKFISH_PATH); sfw.set_skill_level(int(skill_white))
    sfb = Stockfish(path=STOCKFISH_PATH); sfb.set_skill_level(int(skill_black))
    sfw.set_fen_position(ai_board.fen()); sfb.set_fen_position(ai_board.fen())
    mv = sfw.get_best_move() if ai_board.turn == chess.WHITE else sfb.get_best_move()
    ai_board.push(chess.Move.from_uci(mv))
    return render_board_with_hints(ai_board), f"現在の手番: {'白' if ai_board.turn else '黒'}"


# ─── プレイヤー vs プレイヤー ───
def create_game():
    gid = str(uuid.uuid4())[:8]
    games[gid] = {"board": chess.Board(), "lock": threading.Lock(), "history": []}
    return gid, render_board_with_hints(games[gid]["board"]), f"🎉 ゲーム作成完了！ID: {gid}"


def join_game(gid):
    if gid in games:
        return render_board_with_hints(games[gid]["board"]), f"✅ ゲーム {gid} に参加しました。"
    return render_board_with_hints(chess.Board()), "❌ 無効なゲームIDです"


def pvp_move(gid, move_uci):
    if gid not in games:
        return render_board_with_hints(chess.Board()), "❌ 無効なゲームIDです"
    entry = games[gid]
    with entry["lock"]:
        try:
            mv = chess.Move.from_uci(move_uci.strip())
            if mv in entry["board"].legal_moves:
                entry["board"].push(mv)
                entry["history"].append(move_uci.strip())
                if entry["board"].is_game_over():
                    return render_board_with_hints(entry["board"]), f"✅ 結果: {entry['board'].result()}"
                return render_board_with_hints(entry["board"]), f"👍 合法手：{move_uci}"
            return render_board_with_hints(entry["board"]), "❌ 不正手です。"
        except:
            return render_board_with_hints(entry["board"]), "⚠️ 入力エラー（例：e2e4）"


def pvp_reset(gid):
    if gid in games:
        with games[gid]["lock"]:
            games[gid]["board"] = chess.Board()
            games[gid]["history"] = []
        return render_board_with_hints(games[gid]["board"]), "🔄 リセットしました"
    return render_board_with_hints(chess.Board()), "❌ 無効なゲームIDです"


def pvp_download_pgn(gid):
    if gid in games:
        game = update_history(games[gid]["history"])
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return game.accept(exporter)
    return ""


# ─── Gradio UI ───
with gr.Blocks() as app:
    gr.Markdown("## ♟️ グローバルチェスアプリ (Help統合版)")

    with gr.Tabs():

        # あなた vs AI
        with gr.TabItem("あなた vs AI"):
            with gr.Row():
                with gr.Column(scale=3):
                    img_h     = gr.Image(value=render_board_with_hints(board), label="盤面", type="pil")
                    status_h  = gr.Textbox("あなたの番です。", label="状況", interactive=False)
                    history_h = gr.Textbox(label="手番履歴 (PGN)", interactive=False)
                    btn_dl_h  = gr.Button("PGNダウンロード")
                with gr.Column(scale=1):
                    inp_h     = gr.Textbox(label="手またはHelp対象 (例: e2 または e2e4)")
                    btn_h     = gr.Button("指す")
                    btn_help  = gr.Button("Help")
                    btn_undo  = gr.Button("1手戻す")
                    slider_ai = gr.Slider(0, 20, value=3, step=1, label="AIスキル")
                    btn_rst_h = gr.Button("リセット")

            btn_h.click(make_move, [inp_h, slider_ai], [img_h, status_h, history_h]) \
                 .then(lambda: "", None, inp_h)
            btn_help.click(help_move, [inp_h], [img_h, status_h]) \
                    .then(lambda: "", None, inp_h)
            btn_undo.click(undo_move, None, [img_h, status_h, history_h])
            btn_rst_h.click(reset_board, None, [img_h, status_h, history_h])
            btn_dl_h.click(download_pgn, history_h, None)

        # AI vs AI
        with gr.TabItem("AI vs AI"):
            img_ai    = gr.Image(value=render_board_with_hints(ai_board), label="盤面", type="pil")
            status_ai = gr.Textbox("AI vs AIモード開始", label="状況", interactive=False)
            sw        = gr.Slider(0, 20, value=3, step=1, label="白AIスキル")
            sb        = gr.Slider(0, 20, value=3, step=1, label="黒AIスキル")
            btn_step  = gr.Button("1手進める")
            btn_rst_ai= gr.Button("リセット")

            btn_step.click(ai_vs_ai_step, [sw, sb], [img_ai, status_ai])
            btn_rst_ai.click(reset_ai_vs_ai, None, [img_ai, status_ai])

        # プレイヤー vs プレイヤー
        with gr.TabItem("PvP"):
            with gr.Row():
                with gr.Column(scale=3):
                    gid_box   = gr.Textbox(label="ゲームID")
                    img_pvp   = gr.Image(value=render_board_with_hints(chess.Board()), label="盤面", type="pil")
                    status_p  = gr.Textbox(label="状況", interactive=False)
                    history_p = gr.Textbox(label="手番履歴 (PGN)", interactive=False)
                    btn_dl_p  = gr.Button("PGNダウンロード")
                with gr.Column(scale=1):
                    btn_cre   = gr.Button("ゲーム作成")
                    btn_join  = gr.Button("ゲーム参加")
                    inp_pvp   = gr.Textbox(label="手 (例：e2e4)")
                    btn_pvp   = gr.Button("指す")
                    btn_rst   = gr.Button("リセット")

            btn_cre.click(create_game, None, [gid_box, img_pvp, status_p])
            btn_join.click(join_game, [gid_box], [img_pvp, status_p])
            btn_pvp.click(pvp_move, [gid_box, inp_pvp], [img_pvp, status_p]) \
                   .then(lambda: "", None, inp_pvp)
            btn_rst.click(pvp_reset, [gid_box], [img_pvp, status_p])
            btn_dl_p.click(pvp_download_pgn, gid_box, None)

            timer = gr.Timer(1, active=True)
            timer.tick(
                fn=lambda g: render_board_with_hints(games.get(g, {}).get("board", chess.Board())),
                inputs=[gid_box],
                outputs=[img_pvp]
            )

    app.launch()
