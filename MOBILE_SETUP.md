# 在 Android 手機上使用（不開網頁、真正的桌面小工具）

整體流程分三步：**① 後端上 Railway → ② GitHub 雲端 build APK → ③ 手機裝 APK + 新增 widget**。
全程你不用裝 Android Studio。

```
[你的程式碼] --push--> [GitHub]
                         |  \
        (GitHub Actions) |   \ (Railway 部署後端)
                         v    v
                   [APK 檔]   [https://xxx.up.railway.app]
                         |          ^
                  手機下載安裝        | 手機 widget 每 30 分鐘 GET 一次
                         v          |
                  [桌面 LBank Widget] ─┘
```

---

## 前置：把這個資料夾推上 GitHub

> 這個 repo 的 git root 目前是整個家目錄，很亂。請只把 `Lbank tool` 這層獨立成一個 repo。

1. 註冊 GitHub 帳號（免費）。
2. 在 GitHub 開一個新的空 repo，例如 `lbank-widget`（建議設 Private）。
3. 在本機 `Lbank tool` 目錄執行：
   ```powershell
   cd "c:\Users\yaya\Documents\Lbank tool"
   git init
   git add .
   git commit -m "init: LBank read-only widget"
   git branch -M main
   git remote add origin https://github.com/<你的帳號>/lbank-widget.git
   git push -u origin main
   ```
   `.gitignore` 已排除 `.env`、`*.db`、APK 等，不會外洩金鑰。

---

## ① 後端部署到 Railway

1. 到 https://railway.app 用 GitHub 登入。
2. **New Project → Deploy from GitHub repo →** 選 `lbank-widget`。
3. Railway 會自動讀到根目錄的 `Dockerfile` 並開始 build。
4. 部署完成後，到該服務的 **Settings → Networking → Generate Domain**，
   會得到一個網址，例如：`https://lbank-widget-production.up.railway.app`
5. 開 `https://<你的網址>/healthz` 確認回傳：
   ```json
   {"status":"ok","mock_mode":true,"signature_method":"HmacSHA256","base_url":"https://lbkperp.lbank.com/"}
   ```
6. 開 `https://<你的網址>/api/lbank/widget-summary` 應該看到 mock 持倉 JSON。

> 目前是 **mock mode**（`LBANK_WIDGET_MOCK_MODE=true`），顯示假資料，安全。
> 接上真實 LBank 帳號要等合約 endpoint 實測確認後再說（見 README 的「待確認 endpoint」）。
> 真的要接時，在 Railway → Variables 設 `LBANK_API_KEY`（read-only 金鑰）等，**Secret 只放在 Railway 變數，不要進 git**。

---

## ② 用 GitHub Actions 雲端 build APK

不用裝 Android Studio。`.github/workflows/build-apk.yml` 已設定好。

1. push 之後，到 GitHub repo 的 **Actions** 分頁。
2. 找到 **Build Android APK** 這個 workflow：
   - push 有改到 `android/**` 會自動跑；
   - 或手動點 **Run workflow**（workflow_dispatch）。
3. 等綠勾勾（約 3–6 分鐘）。
4. 進入該次 run，最下方 **Artifacts** 區，下載 `lbank-widget-debug-apk`。
5. 解壓縮得到 `app-debug.apk`。

> 這是 **debug 版 APK**，已用 debug 金鑰自動簽章，可直接安裝（不能上架，但自用沒問題）。

---

## ③ 手機安裝 + 新增桌面 Widget

1. 把 `app-debug.apk` 傳到手機（或手機瀏覽器直接登入 GitHub 下載 artifact）。
2. 點開安裝。第一次會要你允許「安裝未知來源的應用程式」→ 同意。
3. 安裝後會有一個 **LBank Widget** App，打開它：
   - 在輸入框填你的 Railway 網址：`https://<你的網址>`
   - 按 **儲存並更新 Widget**。
4. 回桌面，**長按桌面空白處 → 小工具 / Widgets → 找到 LBank Widget → 拖到桌面**。
5. 完成！桌面就會顯示持倉，點 `↻` 手動刷新，系統每 30 分鐘也會自動更新一次。

---

## 常見問題

- **Widget 顯示「尚未設定 API 網址」**：打開 LBank Widget App 填網址並儲存。
- **顯示「無法連線」**：確認 Railway 網址對、`/healthz` 開得起來；網址要 `https://` 開頭（Android 預設擋純 http）。
- **想改畫面 / 欄位**：改 `android/.../PositionWidget.kt`，push 後 Actions 會 build 新 APK。
- **更新頻率**：Android widget 最快 30 分鐘自動更新一次（系統限制），要即時就點 `↻`。
- **安全**：App 只會對後端做 GET，沒有任何下單/交易程式碼；金鑰只在後端（Railway 變數），不在手機、不在 APK。

---

## 之後要接真實 LBank（重要）

目前合約「持倉查詢 / TP-SL」endpoint 官方文件未公開，程式裡是 `RealLBankAdapter` + `TODO` + `NotImplementedError` 擋著。
**在你實測確認那些 endpoint 之前，請保持 mock mode。** 細節見 [README.md](README.md)。
