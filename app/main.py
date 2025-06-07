import uuid
import threading
import time
import sqlite3
import json
import io

import chess
import chess.svg
import chess.pgn
from io import BytesIO
import cairosvg
from PIL import Image
from xml.dom import minidom
from stockfish import Stockfish
import gradio as gr

# ─── DB 初期化 ─────────────────────────────────────────
conn = sqlite3.connect("app/users.db", check_same_thread=False)
c = conn.cursor()
# ユーザ成績テーブル
c.execute("""
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  draws INTEGER DEFAULT 0
)
""")
# オンライン対戦テーブル
c.execute("""
CREATE TABLE IF NOT EXISTS games (
  game_id TEXT PRIMARY KEY,
  fen TEXT NOT NULL,
  history TEXT NOT NULL
)
""")
conn.commit()

# 固定ユーザID（簡易ログインなし）
USER_ID = str(uuid.uuid4())
c.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (USER_ID,))
conn.commit()

# ─── 定跡／詰将棋データ読み込み ────────────────────────
with open("app/openings.json", encoding="utf-8") as f:
    OPENINGS = json.load(f)
with open("app/puzzles.json", encoding="utf-8") as f:
    PUZZLES = json.load(f)

# ─── SVG→PNG 描画ユーティリティ ────────────────────────
def render_board_with_hints(board, hints_legal=None, hints_theoretical=None, last_move=None):
    size = 350
    square = size / 8
    margin = square * 0.5
    svg_board = chess.svg.board(board=board, size=size, coordinates=True)
    doc = minidom.parseString(svg_board)
    svg = doc.documentElement

    # 合法手(緑丸)
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

    # 理論手(青丸)
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

    # 最後の手(黄枠)
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

def update_history(history_list):
    game = chess.pgn.Game()
    node = game
    for uci in history_list:
        node = node.add_main_variation(chess.Move.from_uci(uci))
    return game

# ─── グローバルステート ───────────────────────────────
board = chess.Board()
stockfish = Stockfish(path="/usr/games/stockfish"); stockfish.set_skill_level(3)
last_move = None
move_history = []

ai_board = chess.Board()
games_local = {}  # in-memory PvP
clock = None
puzzle_idx = 0

# ─── ① あなた vs AI ───────────────────────────────────
def make_move(move_uci, ai_skill):
    global board, stockfish, last_move, move_history
    if board.is_game_over():
        return render_board_with_hints(board, last_move=last_move), f"✅ 終了: {board.result()}", move_history
    try:
        mv = chess.Move.from_uci(move_uci.strip())
        if mv in board.legal_moves:
            board.push(mv); last_move = mv; move_history.append(move_uci.strip())
            stockfish.set_skill_level(int(ai_skill))
            stockfish.set_fen_position(board.fen())
            ai_uci = stockfish.get_best_move()
            mv2 = chess.Move.from_uci(ai_uci)
            board.push(mv2); last_move = mv2; move_history.append(ai_uci)
            status = f"✅ 終了: {board.result()}" if board.is_game_over() else "AI が指しました。"
            return render_board_with_hints(board, last_move=last_move), status, move_history
        else:
            return render_board_with_hints(board, last_move=last_move), "❌ 不正手です。", move_history
    except:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 入力エラー", move_history

def help_move(square_uci):
    global board, last_move
    sq = square_uci.strip().lower()
    if len(sq)!=2:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 例: e2"
    try:
        sqi = chess.parse_square(sq)
    except:
        return render_board_with_hints(board, last_move=last_move), "⚠️ 無効なマス"
    piece = board.piece_at(sqi)
    if not piece:
        return render_board_with_hints(board, last_move=last_move), f"⚠️ {sq}に駒なし"
    moves_legal = [m.to_square for m in board.legal_moves if m.from_square==sqi]
    # 理論上の移動先は省略可
    moves_theo = []
    return render_board_with_hints(board, hints_legal=moves_legal, hints_theoretical=moves_theo, last_move=last_move), f"✅ {sq} のヒント"

def undo_move():
    global board, last_move, move_history
    if len(move_history)>=2:
        board.pop(); board.pop()
        move_history = move_history[:-2]
        last_move = chess.Move.from_uci(move_history[-1]) if move_history else None
        return render_board_with_hints(board, last_move=last_move), "♻️ 1手戻し", move_history
    return render_board_with_hints(board, last_move=last_move), "⚠️ これ以上戻せません", move_history

def reset_board():
    global board, stockfish, last_move, move_history
    board = chess.Board()
    stockfish = Stockfish(path="/usr/games/stockfish"); stockfish.set_skill_level(3)
    last_move = None; move_history = []
    return render_board_with_hints(board), "🔄 新ゲーム開始", move_history

def download_pgn(history_list):
    game = update_history(history_list)
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)

# ─── ② 定跡ガイド ─────────────────────────────────────
def load_opening(name):
    data = next(o for o in OPENINGS if o["name"]==name)
    b = chess.Board()
    for uci in data["moves"]:
        b.push(chess.Move.from_uci(uci))
    return render_board_with_hints(b), "\n".join(data["moves"])

# ─── ③ 持ち時間付き対局（時計）────────────────────────
class Clock:
    def __init__(self, w, b):
        self.white, self.black = w, b
        self.turn = True
        self.running = False
        self.lock = threading.Lock()
    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
    def _run(self):
        while self.running and (self.white>0 and self.black>0):
            time.sleep(1)
            with self.lock:
                if self.turn: self.white -= 1
                else:        self.black -= 1
    def switch(self):
        with self.lock:
            self.turn = not self.turn
    def get_times(self):
        return self.white, self.black

def start_clock(w, b):
    global clock
    clock = Clock(int(w), int(b))
    clock.start()
    return f"{w}s vs {b}s", True

def switch_clock():
    if clock:
        clock.switch()
    return f"{clock.white}s vs {clock.black}s"

def refresh_clock():
    if clock:
        w, b = clock.get_times()
        return f"{w}s vs {b}s"
    return ""

# ─── ④ オンライン対戦 ─────────────────────────────────
def create_online_game():
    gid = str(uuid.uuid4())[:8]
    start_fen = chess.Board().fen()
    c.execute("INSERT INTO games(game_id, fen, history) VALUES(?,?,?)",
              (gid, start_fen, json.dumps([])))
    conn.commit()
    board, _ = get_online_state(gid)
    return gid, render_board_with_hints(board), "IDを共有してください。", True

def get_online_state(game_id):
    row = c.execute("SELECT fen, history FROM games WHERE game_id=?", (game_id,)).fetchone()
    if not row:
        return None, []
    fen, hist = row
    return chess.Board(fen), json.loads(hist)

def make_online_move(game_id, uci):
    board, hist = get_online_state(game_id)
    if board is None:
        return None, "❌ 無効ID"
    mv = chess.Move.from_uci(uci.strip())
    if mv not in board.legal_moves:
        return board, "❌ 不正手"
    board.push(mv); hist.append(uci.strip())
    c.execute("UPDATE games SET fen=?, history=? WHERE game_id=?", 
              (board.fen(), json.dumps(hist), game_id))
    conn.commit()
    return board, "👍 合法手"

def refresh_online(game_id):
    board, _ = get_online_state(game_id)
    return render_board_with_hints(board) if board else None

def _join_and_start(gid):
    board, _ = get_online_state(gid)
    if board is None:
        return "", render_board_with_hints(chess.Board()), "❌ 無効ID", False
    return gid, render_board_with_hints(board), "✅ 参加完了", True

# ─── ⑤ 成績表示 ───────────────────────────────────────
def show_stats():
    w, l, d = c.execute("SELECT wins,losses,draws FROM users WHERE id=?", (USER_ID,)).fetchone()
    return f"勝: {w}  負: {l}  引: {d}"

# ─── ⑥ 詰将棋トレーニング ────────────────────────────
def next_puzzle():
    global puzzle_idx
    fen = PUZZLES[puzzle_idx]["fen"]
    puzzle_idx = (puzzle_idx + 1) % len(PUZZLES)
    return render_board_with_hints(chess.Board(fen)), ""

def check_answer(ans):
    sol = PUZZLES[puzzle_idx-1]["solution"]
    return "✅ 正解！" if ans.split() == sol else f"❌ 不正解。解: {' '.join(sol)}"

# ─── ⑦ 局面入出力 ────────────────────────────────────
def load_fen(fen):
    try:
        b = chess.Board(fen)
        return render_board_with_hints(b)
    except:
        return None

def load_pgn(pgn_text):
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        b = game.end().board()
        return render_board_with_hints(b)
    except:
        return None

def export_fen():
    return board.fen()

def export_pgn():
    return download_pgn(move_history)

# ─── AI vs AI ─────────────────────────────────────────────
def ai_vs_ai_step(skill_white, skill_black):
    global ai_board
    if ai_board.is_game_over():
        return render_board_with_hints(ai_board), f"✅ 終了: {ai_board.result()}"
    sfw = Stockfish(path="/usr/games/stockfish"); sfw.set_skill_level(int(skill_white)); sfw.set_fen_position(ai_board.fen())
    sfb = Stockfish(path="/usr/games/stockfish"); sfb.set_skill_level(int(skill_black)); sfb.set_fen_position(ai_board.fen())
    mv_uci = sfw.get_best_move() if ai_board.turn else sfb.get_best_move()
    ai_board.push(chess.Move.from_uci(mv_uci))
    return render_board_with_hints(ai_board), f"現在の手番: {'白' if ai_board.turn else '黒'}"

def reset_ai_vs_ai():
    global ai_board
    ai_board = chess.Board()
    return render_board_with_hints(ai_board), "🤖 AI vs AI リセット完了"

# ─── ローカル PvP ────────────────────────────────────────
def create_game():
    gid = str(uuid.uuid4())[:8]
    games_local[gid] = {"board": chess.Board(), "lock": threading.Lock(), "history": []}
    return gid, render_board_with_hints(games_local[gid]["board"]), f"🎉 作成済: {gid}"

def join_game(gid):
    if gid in games_local:
        return render_board_with_hints(games_local[gid]["board"]), f"✅ 参加: {gid}"
    else:
        return render_board_with_hints(chess.Board()), "❌ 無効ID"

def pvp_move(gid, move_uci):
    if gid not in games_local:
        return render_board_with_hints(chess.Board()), "❌ 無効ID"
    entry = games_local[gid]
    with entry["lock"]:
        try:
            mv = chess.Move.from_uci(move_uci.strip())
            if mv in entry["board"].legal_moves:
                entry["board"].push(mv)
                entry["history"].append(move_uci.strip())
                if entry["board"].is_game_over():
                    return render_board_with_hints(entry["board"]), f"✅ 終了: {entry['board'].result()}"
                return render_board_with_hints(entry["board"]), f"👍 合法手: {move_uci}"
            else:
                return render_board_with_hints(entry["board"]), "❌ 不正手"
        except:
            return render_board_with_hints(entry["board"]), "⚠️ 入力エラー"

def pvp_reset(gid):
    if gid in games_local:
        with games_local[gid]["lock"]:
            games_local[gid]["board"] = chess.Board()
            games_local[gid]["history"] = []
        return render_board_with_hints(games_local[gid]["board"]), "🔄 リセット完了"
    else:
        return render_board_with_hints(chess.Board()), "❌ 無効ID"

def pvp_download_pgn(gid):
    if gid in games_local:
        game = update_history(games_local[gid]["history"])
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return game.accept(exporter)
    else:
        return ""

# ─── Gradio UI ─────────────────────────────────────────
with gr.Blocks() as app:
    gr.Markdown("## ♟️ チェスアプリ＋拡張機能")

    with gr.Tabs():

        # あなた vs AI
        with gr.TabItem("あなた vs AI"):
            img_h  = gr.Image(render_board_with_hints(board), type="pil", label="盤面")
            stat_h = gr.Textbox("あなたの番です。", interactive=False, label="状況")
            hist_h = gr.Textbox(interactive=False, label="履歴")
            inp_h  = gr.Textbox(placeholder="e2e4 or e2", label="入力")
            btn_go = gr.Button("指す")
            btn_help = gr.Button("Help")
            btn_undo = gr.Button("戻す")
            btn_reset = gr.Button("リセット")
            slider = gr.Slider(0,20,value=3,step=1,label="AIスキル")
            btn_dl = gr.Button("PGN ダウンロード")

            btn_go.click(make_move, [inp_h, slider], [img_h, stat_h, hist_h])
            btn_help.click(help_move, inp_h, [img_h, stat_h])
            btn_undo.click(undo_move, None, [img_h, stat_h, hist_h])
            btn_reset.click(reset_board, None, [img_h, stat_h, hist_h])
            btn_dl.click(download_pgn, hist_h, None)

        # AI vs AI
        with gr.TabItem("AI vs AI"):
            img_ai = gr.Image(render_board_with_hints(ai_board), type="pil", label="盤面")
            stat_ai= gr.Textbox("AI vs AI", interactive=False, label="状況")
            sw = gr.Slider(0,20,value=3,label="白AI")
            sb = gr.Slider(0,20,value=3,label="黒AI")
            btn_step = gr.Button("1手進める")
            btn_rst  = gr.Button("リセット")
            btn_step.click(ai_vs_ai_step, [sw, sb], [img_ai, stat_ai])
            btn_rst.click(reset_ai_vs_ai, None, [img_ai, stat_ai])

        # ローカル PvP
        with gr.TabItem("PvP (ローカル)"):
            gid_b = gr.Textbox(label="ゲームID")
            img_p = gr.Image(render_board_with_hints(chess.Board()), type="pil", label="盤面")
            stat_p= gr.Textbox(interactive=False, label="状況")
            inp_p = gr.Textbox(placeholder="e2e4",label="手")
            btn_c = gr.Button("作成")
            btn_j = gr.Button("参加")
            btn_p = gr.Button("指す")
            btn_pr= gr.Button("リセット")
            btn_pd= gr.Button("PGN ダウンロード")

            btn_c.click(create_game, None, [gid_b, img_p, stat_p])
            btn_j.click(join_game, gid_b, [img_p, stat_p])
            btn_p.click(pvp_move, [gid_b, inp_p], [img_p, stat_p])
            btn_pr.click(pvp_reset, gid_b, [img_p, stat_p])
            btn_pd.click(pvp_download_pgn, gid_b, None)

        # 定跡ガイド
        with gr.TabItem("定跡ガイド"):
            sel_o = gr.Dropdown([o["name"] for o in OPENINGS], label="オープニング")
            btn_o = gr.Button("開始")
            img_o = gr.Image(type="pil", label="盤面")
            stat_o= gr.Textbox(interactive=False, label="手順")
            btn_o.click(load_opening, sel_o, [img_o, stat_o])

        # 時計対局
        with gr.TabItem("時計対局"):
            time_w = gr.Number(300, label="白(s)")
            time_b = gr.Number(300, label="黒(s)")
            btn_sc = gr.Button("開始")
            btn_sw = gr.Button("切替")
            stat_c = gr.Textbox(interactive=False, label="残り時間")
            timer_c = gr.Timer(1.0, active=False)
            btn_sc.click(start_clock, [time_w, time_b], [stat_c, timer_c])
            btn_sw.click(switch_clock, None, stat_c)
            timer_c.tick(refresh_clock, None, stat_c)

        # オンライン対戦
        with gr.TabItem("オンライン対戦"):
            btn_co = gr.Button("作成")
            txt_gid = gr.Textbox(interactive=False, label="ゲームID")
            btn_jo = gr.Button("参加")
            inp_om = gr.Textbox(placeholder="e2e4", label="手")
            img_om = gr.Image(type="pil", label="盤面")
            stat_om= gr.Textbox(interactive=False, label="状況")
            timer_om= gr.Timer(1.0, active=False)
            btn_co.click(create_online_game, None, [txt_gid, img_om, stat_om, timer_om])
            btn_jo.click(_join_and_start, txt_gid, [txt_gid, img_om, stat_om, timer_om])
            btn_om = gr.Button("指す")
            btn_om.click(make_online_move, [txt_gid, inp_om], [img_om, stat_om])
            timer_om.tick(refresh_online, txt_gid, img_om)

        # 詰将棋
        with gr.TabItem("詰将棋"):
            img_pz = gr.Image(type="pil", label="盤面")
            btn_npz = gr.Button("次")
            inp_ans = gr.Textbox(label="解答")
            btn_ck = gr.Button("チェック")
            stat_pz = gr.Textbox(interactive=False, label="結果")
            btn_npz.click(next_puzzle, None, [img_pz, stat_pz])
            btn_ck.click(check_answer, inp_ans, stat_pz)

        # 成績
        with gr.TabItem("成績"):
            stat_u = gr.Textbox(interactive=False, label="あなたの成績")
            btn_st = gr.Button("見る")
            btn_st.click(show_stats, None, stat_u)

        # 入出力
        with gr.TabItem("入出力"):
            inp_fen = gr.Textbox(label="FEN")
            btn_lf  = gr.Button("FEN読込")
            inp_pgn = gr.Textbox(label="PGN")
            btn_lp  = gr.Button("PGN読込")
            out_img = gr.Image(type="pil", label="盤面")
            out_fen = gr.Textbox(interactive=False, label="FEN出力")
            out_pgn = gr.Textbox(interactive=False, label="PGN出力")
            btn_lf.click(load_fen, inp_fen, out_img)
            btn_lp.click(load_pgn, inp_pgn, out_img)
            gr.Button("FEN出力").click(export_fen, None, out_fen)
            gr.Button("PGN出力").click(export_pgn, None, out_pgn)

    app.launch(server_name="0.0.0.0", server_port=7860, share=True)
