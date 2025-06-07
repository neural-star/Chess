import io
from fastapi import APIRouter
from matplotlib import pyplot as plt
from ..services.stockfish_eval import eval_moves

router = APIRouter()

@router.post("/eval")
def eval_game(moves: list[str]):
    # moves = ["e2e4", "e7e5", …]
    evals = eval_moves(moves)  # [0.1, -0.3, 1.2, …]
    # 画像生成
    fig, ax = plt.subplots()
    ax.plot(evals)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
