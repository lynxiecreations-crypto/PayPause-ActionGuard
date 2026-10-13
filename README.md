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

## Trained text baseline and simulation API
The Render model service trains TF-IDF + Logistic Regression on the UCI SMS Spam Collection during deployment, evaluates a stratified 80/20 random split, exports and validates an ONNX artifact, and serves inference at `/predict`. The phone simulation sends only its fictional sample text to this API when a user taps **Explain risk**. It does not access personal apps or inboxes.

- Model service: https://paypause-actionguard-model-api.onrender.com
- Health: `/health`
- Held-out metrics: `/metrics`
- Inference: `POST /predict` with JSON `{"text":"sample message"}`
- Model: TF-IDF word n-grams + Logistic Regression.
- Separate rule checks flag OTP/PIN requests, urgency/threats, money pressure, secrecy/impersonation, links/login requests, and APK/device-permission language.
- Automated smoke tests run in `.github/workflows/model-baseline.yml`.

**Limitations:** UCI SMS Spam Collection is general English SMS spam, not an Indian UPI/banking scam dataset. The model is English-only, the score is not a calibrated fraud probability, and rule signals are not ML predictions. These results do not establish production readiness. Do not enter real private messages into the demo.
