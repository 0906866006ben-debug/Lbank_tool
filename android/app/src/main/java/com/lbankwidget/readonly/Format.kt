package com.lbankwidget.readonly

import kotlin.math.abs

/** Display helpers. Mirrors the web preview rules: "--" for missing data,
 *  always show +/- on PnL and ROE. */
object Format {

    fun price(n: Double?): String {
        if (n == null) return "--"
        val a = abs(n)
        val decimals = when {
            a >= 1000 -> 0
            a >= 1 -> 2
            else -> 4
        }
        return String.format("%,.${decimals}f", n)
    }

    fun signed(n: Double?, suffix: String = ""): String {
        if (n == null) return "--"
        val sign = if (n >= 0) "+" else ""
        return "$sign${String.format("%.2f", n)}$suffix"
    }

    fun percent(n: Double?): String {
        if (n == null) return "--"
        return "${String.format("%.1f", n)}%"
    }

    fun riskLabel(level: String): String = when (level) {
        "safe" -> "安全"
        "medium" -> "中"
        "high" -> "高"
        else -> "未知"
    }

    fun hhmm(isoOrText: String): String {
        // updated_at looks like 2026-06-04T14:32:00+08:00
        val t = isoOrText.indexOf('T')
        if (t >= 0 && isoOrText.length >= t + 6) {
            return isoOrText.substring(t + 1, t + 6)
        }
        return "--"
    }
}
