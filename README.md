# LBank Futures Position Widget（read-only）

手機桌面用的 **唯讀** LBank 合約持倉小工具後端 + 前端預覽。
只做三件事：**查詢 + 顯示 + 風險提示**。

> ⚠️ **這不是交易機器人。** 全程不下單、不平倉、不取消單、不改槓桿、不改保證金/倉位模式、不提領、不轉帳。
> 連「測試下單」都沒有。API Key 請設定為 **read-only**。

> 📱 **想直接在 Android 手機桌面看（不開網頁）？** 看 [MOBILE_SETUP.md](MOBILE_SETUP.md)：
> Railway 部署後端 → GitHub Actions 雲端 build APK → 手機裝桌面 widget，全程不用 Android Studio。

---

## 安全須知（請務必先讀）

- **API Key 必須設為 read-only。** 本服務不需要、也不會呼叫任何 trading / withdrawal 端點。
- **不要開 withdrawal 權限、不要開 trading 權限。**
- **API Secret 只存在後端 `.env`。** 它不會出現在任何 API response、log、前端、錯誤訊息或 git repo。
  - `signature_method` / `base_url` / `mock_mode` 屬於可公開資訊（`/healthz` 只回這些）。
  - `sign` 簽名值本身也絕不會出現在回應或被簽字串中。
- **建議綁定後端伺服器 IP。** 依 LBank 規則，API Key 若未綁 IP，最長可能 30 天後失效。
- `.env`、`*.db` 已列入 `.gitignore`，不要 commit 真實金鑰。

### 需要實測 / 需要確認的 LBank Futures endpoint（目前未驗證）

LBank 官方公開文件（`https://www.lbank.com/docs/`）目前**只涵蓋 Spot V2 API**，
查不到以下永續/合約端點，因此這些一律走 **adapter + mock + `TODO`**，不硬寫猜測路徑：

- ❓ 合約 / 永續 **持倉查詢** REST endpoint 與 response 格式
- ❓ 合約 **TP/SL 查詢 / 設定** endpoint
- ❓ `lbkperp.lbank.com` / `lbkperpws.lbank.com` 的明確 REST 路徑

在這些端點被實測確認前，**請保持 `LBANK_WIDGET_MOCK_MODE=true`**。
`RealLBankAdapter` 的對應方法會 `raise NotImplementedError`，避免誤用猜測路徑。

> 簽名流程（HmacSHA256）是依官方 Spot 文件公開步驟實作的，屬已確定部分，已含測試。

---

## 專案結構

```
backend/
  app/
    main.py                       FastAPI 入口
    config.py                     設定（secret 不外洩）
    api/routes/lbank_widget.py    /api/lbank/* 路由
    services/exchange/
      lbank_signer.py             HmacSHA256 簽名（read-only）
      lbank_client.py             簽名 HTTP 傳輸（未上主線）
      lbank_models.py             Pydantic schema
      lbank_adapter.py            介面 + MockLBankAdapter + RealLBankAdapter(TODO)
    services/widget/
      lbank_widget_service.py     組 widget summary（扁平、給 Android Glance 直接吃）
      risk_calculator.py          風險距離 / 等級
    db/
      database.py
      models/lbank_widget_settings.py    顯示用 TP/SL（只存價格，無數量欄位）
      models/lbank_api_credentials.py    憑證（secret 不可序列化外傳）
  tests/                          pytest（signer / risk / schema / security）
frontend/
  widget-preview/index.html       零建置靜態預覽（大尺寸 widget 樣貌）
.env / .env.example
```

> 註：原規劃前端用 Next.js，但本機未安裝 Node，故先用零建置純靜態 HTML 預覽（功能等價、可直接 fetch 後端）。日後裝了 Node 再加 Next.js / PWA 版即可，後端契約不變。

---

## 啟動

### 1. 後端（mock mode，第一版主線）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- `GET  /healthz`
- `GET  /api/lbank/widget-summary`
- `POST /api/lbank/widget-settings/tpsl`
- `POST /api/lbank/test-connection`

API 文件：`http://127.0.0.1:8000/docs`

### 2. 前端預覽

直接用瀏覽器開 `frontend/widget-preview/index.html`，
頁面預設打 `http://127.0.0.1:8000`（後端已開 CORS）。

### 3. Mock mode 開關

`.env`：

```
LBANK_WIDGET_MOCK_MODE=true   # 主線；改 false 會走 RealLBankAdapter（目前 NotImplementedError）
LBANK_API_KEY=
LBANK_API_SECRET=
LBANK_SIGNATURE_METHOD=HmacSHA256
LBANK_BASE_URL=https://lbkperp.lbank.com/
```

Mock 內含：BTCUSDT Long、ETHUSDT Short、SOLUSDT（high risk、無 TP/SL）、XRPUSDT（缺強平價 → risk unknown）。
**Mock 不含任何真實 key / secret / sign。**

---

## 測試

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

涵蓋：
- `test_lbank_signer.py`：參數排序、MD5 大寫、HmacSHA256 正確、`sign` 不入被簽字串、`timestamp/signature_method/echostr` 有被加入。
- `test_lbank_risk_calculator.py`：long/short 距離、high/medium/safe/unknown 門檻、缺強平價 / 缺現價。
- `test_lbank_widget_schema.py`：最多 3 筆 + `+N more`、缺 TP/SL → null、`position_key` 為複合鍵、Hedge Mode 同 symbol long/short 不互相覆蓋、partial TP/SL 無數量欄位。
- `test_lbank_security.py`：response / log / mock 都不含 secret / api_key / sign；憑證 `to_public_dict` 不吐 secret。

---

## API 摘要

| Method | Path | 說明 | 限制 |
|---|---|---|---|
| GET | `/api/lbank/widget-summary` | 手機大尺寸 widget 資料 | read-only |
| POST | `/api/lbank/widget-settings/tpsl` | 存**顯示用** TP/SL 價格 | 只存本地、不送 LBank、不改真實 TP/SL |
| POST | `/api/lbank/test-connection` | read-only 連線測試 | 不可 test order、不呼叫交易端點 |

---

## 風險計算

`liquidation_distance_percent`：
- Long：`abs(mark - liq) / mark * 100`
- Short：`abs(liq - mark) / mark * 100`

`risk_level`：`<5 → high`、`5~10 → medium`、`>=10 → safe`、缺強平價或缺現價 → `unknown`。

排序進 widget：high → 虧損 PnL → 距強平最近 → notional 大 → 最多 3 筆，其餘 `+N more`。

---

## 允許 / 禁止

**允許**：read-only 查詢、mock mode、存顯示用 TP/SL 價格、風險計算、widget summary、預留 Android Glance interface。

**禁止**：下單、平倉、取消單、改槓桿、改保證金模式、提領、轉帳、啟用 trading/withdrawal 權限、在前端存 secret、log secret、README 放真實 key、亂測未確認的 LBank endpoint。
