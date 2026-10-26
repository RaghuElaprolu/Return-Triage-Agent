# Returns Triage Agent

Decides auto-refund / auto-exchange / human review / reject for return requests, with an explanation for every decision.

![tests](https://img.shields.io/badge/tests-unittest-blue) ![python](https://img.shields.io/badge/python-3.10%2B-blue)

## Architecture

```
request -> classify reason (rules | Claude) -> policy checks (category, window, grace)
         -> fraud signals (0-100) -> value & ambiguity gates -> Decision(action, code, refund, explanation[])
```

## Quick start

```bash
# no required dependencies (standard library only)
PYTHONPATH=src python -m returntriage.cli data/sample_returns.json
PYTHONPATH=src python -m unittest discover -s tests -v
```

Example output:

```
A100  auto_refund    DEFECTIVE_REFUND      refund=$89.0   fraud=0
A102  manual_review  FRAUD_SCORE           refund=$0.0    fraud=75
A103  reject         NONRETURNABLE_CATEGORY
A104  reject         OUTSIDE_WINDOW
A105  auto_exchange  WRONG_ITEM_EXCHANGE   refund=$18.0   fraud=0
```

## Key design decisions

- Order of checks is the policy: hard stops -> window -> fraud -> value/ambiguity -> automatic outcome. Fraud is checked BEFORE auto-approval so a high-risk customer never gets a silent refund.
- The LLM (optional) only classifies the reason into a closed label set. Money decisions stay in plain, testable code.
- Seller-fault claims (defective, wrong item, transit damage) outside the window or in a non-returnable category go to a human rather than being auto-rejected; auto-rejecting a legitimate defect claim is the costlier mistake.
- Policy is a frozen dataclass injected into `triage()`, so thresholds are changeable per merchant without code edits.

## Limitations (read before using)

- Fraud signals are heuristics (return frequency, missing receipt, condition/reason mismatch), not a trained model.
- No image evidence, order-history lookup, or carrier-tracking integration.
- Rule-based classifier is keyword matching; it will say `other` for unusual phrasing (which routes to a human, by design).

## Next steps

- Add photo evidence via a vision model, still gated by the same policy code.
- Replace fraud heuristics with a model trained on historical chargebacks/abuse labels.
- Offline evaluation harness: replay past returns and compare decisions with human outcomes.

See [docs/DESIGN.md](docs/DESIGN.md) for the module map and test strategy.
