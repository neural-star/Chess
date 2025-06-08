import gradio as gr
import chess
from stockfish import Stockfish
from db import list_active_games
from puzzles import next_puzzle, check_puzzle_move
from ai_training import run_batch_ai_vs_ai
from online import (
    create_room, join_room, list_rooms,
    make_move as online_make_move,
    get_room_chat, post_room_chat
)
from stats import user_stats
from io import BytesIO
import chess.svg, cairosvg
from PIL import Image
from xml.dom import minidom

STOCKFISH_PATH = "/usr/games/stockfish"

# SVG→PNG変換共通関数
def render_board(board):
    svg_board = chess.svg.board(board=board, size=350, coordinates=True)
    doc = minidom.parseString(svg_board)
    png = cairosvg.svg2png(bytestring=doc.toxml().encode('utf-8'))
    return Image.open(BytesIO(png))

# Gradio UI
with gr.Blocks() as app:
    gr.Markdown("## ♟️ グローバルチェスアプリ 拡張版")

    with gr.Tabs():

        # ------- あなた vs AI -------
        with gr.TabItem("あなた vs AI"):
            board = chess.Board()
            sf = Stockfish(path=STOCKFISH_PATH)
            sf.set_skill_level(3)
            img = gr.Image(value=render_board(board), type="pil", label="盤面")
            status = gr.Textbox("あなたの番です。", interactive=False)
            hist = gr.Textbox(interactive=False, label="PGN")
            move_in = gr.Textbox(placeholder="例: e2e4")
            ai_lvl = gr.Slider(0,20,value=3,label="AIレベル")
            btn = gr.Button("指す")
            def vs_ai(move, lvl):
                nonlocal board, sf
                try:
                    mv = chess.Move.from_uci(move.strip())
                    if mv in board.legal_moves:
                        board.push(mv)
                        sf.set_skill_level(int(lvl))
                        sf.set_fen_position(board.fen())
                        ai_mv = sf.get_best_move()
                        board.push(chess.Move.from_uci(ai_mv))
                        res = board.result() if board.is_game_over() else "あなたの番です。"
                        return render_board(board), res, board.board_fen()
                    else:
                        return render_board(board), "❌ 不正な手です", hist.value
                except:
                    return render_board(board), "⚠️ 入力エラー", hist.value
            btn.click(vs_ai, [move_in, ai_lvl], [img, status, hist])

        # ------- 練習モード -------
        with gr.TabItem("練習モード"):
            img_puz = gr.Image(type="pil", label="問題盤面")
            res_puz = gr.Textbox(interactive=False)
            btn_next = gr.Button("次の問題")
            inp_puz = gr.Textbox(placeholder="例: e2e4")
            btn_check = gr.Button("解答")
            btn_next.click(next_puzzle, None, [img_puz, res_puz])
            btn_check.click(check_puzzle_move, inp_puz, [img_puz, res_puz])

        # ------- AI vs AI 学習 -------
        with gr.TabItem("AI vs AI 学習"):
            lvl_w = gr.Slider(0,20,value=5,label="白AI")
            lvl_b = gr.Slider(0,20,value=15,label="黒AI")
            n_games = gr.Slider(1,100,value=20,label="対局数")
            out_summary = gr.Textbox(interactive=False, label="集計結果")
            out_csv = gr.Textbox(interactive=False, visible=False)
            btn_run = gr.Button("実行")
            btn_dl = gr.File(value=None, visible=False, label="CSVダウンロード")
            def run_and_export(w, b, n):
                summary, csv_data = run_batch_ai_vs_ai(w, b, n)
                # 一時ファイルに保存
                path = "/mnt/data/ai_vs_ai.csv"
                with open(path, "w") as f:
                    f.write(csv_data)
                return summary, path
            btn_run.click(run_and_export, [lvl_w, lvl_b, n_games], [out_summary, btn_dl])

        # ------- オンライン対戦 -------
        with gr.TabItem("オンライン対戦"):
            user_id = gr.Textbox(label="あなたの名前")
            # ルーム一覧
            room_list = gr.Dataframe(headers=["id","players","result"], interactive=False)
            btn_refresh = gr.Button("ルーム一覧更新")
            btn_refresh.click(lambda: list_active_games(), None, room_list)

            # ルーム作成 / 参加
            inp_room = gr.Textbox(label="ルームID")
            btn_create = gr.Button("作成")
            btn_join = gr.Button("参加")
            status_room = gr.Textbox(interactive=False)
            btn_create.click(lambda u: (create_room(u),), user_id, status_room)
            btn_join.click(lambda gid,u: ("参加済", join_room(gid,u)), [inp_room,user_id], status_room)

            # 対局盤面
            img_on = gr.Image(type="pil", label="盤面")
            move_on = gr.Textbox(placeholder="例: e2e4")
            btn_move = gr.Button("指す")
            status_on = gr.Textbox(interactive=False)
            def on_move(gid, uid, mv):
                board, msg = online_make_move(gid, uid, mv)
                return render_board(board), msg
            btn_move.click(on_move, [inp_room,user_id,move_on], [img_on,status_on])

            # チャット
            chat = gr.Chatbot()
            chat_in = gr.Textbox(placeholder="チャットメッセージ")
            chat_send = gr.Button("送信")
            chat_refresh = gr.Timer(1, active=True)
            def send_msg(gid, uid, txt):
                return post_room_chat(gid, uid, txt)
            chat_send.click(send_msg, [inp_room,user_id,chat_in], chat)
            chat_refresh.tick(lambda gid: get_room_chat(gid), inp_room, chat)

        # ------- 統計 -------
        with gr.TabItem("統計"):
            uid_stat = gr.Textbox(label="ユーザー名")
            out_stat = gr.JSON()
            btn_stat = gr.Button("表示")
            btn_stat.click(lambda u: user_stats(u), uid_stat, out_stat)

    app.launch(
      share=True,
    )
