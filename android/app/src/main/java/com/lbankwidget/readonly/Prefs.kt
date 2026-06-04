package com.lbankwidget.readonly

import android.content.Context

/** Stores the backend API base URL. No credentials are ever stored here. */
object Prefs {
    private const val FILE = "lbank_widget_prefs"
    private const val KEY_BASE_URL = "base_url"

    fun getBaseUrl(ctx: Context): String =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(KEY_BASE_URL, "") ?: ""

    fun setBaseUrl(ctx: Context, url: String) {
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_BASE_URL, url.trim().trimEnd('/'))
            .apply()
    }
}
