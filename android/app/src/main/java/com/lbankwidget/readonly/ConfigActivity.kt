package com.lbankwidget.readonly

import android.app.Activity
import android.os.Bundle
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.glance.appwidget.GlanceAppWidgetManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Minimal settings screen: enter the backend API base URL
 * (e.g. https://your-app.up.railway.app). No credentials are entered here;
 * the app is read-only and never sends keys.
 */
class ConfigActivity : Activity() {

    private val scope = CoroutineScope(Dispatchers.Main)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val pad = (16 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        val title = TextView(this).apply {
            text = "LBank Widget 設定（唯讀）"
            textSize = 20f
        }
        val hint = TextView(this).apply {
            text = "輸入後端 API 網址，例如：\nhttps://your-app.up.railway.app\n\n" +
                "本 App 為唯讀，只會 GET 持倉摘要，不會送出任何金鑰或交易。"
            setPadding(0, pad / 2, 0, pad)
        }
        val input = EditText(this).apply {
            hint = "https://your-app.up.railway.app"
            setText(Prefs.getBaseUrl(this@ConfigActivity))
            setSingleLine(true)
        }
        val status = TextView(this).apply { setPadding(0, pad / 2, 0, 0) }

        val save = Button(this).apply {
            text = "儲存並更新 Widget"
            setOnClickListener {
                val url = input.text.toString().trim()
                if (!url.startsWith("http")) {
                    Toast.makeText(this@ConfigActivity, "請輸入 http(s) 開頭的網址", Toast.LENGTH_SHORT).show()
                    return@setOnClickListener
                }
                Prefs.setBaseUrl(this@ConfigActivity, url)
                refreshAllWidgets(status)
            }
        }

        root.addView(title)
        root.addView(hint)
        root.addView(input)
        root.addView(save)
        root.addView(status)
        setContentView(root)
    }

    private fun refreshAllWidgets(status: TextView) {
        scope.launch {
            try {
                val mgr = GlanceAppWidgetManager(this@ConfigActivity)
                val ids = mgr.getGlanceIds(PositionWidget::class.java)
                val widget = PositionWidget()
                ids.forEach { widget.update(this@ConfigActivity, it) }
                status.text = "已儲存。已更新 ${ids.size} 個 widget。" +
                    if (ids.isEmpty()) "\n（尚未在桌面新增 widget，長按桌面 → 小工具 → LBank Widget）" else ""
            } catch (e: Exception) {
                status.text = "儲存成功，但更新 widget 失敗：${e.message}"
            }
        }
    }
}
