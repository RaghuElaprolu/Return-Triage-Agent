from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Action(str, Enum):
    AUTO_REFUND = "auto_refund"
    AUTO_EXCHANGE = "auto_exchange"
    MANUAL_REVIEW = "manual_review"
    REJECT = "reject"


@dataclass
class ReturnRequest:
    order_id: str
    customer_id: str
    sku: str
    category: str                 # e.g. electronics, apparel, final_sale, perishable
    price: float
    purchase_date: date
    request_date: date
    reason_text: str
    condition: str = "unopened"   # unopened | opened | used | damaged
    has_receipt: bool = True
    returns_last_90d: int = 0


@dataclass
class Decision:
    order_id: str
    action: Action
    reason_code: str
    refund_amount: float = 0.0
    fraud_score: int = 0
    explanation: list[str] = field(default_factory=list)
