from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    window_days: dict[str, int] = field(default_factory=lambda: {
        "electronics": 15, "apparel": 30, "home": 30, "default": 30})
    non_returnable: frozenset[str] = frozenset({"final_sale", "perishable", "intimate"})
    restocking_fee_pct: dict[str, float] = field(default_factory=lambda: {"electronics": 0.15})
    grace_multiplier_for_faults: float = 2.0   # defective/wrong item gets 2x window, via human review
    auto_approve_max_value: float = 200.0
    fraud_review_threshold: int = 40

    def window_for(self, category: str) -> int:
        return self.window_days.get(category, self.window_days["default"])
