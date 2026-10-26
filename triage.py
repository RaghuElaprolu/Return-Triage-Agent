from __future__ import annotations
from typing import Callable
from .classifier import classify_rules
from .fraud import fraud_signals
from .models import Action, Decision, ReturnRequest
from .policy import Policy

FAULT_REASONS = {"defective", "wrong_item", "transit_damage"}


def triage(req: ReturnRequest, policy: Policy | None = None,
           classify: Callable[[str], str] = classify_rules) -> Decision:
    policy = policy or Policy()
    reason = classify(req.reason_text)
    days = (req.request_date - req.purchase_date).days
    window = policy.window_for(req.category)
    fraud, fraud_notes = fraud_signals(req, reason)
    why = [f"reason={reason}", f"{days}d since purchase (window {window}d)"] + fraud_notes

    def out(action: Action, code: str, refund: float = 0.0) -> Decision:
        return Decision(req.order_id, action, code, round(refund, 2), fraud, why)

    # 1. Hard stops
    if req.category in policy.non_returnable:
        if reason in FAULT_REASONS:
            why.append("non-returnable category but seller-fault claim -> human")
            return out(Action.MANUAL_REVIEW, "NONRETURNABLE_FAULT_CLAIM")
        return out(Action.REJECT, "NONRETURNABLE_CATEGORY")
    if days < 0:
        return out(Action.MANUAL_REVIEW, "DATE_INCONSISTENT")

    # 2. Window
    if days > window:
        if reason in FAULT_REASONS and days <= window * policy.grace_multiplier_for_faults:
            why.append("outside window but within fault grace period")
            return out(Action.MANUAL_REVIEW, "LATE_FAULT_CLAIM")
        return out(Action.REJECT, "OUTSIDE_WINDOW")

    # 3. Fraud gate
    if fraud >= policy.fraud_review_threshold:
        return out(Action.MANUAL_REVIEW, "FRAUD_SCORE")

    # 4. Value / ambiguity gates
    if req.price > policy.auto_approve_max_value:
        return out(Action.MANUAL_REVIEW, "HIGH_VALUE")
    if reason == "other":
        return out(Action.MANUAL_REVIEW, "UNCLEAR_REASON")

    # 5. Automatic outcomes
    if reason in FAULT_REASONS:
        if reason == "wrong_item":
            return out(Action.AUTO_EXCHANGE, "WRONG_ITEM_EXCHANGE", req.price)
        return out(Action.AUTO_REFUND, f"{reason.upper()}_REFUND", req.price)
    # changed_mind / not_as_described
    if req.condition in {"used", "damaged"}:
        return out(Action.MANUAL_REVIEW, "CONDITION_NOT_RESALEABLE")
    fee = policy.restocking_fee_pct.get(req.category, 0.0) if (req.condition == "opened" and reason == "changed_mind") else 0.0
    if fee:
        why.append(f"restocking fee {fee:.0%}")
    return out(Action.AUTO_REFUND, "STANDARD_REFUND", req.price * (1 - fee))
