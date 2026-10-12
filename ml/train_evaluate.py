"""
Reproducible baseline training/evaluation for PayPause.
Downloads the UCI SMS Spam Collection, trains TF-IDF + LogisticRegression,
reports held-out metrics, and exports ONNX if skl2onnx is installed.

This general SMS spam baseline is NOT a validated Indian UPI scam detector.
"""
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, classification_report, precision_score, recall_score, f1_score

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "artifacts"
DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)
DATA_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
ZIP_PATH = DATA_DIR / "sms-spam-collection.zip"

def load_dataset():
    if not ZIP_PATH.exists():
        print("Downloading UCI SMS Spam Collection...")
        urllib.request.urlretrieve(DATA_URL, ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        name = next(n for n in zf.namelist() if n.endswith("SMSSpamCollection"))
        rows = []
        for line in zf.read(name).decode("utf-8", errors="replace").splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and parts[0] in {"ham", "spam"}:
                rows.append((parts[1], 1 if parts[0] == "spam" else 0))
    return np.array([r[0] for r in rows], dtype=object), np.array([r[1] for r in rows], dtype=int)

def main():
    texts, labels = load_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    model = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, strip_accents="unicode",
                                  ngram_range=(1, 2), min_df=2, max_features=60000)),
        ("classifier", LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42))
    ])
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
    metrics = {
        "dataset": "UCI SMS Spam Collection",
        "dataset_url": DATA_URL,
        "total_examples": int(len(texts)),
        "train_examples": int(len(x_train)),
        "test_examples": int(len(x_test)),
        "positive_class": "spam",
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "classification_report": classification_report(
            y_test, predictions, target_names=["ham", "spam"], output_dict=True, zero_division=0
        ),
        "limitations": [
            "General SMS spam dataset; not specifically Indian UPI or banking scams.",
            "Random split is a baseline, not temporal or external validation.",
            "Metrics do not establish production readiness."
        ]
    }
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    import joblib
    joblib.dump(model, OUT_DIR / "sms_spam_baseline.joblib")
    print(json.dumps(metrics, indent=2))
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import StringTensorType
        onx = convert_sklearn(model, initial_types=[("text", StringTensorType([None, 1]))], target_opset=17)
        (OUT_DIR / "sms_spam_baseline.onnx").write_bytes(onx.SerializeToString())
        print("ONNX exported to", OUT_DIR / "sms_spam_baseline.onnx")
    except ImportError:
        print("ONNX not exported. Install skl2onnx and onnx to enable export.")
    print("IMPORTANT: review metrics and test against a separate Indian scam dataset before using in app.")

if __name__ == "__main__":
    main()
