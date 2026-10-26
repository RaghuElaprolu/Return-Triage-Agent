import unittest
from datetime import date, timedelta
from returntriage import ReturnRequest, Action, triage
from returntriage.classifier import classify_claude, classify_rules
from returntriage.policy import Policy

BUY = date(2026, 10, 1)


def req(**kw):
    base = dict(order_id="T1", customer_id="c", sku="S", category="apparel", price=50.0,
                purchase_date=BUY, request_date=BUY + timedelta(days=5),
                reason_text="too small", condition="unopened")
    base.update(kw)
    return ReturnRequest(**base)


class ClassifierTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(classify_rules("It just stopped working"), "defective")
        self.assertEqual(classify_rules("Received a different item"), "wrong_item")
        self.assertEqual(classify_rules("meh"), "other")

    def test_claude_classifier_always_returns_valid_label(self):
        self.assertIn(classify_claude("broken screen"), ["defective", "wrong_item", "not_as_described",
                                                          "transit_damage", "changed_mind", "other"])


class TriageTests(unittest.TestCase):
    def test_standard_refund(self):
        d = triage(req())
        self.assertEqual((d.action, d.refund_amount), (Action.AUTO_REFUND, 50.0))

    def test_restocking_fee_on_opened_electronics_change_of_mind(self):
        d = triage(req(category="electronics", condition="opened", reason_text="changed my mind", price=100))
        self.assertEqual(d.action, Action.AUTO_REFUND)
        self.assertEqual(d.refund_amount, 85.0)

    def test_nonreturnable_rejected_but_fault_goes_to_human(self):
        self.assertEqual(triage(req(category="final_sale")).action, Action.REJECT)
        self.assertEqual(triage(req(category="final_sale", reason_text="arrived broken")).action,
                         Action.MANUAL_REVIEW)

    def test_outside_window(self):
        late = req(request_date=BUY + timedelta(days=40))
        self.assertEqual(triage(late).reason_code, "OUTSIDE_WINDOW")
        late_fault = req(request_date=BUY + timedelta(days=40), reason_text="stopped working")
        self.assertEqual(triage(late_fault).reason_code, "LATE_FAULT_CLAIM")
        way_late = req(request_date=BUY + timedelta(days=90), reason_text="stopped working")
        self.assertEqual(triage(way_late).action, Action.REJECT)

    def test_fraud_gate_beats_auto_approve(self):
        d = triage(req(returns_last_90d=6, reason_text="changed my mind"))
        self.assertEqual((d.action, d.reason_code), (Action.MANUAL_REVIEW, "FRAUD_SCORE"))

    def test_high_value_and_unclear_go_to_human(self):
        self.assertEqual(triage(req(price=450)).reason_code, "HIGH_VALUE")
        self.assertEqual(triage(req(reason_text="hmm")).reason_code, "UNCLEAR_REASON")

    def test_wrong_item_exchange(self):
        self.assertEqual(triage(req(reason_text="wrong item received")).action, Action.AUTO_EXCHANGE)

    def test_future_dated_request_is_flagged(self):
        d = triage(req(request_date=BUY - timedelta(days=1)))
        self.assertEqual(d.reason_code, "DATE_INCONSISTENT")

    def test_policy_is_injectable(self):
        strict = Policy(auto_approve_max_value=10.0)
        self.assertEqual(triage(req(), strict).reason_code, "HIGH_VALUE")


if __name__ == "__main__":
    unittest.main()
