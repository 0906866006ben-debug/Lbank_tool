package com.lbankwidget.readonly

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.ColorProvider
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.action.actionRunCallback
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.provideContent
import androidx.glance.background
import androidx.glance.layout.Alignment
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.padding
import androidx.glance.layout.width
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private val BG = Color(0xFF0D1117)
private val CARD = Color(0xFF161B22)
private val TEXT = Color(0xFFE6EDF3)
private val MUTED = Color(0xFF8B949E)
private val GREEN = Color(0xFF2EA043)
private val RED = Color(0xFFF85149)
private val AMBER = Color(0xFFD29922)
private val GREY = Color(0xFF6E7681)

private fun cp(c: Color) = ColorProvider(c)

private fun riskColor(level: String): Color = when (level) {
    "safe" -> GREEN
    "medium" -> AMBER
    "high" -> RED
    else -> GREY
}

private fun pnlColor(n: Double?): Color = when {
    n == null -> MUTED
    n >= 0 -> GREEN
    else -> RED
}

class PositionWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val baseUrl = Prefs.getBaseUrl(context)
        val state: WidgetState = try {
            if (baseUrl.isBlank()) {
                WidgetState.Error("尚未設定 API 網址，請開啟 App 設定")
            } else {
                val summary = withContext(Dispatchers.IO) { LbankApi.fetchSummary(baseUrl) }
                WidgetState.Loaded(summary)
            }
        } catch (e: Exception) {
            WidgetState.Error("無法連線：${e.message ?: "未知錯誤"}")
        }

        provideContent {
            WidgetRoot(state)
        }
    }
}

private sealed interface WidgetState {
    data class Loaded(val summary: SummaryView) : WidgetState
    data class Error(val message: String) : WidgetState
}

@Composable
private fun WidgetRoot(state: WidgetState) {
    Column(
        modifier = GlanceModifier
            .fillMaxSize()
            .background(cp(BG))
            .cornerRadius(20.dp)
            .padding(14.dp)
            .clickable(actionStartActivity<ConfigActivity>())
    ) {
        Header(state)
        when (state) {
            is WidgetState.Error -> Text(
                state.message,
                style = TextStyle(color = cp(RED), fontSize = 13.sp)
            )
            is WidgetState.Loaded -> Body(state.summary)
        }
    }
}

@Composable
private fun Header(state: WidgetState) {
    Row(modifier = GlanceModifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(
            "LBank Futures",
            style = TextStyle(color = cp(TEXT), fontWeight = FontWeight.Bold, fontSize = 15.sp)
        )
        Spacer(GlanceModifier.defaultWeight())
        // Manual refresh.
        Text(
            "↻",
            style = TextStyle(color = cp(MUTED), fontSize = 16.sp),
            modifier = GlanceModifier.clickable(actionRunCallback<RefreshAction>())
        )
    }
    if (state is WidgetState.Loaded) {
        val s = state.summary
        Row(modifier = GlanceModifier.fillMaxWidth().padding(top = 4.dp)) {
            Text("PnL ", style = TextStyle(color = cp(MUTED), fontSize = 13.sp))
            Text(
                Format.signed(s.totalUnrealizedPnl, " USDT"),
                style = TextStyle(color = cp(pnlColor(s.totalUnrealizedPnl)), fontWeight = FontWeight.Bold, fontSize = 13.sp)
            )
            Spacer(GlanceModifier.width(12.dp))
            Text("ROE ", style = TextStyle(color = cp(MUTED), fontSize = 13.sp))
            Text(
                if (s.totalRoePercent != null) Format.signed(s.totalRoePercent, "%") else "--",
                style = TextStyle(color = cp(pnlColor(s.totalRoePercent)), fontWeight = FontWeight.Bold, fontSize = 13.sp)
            )
            Spacer(GlanceModifier.defaultWeight())
            Text("Updated ${Format.hhmm(s.updatedAt)}", style = TextStyle(color = cp(MUTED), fontSize = 11.sp))
        }
        Row(modifier = GlanceModifier.fillMaxWidth().padding(top = 2.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Risk ", style = TextStyle(color = cp(MUTED), fontSize = 11.sp))
            Text(
                Format.riskLabel(s.riskLevel),
                style = TextStyle(color = cp(riskColor(s.riskLevel)), fontWeight = FontWeight.Bold, fontSize = 11.sp)
            )
        }
    }
}

@Composable
private fun Body(s: SummaryView) {
    s.positions.forEach { p -> PositionCard(p) }
    if (s.moreCount > 0) {
        Text(
            "+${s.moreCount} more",
            style = TextStyle(color = cp(MUTED), fontSize = 11.sp),
            modifier = GlanceModifier.fillMaxWidth().padding(top = 6.dp)
        )
    }
}

@Composable
private fun PositionCard(p: PositionView) {
    val sideColor = if (p.side == "long") GREEN else RED
    val sideLabel = if (p.side == "long") "Long" else "Short"
    Column(
        modifier = GlanceModifier
            .fillMaxWidth()
            .padding(top = 8.dp)
            .background(cp(CARD))
            .cornerRadius(12.dp)
            .padding(8.dp)
    ) {
        Row(modifier = GlanceModifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(p.symbol, style = TextStyle(color = cp(TEXT), fontWeight = FontWeight.Bold, fontSize = 13.sp))
            Spacer(GlanceModifier.width(6.dp))
            Text(sideLabel, style = TextStyle(color = cp(sideColor), fontSize = 12.sp))
            Spacer(GlanceModifier.width(6.dp))
            Text(p.leverage?.let { "${it}x" } ?: "--", style = TextStyle(color = cp(MUTED), fontSize = 12.sp))
            Spacer(GlanceModifier.defaultWeight())
            Text(Format.riskLabel(p.riskLevel), style = TextStyle(color = cp(riskColor(p.riskLevel)), fontWeight = FontWeight.Bold, fontSize = 11.sp))
        }
        Row(modifier = GlanceModifier.fillMaxWidth().padding(top = 4.dp)) {
            Text("未實現 ", style = TextStyle(color = cp(MUTED), fontSize = 12.sp))
            Text(Format.signed(p.unrealizedPnl), style = TextStyle(color = cp(pnlColor(p.unrealizedPnl)), fontSize = 12.sp))
            Spacer(GlanceModifier.defaultWeight())
            Text("ROE ", style = TextStyle(color = cp(MUTED), fontSize = 12.sp))
            Text(if (p.roePercent != null) Format.signed(p.roePercent, "%") else "--", style = TextStyle(color = cp(pnlColor(p.roePercent)), fontSize = 12.sp))
        }
        KvRow("現價", Format.price(p.markPrice), "強平", Format.price(p.liquidationPrice))
        KvRow("進場", Format.price(p.entryPrice), "距強平", Format.percent(p.liquidationDistancePercent))
        KvRow("全倉止盈", Format.price(p.fullTakeProfit), "全倉止損", Format.price(p.fullStopLoss))
        KvRow("定量止盈", Format.price(p.partialTakeProfit), "定量止損", Format.price(p.partialStopLoss))
    }
}

@Composable
private fun KvRow(k1: String, v1: String, k2: String, v2: String) {
    Row(modifier = GlanceModifier.fillMaxWidth().padding(top = 2.dp)) {
        Text("$k1 ", style = TextStyle(color = cp(MUTED), fontSize = 11.sp))
        Text(v1, style = TextStyle(color = cp(TEXT), fontSize = 11.sp))
        Spacer(GlanceModifier.defaultWeight())
        Text("$k2 ", style = TextStyle(color = cp(MUTED), fontSize = 11.sp))
        Text(v2, style = TextStyle(color = cp(TEXT), fontSize = 11.sp))
    }
}
