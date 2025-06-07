import uuid, threading, time, sqlite3, json
import chess, chess.svg, chess.pgn
from io import BytesIO
import cairosvg
from PIL import Image
from xml.dom import minidom
from stockfish import Stockfish
import gradio as gr

# ─── ユーザ成績用DB準備 ───
conn = sqlite3.connect("app/users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0
  )
""")
conn.commit()
# UUID で簡易ユーザ管理
USER_ID = str(uuid.uuid4())
c.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (USER_ID,))
conn.commit()

# ─── 定跡＆詰将棋データ読み込み ───
with open("app/openings.json", "r", encoding="utf-8") as f:
    OPENINGS = json.load(f)
with open("app/puzzles.json", "r", encoding="utf-8") as f:
    PUZZLES = json.load(f)

# ─── SVG→PNGボード描画 ───
def render_board_with_hints(board, hints_legal=None, hints_theoretical=None, last_move=None):
    size, square, margin = 350, 350/8, (350/8)*0.5
    svg_board = chess.svg.board(board=board, size=size, coordinates=True)
    doc = minidom.parseString(svg_board); svg = doc.documentElement
    # （ここに緑丸・青丸・黄枠の挿入処理... 省略）

    png = cairosvg.svg2png(bytestring=doc.toxml().encode("utf-8"))
    return Image.open(BytesIO(png))

# ─── 既存のあなたvsAI, AI vs AI, PvP, Help, Undo, Reset, PGNダウンロード... ───
# ここにはお手元の既存コードをそのままコピペしてください。

# ─── ② 定跡ガイド タブ ───
def load_opening(name):
    data = next(o for o in OPENINGS if o["name"] == name)
    b = chess.Board()
    for uci in data["moves"]:
        b.push(chess.Move.from_uci(uci))
    return render_board_with_hints(b), "\n".join(data["moves"])

# ─── ⑤ 成績表示 ───
def show_stats():
    c.execute("SELECT wins, losses, draws FROM users WHERE id=?", (USER_ID,))
    w, l, d = c.fetchone()
    return f"勝利: {w}  敗北: {l}  引き分け: {d}"

# ─── ⑥ 詰将棋トレーニング ───
puzzle_idx = 0
def next_puzzle():
    global puzzle_idx
    fen = PUZZLES[puzzle_idx]["fen"]
    puzzle_idx = (puzzle_idx + 1) % len(PUZZLES)
    return render_board_with_hints(chess.Board(fen)), ""
def check_answer(ans):
    sol = PUZZLES[puzzle_idx - 1]["solution"]
    return "✅ 正解！" if ans.split() == sol else f"❌ 不正解。解答: {' '.join(sol)}"

# ─── Gradio UI 定義 ───
with gr.Blocks() as app:
    gr.Markdown("## ♟️ グローバルチェスアプリ＋拡張機能")
    with gr.Tabs():
        # --- 既存タブ: あなた vs AI, AI vs AI, PvP  ---
        with gr.TabItem("定跡ガイド"):
            sel_o = gr.Dropdown([o["name"] for o in OPENINGS], label="オープニング選択")
            btn_o = gr.Button("定跡開始")
            board_o = gr.Image(type="pil")
            status_o = gr.Textbox(interactive=False)
            btn_o.click(load_opening, sel_o, [board_o, status_o])

        with gr.TabItem("詰将棋トレーニング"):
            board_p = gr.Image(type="pil")
            btn_np = gr.Button("次の問題")
            inp_pa = gr.Textbox(label="解答（例: e7e8q）")
            btn_ca = gr.Button("解答チェック")
            status_p = gr.Textbox(interactive=False)
            btn_np.click(next_puzzle, None, [board_p, status_p])
            btn_ca.click(check_answer, inp_pa, status_p)

        with gr.TabItem("成績＆プロフィール"):
            stats = gr.Textbox(interactive=False)
            btn_stats = gr.Button("戦績を見る")
            btn_stats.click(show_stats, None, stats)

        # --- 他のタブも同様に追加: 時計, 観戦, 入出力 など ---
    app.launch(server_name="0.0.0.0", server_port=7860)
