package com.beyondbinary.paypause

import android.app.Activity
import android.os.Bundle
import android.content.Intent
import android.graphics.Typeface
import android.graphics.Color
import android.view.Gravity
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.widget.*
import java.util.Locale

class MainActivity : Activity() {
    private lateinit var input: EditText
    private lateinit var result: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildUi()
        handleIncoming(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncoming(intent)
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(26), dp(20), dp(24))
            setBackgroundColor(Color.rgb(245, 247, 243))
        }
        val scroll = ScrollView(this)
        val content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        val brand = TextView(this).apply {
            text = "PAYPAUSE  /  ACTIONGUARD"
            textSize = 12f
            setTextColor(Color.rgb(22, 79, 61))
            setTypeface(null, Typeface.BOLD)
        }
        val title = TextView(this).apply {
            text = "Pause before you pay."
            textSize = 29f
            setTextColor(Color.rgb(24, 37, 31))
            setTypeface(null, Typeface.BOLD)
            setPadding(0, dp(12), 0, dp(6))
        }
        val subtitle = TextView(this).apply {
            text = "Review suspicious messages locally. Nothing is uploaded by the local check."
            textSize = 15f
            setTextColor(Color.rgb(78, 91, 83))
        }
        input = EditText(this).apply {
            hint = "Paste or share a suspicious message or URL"
            minLines = 5
            gravity = Gravity.TOP
            textSize = 16f
            setPadding(dp(14), dp(12), dp(14), dp(12))
            setBackgroundColor(Color.WHITE)
        }
        val check = Button(this).apply {
            text = "Check on this device"
            setOnClickListener {
                val text = input.text.toString().trim()
                (getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager)
                    .hideSoftInputFromWindow(input.windowToken, 0)
                showAnalysis(LocalRuleChecker.analyze(text))
            }
        }
        result = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(16), 0, 0)
        }
        val privacy = TextView(this).apply {
            text = "PRIVACY: local heuristic checks only. No SMS permission, inbox monitoring, cloud request, or payment blocking is enabled."
            textSize = 12f
            setTextColor(Color.rgb(91, 103, 95))
            setPadding(0, dp(20), 0, 0)
        }
        content.addView(brand)
        content.addView(title)
        content.addView(subtitle)
        content.addView(input, marginParams(top = 18))
        content.addView(check, marginParams(top = 12))
        content.addView(result)
        content.addView(privacy)
        scroll.addView(content)
        root.addView(scroll)
        setContentView(root)
    }

    private fun handleIncoming(intent: Intent?) {
        if (intent == null) return
        val incoming = when (intent.action) {
            Intent.ACTION_SEND -> intent.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
            Intent.ACTION_VIEW -> intent.data?.toString()
            else -> null
        }
        if (!incoming.isNullOrBlank()) {
            input.setText(incoming)
            showAnalysis(LocalRuleChecker.analyze(incoming))
        }
    }

    private fun showAnalysis(report: LocalRuleChecker.Report) {
        result.removeAllViews()
        val heading = TextView(this).apply {
            text = "${report.level} CONCERN  ·  heuristic score ${report.score}/100"
            textSize = 18f
            setTypeface(null, Typeface.BOLD)
            setTextColor(when (report.level) {
                "HIGH" -> Color.rgb(174, 48, 42)
                "MEDIUM" -> Color.rgb(151, 92, 12)
                else -> Color.rgb(22, 79, 61)
            })
        }
        result.addView(heading)
        result.addView(body("This is a rule-based warning, not a verified fraud verdict or trained ML prediction."))
        result.addView(section("Signals found"))
        if (report.signals.isEmpty()) {
            result.addView(body("No configured warning patterns matched. That does not prove the message is safe."))
        }
        report.signals.forEach { result.addView(body("• $it")) }
        result.addView(section("Safer next steps"))
        report.steps.forEachIndexed { i, step -> result.addView(body("${i + 1}. $step")) }
    }

    private fun section(s: String) = TextView(this).apply {
        text = s
        textSize = 16f
        setTypeface(null, Typeface.BOLD)
        setTextColor(Color.rgb(24, 37, 31))
        setPadding(0, dp(14), 0, dp(4))
    }

    private fun body(s: String) = TextView(this).apply {
        text = s
        textSize = 14f
        setTextColor(Color.rgb(61, 73, 65))
        setPadding(0, dp(4), 0, dp(4))
    }

    private fun marginParams(top: Int = 0) = LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
    ).apply { topMargin = dp(top) }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}

object LocalRuleChecker {
    data class Report(val score: Int, val level: String, val signals: List<String>, val steps: List<String>)

    fun analyze(raw: String): Report {
        val text = raw.lowercase(Locale.ROOT)
        val signals = mutableListOf<String>()
        var score = 0
        fun add(pattern: Regex, points: Int, label: String) {
            if (pattern.containsMatchIn(text)) {
                signals += label
                score += points
            }
        }
        add(Regex("\\b(pin|otp|one.time password|password|cvv|upi pin)\\b"), 28, "Requests a PIN, OTP, password, or payment credential")
        add(Regex("\\b(pay now|urgent|immediately|account blocked|account suspended|last chance|within \\d+ minutes)\\b"), 18, "Uses urgency or a threat")
        add(Regex("\\b(refund|cashback|reward|prize|processing fee|verification fee|receive money)\\b"), 16, "Mentions a refund, reward, or fee-related payment scenario")
        add(Regex("\\b(anydesk|teamviewer|quick.support|screen sharing|install this app|download apk|remote access)\\b"), 25, "Requests remote access or an app installation")
        add(Regex("\\b(kyc|bank account|upi|wallet|beneficiary)\\b"), 10, "References financial account activity")
        if (Regex("https?://|www\\.").containsMatchIn(text)) {
            signals += "Contains a link that has not been reputation-checked"
            score += 12
        }
        if (Regex("https?://[^/ ]+@|https?://\\d{1,3}(?:\\.\\d{1,3}){3}").containsMatchIn(text)) {
            signals += "URL has an unusual user-info or IP-address shape"
            score += 18
        }
        score = score.coerceAtMost(100)
        val level = when {
            score >= 55 -> "HIGH"
            score >= 25 -> "MEDIUM"
            else -> "LOW"
        }
        val steps = mutableListOf<String>()
        if (signals.any { it.contains("credential") || it.contains("PIN") }) {
            steps += "Never share an OTP, UPI PIN, CVV, or password to receive money."
        }
        if (signals.any { it.contains("link") || it.contains("URL") }) {
            steps += "Do not open the link from the message; verify the domain independently."
        }
        if (signals.any { it.contains("remote access") }) {
            steps += "Do not install remote-control apps or share your screen with an unsolicited caller."
        }
        steps += "Verify the request using a known official contact, not contact details in the message."
        steps += "If money was lost in India, contact your bank immediately and report suspected cyber fraud at 1930."
        return Report(score, level, signals.distinct(), steps.distinct())
    }
}
