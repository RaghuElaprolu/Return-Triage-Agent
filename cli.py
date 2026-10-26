import argparse, json
from datetime import date
from .models import ReturnRequest
from .triage import triage


def main() -> None:
    ap = argparse.ArgumentParser(description="Triage returns from a JSON list.")
    ap.add_argument("input")
    ap.add_argument("--llm", action="store_true", help="classify reasons with Claude (needs API key)")
    a = ap.parse_args()
    classify = None
    if a.llm:
        from .classifier import classify_claude as classify
    for r in json.load(open(a.input)):
        r["purchase_date"] = date.fromisoformat(r["purchase_date"])
        r["request_date"] = date.fromisoformat(r["request_date"])
        d = triage(ReturnRequest(**r), **({"classify": classify} if classify else {}))
        print(f"{d.order_id:8} {d.action.value:14} {d.reason_code:26} refund=${d.refund_amount:<8} fraud={d.fraud_score}")


if __name__ == "__main__":
    main()
