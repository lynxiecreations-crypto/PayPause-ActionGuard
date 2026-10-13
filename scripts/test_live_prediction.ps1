$ErrorActionPreference = "Stop"
$baseUrl = "https://paypause-actionguard-model-api.onrender.com"

Write-Host "Checking live PayPause model API..." -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 60
$health | ConvertTo-Json -Depth 8

if ($health.status -ne "ok") {
    throw "Health check failed: API status was not 'ok'."
}
if (-not $health.model_loaded) {
    throw "API is reachable, but the trained model is not loaded. $($health.model_load_error)"
}

Write-Host "`nSending a fictional scam-like test message to POST /predict..." -ForegroundColor Cyan
$body = @{
    text = "Your bank account is blocked. Share your OTP immediately to avoid suspension."
} | ConvertTo-Json

$prediction = Invoke-RestMethod -Uri "$baseUrl/predict" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 60
$prediction | ConvertTo-Json -Depth 8

if (-not $prediction.model_label) {
    throw "Prediction response did not include model_label."
}
Write-Host "`nLIVE PREDICTION REQUEST SUCCEEDED. Label: $($prediction.model_label)" -ForegroundColor Green
Write-Host "Note: this is a general English SMS-spam baseline, not proof of fraud or an India-specific scam verdict."
