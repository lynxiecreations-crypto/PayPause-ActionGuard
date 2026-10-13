"""Smoke tests for the trained baseline and transparent rule signals."""
import unittest
from pathlib import Path
from model_api.app import MODEL_PATH, model, risk_signals

class ModelSmokeTests(unittest.TestCase):
    def test_trained_artifact_is_loaded(self):
        self.assertTrue(MODEL_PATH.exists(), f"Missing model artifact: {MODEL_PATH}")
        self.assertIsNotNone(model, "Model failed to load")

    def test_model_returns_binary_prediction_and_probability(self):
        text = "Congratulations! You won a prize. Click the link to claim now."
        self.assertIn(int(model.predict([text])[0]), (0, 1))
        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba([text])[0][list(model.classes_).index(1)])
            self.assertGreaterEqual(probability, 0.0)
            self.assertLessEqual(probability, 1.0)

    def test_otp_and_link_signals_are_explained(self):
        signals = risk_signals("Your bank account is blocked. Verify OTP at https://example.invalid now.")
        keys = {item["key"] for item in signals}
        self.assertIn("otp_or_pin", keys)
        self.assertIn("link_or_login", keys)
        self.assertIn("urgency_or_threat", keys)

    def test_payment_pressure_is_detected(self):
        keys = {item["key"] for item in risk_signals("Send money now to avoid account suspension.")}
        self.assertIn("money_pressure", keys)
        self.assertIn("urgency_or_threat", keys)

    def test_ordinary_message_does_not_trigger_known_rules(self):
        signals = risk_signals("Reminder: the project review is tomorrow at 11:30 AM. Bring your prototype.")
        self.assertEqual(signals, [])

if __name__ == "__main__":
    unittest.main()
