# PayPause ActionGuard — Android starter

Beyond Binary's native Android starter for privacy-first scam-message review.

## Current scope
- Native Kotlin Android application.
- Local deterministic heuristic checks; the checker does not send message text to a server.
- Accepts text through Android Share (`ACTION_SEND`) and links opened with the app (`ACTION_VIEW`).
- No SMS permissions, background inbox monitoring, payment access, or transaction blocking.
- The displayed score is a heuristic score, not a probability or trained-model prediction.

## Build
1. Install Android Studio.
2. Open this repository as a project and let Gradle sync.
3. Run on an Android device or emulator (Android 8.0 / API 26+).

## Share-to-app test
Share suspicious text from another app and choose PayPause ActionGuard. Confirm it appears and a local check runs.

## Limitations
- No trained ONNX/TFLite model is bundled yet.
- Native app does not call a URL reputation API.
- No benchmark metrics are claimed.
- PWA and native Android app are separate deliverables.
- Test security, privacy, and accessibility before release.

## Reproducible model baseline (not yet trained)
The `ml/` folder contains a script to download the UCI SMS Spam Collection, train TF-IDF + Logistic Regression, calculate held-out precision, recall, F1, confusion matrix and false-positive rate, and optionally export ONNX. It is not a UPI scam detector, and the model is not yet trained or bundled.

Run with Python 3.11+:
```bash
python -m pip install -r ml/requirements.txt
python ml/train_evaluate.py
```
Review `ml/artifacts/metrics.json`. Evaluate against a separately labelled India-specific scam dataset before making claims about UPI/banking scam detection.
