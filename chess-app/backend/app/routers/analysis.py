import io
from fastapi import APIRouter
from matplotlib import pyplot as plt
from ..services.stockfish_eval import eval_moves
from ..services.stockfish_best import best_eval_moves

router = APIRouter(prefix="/analysis", tags=["analysis"])

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

class AnalysisCompareOut(BaseModel):
    moves: List[str]
    actual_eval: List[float]
    best_eval:   List[float]

@router.post("/compare", response_model=AnalysisCompareOut)
def compare_game(moves: List[str]):
    actual = eval_moves(moves)
    best   = best_eval_moves(moves)
    return {"moves": moves, "actual_eval": actual, "best_eval": best}
