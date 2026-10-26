# Design notes: Returns Triage Agent

## Module map (`src/returntriage/`)

- `classifier.py`
- `cli.py`
- `fraud.py`
- `models.py`
- `policy.py`
- `triage.py`

## Test strategy

- Tests use only `unittest` (run with `python -m unittest` or `pytest`). Each test asserts a behaviour, with known-answer cases where a closed form exists, not just that code runs.
- Paths that need external services (LLM API, webcam) are isolated behind small interfaces and are NOT covered by the unit tests; each README says so.

## Failure modes considered

- Order of checks is the policy: hard stops -> window -> fraud -> value/ambiguity -> automatic outcome. Fraud is checked BEFORE auto-approval so a high-risk customer never gets a silent refund.
- The LLM (optional) only classifies the reason into a closed label set. Money decisions stay in plain, testable code.
- Seller-fault claims (defective, wrong item, transit damage) outside the window or in a non-returnable category go to a human rather than being auto-rejected; auto-rejecting a legitimate defect claim is the costlier mistake.

## Known gaps

- Fraud signals are heuristics (return frequency, missing receipt, condition/reason mismatch), not a trained model.
- No image evidence, order-history lookup, or carrier-tracking integration.
- Rule-based classifier is keyword matching; it will say `other` for unusual phrasing (which routes to a human, by design).
