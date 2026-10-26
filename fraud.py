from __future__ import annotations
from .models import ReturnRequest


def fraud_signals(req: ReturnRequest, reason: str) -> tuple[int, list[str]]:
    """Returns (score 0-100, human-readable signals). Heuristic, not a trained model."""
    score, notes = 0, []
    if req.returns_last_90d >= 5:
        score += 40; notes.append(f"{req.returns_last_90d} returns in 90 days (+40)")
    elif req.returns_last_90d >= 3:
        score += 20; notes.append(f"{req.returns_last_90d} returns in 90 days (+20)")
    if not req.has_receipt and req.price >= 100:
        score += 25; notes.append("no receipt on item >= $100 (+25)")
    if reason == "defective" and req.condition == "unopened":
        score += 20; notes.append("claims defective but item is unopened (+20)")
    if req.condition == "used" and reason == "changed_mind":
        score += 15; notes.append("used item returned for change of mind (+15)")
    if req.price >= 500:
        score += 10; notes.append("high-value item (+10)")
    return min(score, 100), notes
