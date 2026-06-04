package com.lbankwidget.readonly

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Flat view models matching the backend widget-summary response. */
data class PositionView(
    val symbol: String,
    val side: String,
    val leverage: Int?,
    val unrealizedPnl: Double?,
    val roePercent: Double?,
    val markPrice: Double?,
    val entryPrice: Double?,
    val liquidationPrice: Double?,
    val fullTakeProfit: Double?,
    val fullStopLoss: Double?,
    val partialTakeProfit: Double?,
    val partialStopLoss: Double?,
    val liquidationDistancePercent: Double?,
    val riskLevel: String,
)

data class SummaryView(
    val updatedAt: String,
    val totalUnrealizedPnl: Double?,
    val totalRoePercent: Double?,
    val riskLevel: String,
    val positions: List<PositionView>,
    val moreCount: Int,
)

/**
 * Read-only client. It only performs an HTTP GET against the widget-summary
 * endpoint. It has no method that could place, cancel, or modify any order.
 */
object LbankApi {

    fun fetchSummary(baseUrl: String): SummaryView {
        val url = URL("$baseUrl/api/lbank/widget-summary")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 8000
            readTimeout = 8000
        }
        try {
            val code = conn.responseCode
            if (code !in 200..299) {
                throw RuntimeException("HTTP $code")
            }
            val body = conn.inputStream.bufferedReader().use { it.readText() }
            return parse(body)
        } finally {
            conn.disconnect()
        }
    }

    private fun parse(body: String): SummaryView {
        val o = JSONObject(body)
        val arr = o.optJSONArray("positions")
        val positions = ArrayList<PositionView>()
        if (arr != null) {
            for (i in 0 until arr.length()) {
                val p = arr.getJSONObject(i)
                positions.add(
                    PositionView(
                        symbol = p.optString("symbol", "--"),
                        side = p.optString("side", "--"),
                        leverage = p.optNullableInt("leverage"),
                        unrealizedPnl = p.optNullableDouble("unrealized_pnl"),
                        roePercent = p.optNullableDouble("roe_percent"),
                        markPrice = p.optNullableDouble("mark_price"),
                        entryPrice = p.optNullableDouble("entry_price"),
                        liquidationPrice = p.optNullableDouble("liquidation_price"),
                        fullTakeProfit = p.optNullableDouble("full_take_profit_price"),
                        fullStopLoss = p.optNullableDouble("full_stop_loss_price"),
                        partialTakeProfit = p.optNullableDouble("partial_take_profit_price"),
                        partialStopLoss = p.optNullableDouble("partial_stop_loss_price"),
                        liquidationDistancePercent = p.optNullableDouble("liquidation_distance_percent"),
                        riskLevel = p.optString("risk_level", "unknown"),
                    )
                )
            }
        }
        return SummaryView(
            updatedAt = o.optString("updated_at", "--"),
            totalUnrealizedPnl = o.optNullableDouble("total_unrealized_pnl"),
            totalRoePercent = o.optNullableDouble("total_roe_percent"),
            riskLevel = o.optString("risk_level", "unknown"),
            positions = positions,
            moreCount = o.optInt("more_count", 0),
        )
    }

    private fun JSONObject.optNullableDouble(key: String): Double? {
        if (!has(key) || isNull(key)) return null
        val v = optDouble(key)
        return if (v.isNaN()) null else v
    }

    private fun JSONObject.optNullableInt(key: String): Int? {
        if (!has(key) || isNull(key)) return null
        return optInt(key)
    }
}
