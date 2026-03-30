# Confidence helpers for post-processing extraction scores.

def clamp_confidence(score: float) -> float:
    if score < 0:
        return 0.0
    if score > 1:
        return 1.0
    return round(score, 2)
