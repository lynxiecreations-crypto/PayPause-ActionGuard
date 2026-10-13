"""PayPause baseline inference API. Inputs are processed in memory and never logged/stored."""
import os
import re
from pathlib import Path
from typing import List
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("PAYPAUSE_MODEL_PATH", ROOT / "ml/artifacts/sms_spam_baseline.joblib"))
app = FastAPI(title="PayPause ActionGuard Model API", version="0.1.0",
              description="Baseline SMS spam classifier plus transparent rule-based risk signals.")
origins = ["https://paypause-actionguard-demo.onrender.com", "http://localhost:8000", "http://127.0.0.1:8000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])
model = None
model_load_error = None
try:
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
    else:
        model_load_error = f"Model artifact missing at {MODEL_PATH}"
except Exception as exc:
    model_load_error = f"Model load failed: {type(exc).__name__}"

class PredictionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

class Signal(BaseModel):
    key: str
    explanation: str
    severity: str

def risk_signals(text: str) -> List[dict]:
    t = text.lower()
    signals = []
    rules = [
        ("otp_or_pin", r"\b(otp|one.time password|upi pin|pin number|password|verification code)\b", "Requests a secret code, PIN or password.", "high"),
        ("urgency_or_threat", r"\b(urgent|immediately|within \d+ minutes?|today|blocked|suspend|frozen|expire|last chance)\b", "Uses urgency or a threat to push a quick decision.", "medium"),
        ("money_pressure", r"\b(send money|transfer|pay now|payment|collect request|registration fee|redelivery fee|refund fee)\b", "Mentions a payment or money transfer.", "medium"),
        ("secrecy_or_impersonation", r"\b(don't call|do not call|keep it secret|don't tell|bank support|customer support|family member|police officer)\b", "May use secrecy or an authority/family claim to build trust.", "medium"),
        ("link_or_login", r"(https?://|www\.|\bclick (the )?link\b|verify your account|confirm your details|login)", "Contains a link or asks for account verification.", "medium"),
        ("app_install", r"\b(apk|install this app|download this app|accessibility permission)\b", "Mentions installing an app or granting device access.", "medium"),
    ]
    for key, pattern, explanation, severity in rules:
        if re.search(pattern, t):
            signals.append({"key": key, "explanation": explanation, "severity": severity})
    return signals

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None,
            "model_name": "TF-IDF + Logistic Regression (UCI SMS Spam Collection baseline)",
            "model_load_error": model_load_error}

@app.get("/metrics")
def metrics():
    path = ROOT / "ml/artifacts/metrics.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Evaluation metrics not found. Run ml/train_evaluate.py during build.")
    import json
    return json.loads(path.read_text(encoding="utf-8"))

@app.post("/predict")
def predict(req: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Trained baseline is unavailable; prediction was not run.")
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text must not be blank.")
    label = int(model.predict([text])[0])
    probability = None
    try:
        probs = model.predict_proba([text])[0]
        classes = list(model.classes_)
        probability = float(probs[classes.index(1)])
    except Exception:
        pass
    signals = risk_signals(text)
    # This combines a measured dataset-specific model output with separate transparent rules.
    # It is not calibrated for Indian financial scams and must not be presented as such.
    return {
        "model": "TF-IDF + Logistic Regression",
        "dataset": "UCI SMS Spam Collection",
        "dataset_scope": "general English SMS spam; not a validated Indian UPI/banking scam dataset",
        "model_label": "spam_like" if label == 1 else "ham_like",
        "model_spam_score": round(probability, 4) if probability is not None else None,
        "risk_signals": signals,
        "signal_count": len(signals),
        "note": "Model output is a baseline spam classification, not proof of fraud. Rule signals are separate and transparent. Do not use this alone to decide whether a payment is safe."
    }
