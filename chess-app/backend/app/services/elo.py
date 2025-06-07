def expected_score(rating_a: int, rating_b: int) -> float:
    """Elo 期待勝率"""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_ratings(rating_white: int, rating_black: int,
                   outcome: float, k: int = 32) -> tuple[int, int]:
    """
    outcome: 白視点での結果 (1.0=勝ち, 0.5=引き分け, 0=負け)
    戻り値: (new_white_rating, new_black_rating)
    """
    exp_w = expected_score(rating_white, rating_black)
    exp_b = 1 - exp_w
    new_w = round(rating_white + k * (outcome - exp_w))
    new_b = round(rating_black + k * ((1 - outcome) - exp_b))
    return new_w, new_b