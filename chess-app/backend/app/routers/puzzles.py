import random, chess, chess.pgn
router = APIRouter()
# PGN から詰将棋集を読み込んでおく
puzzles = load_pgn("tactics.pgn")

@router.get("/random")
def random_puzzle():
    puzzle = random.choice(puzzles)
    return {
        "fen": puzzle.board().fen(),
        "solution": [mv.uci() for mv in puzzle.mainline_moves()]
    }
