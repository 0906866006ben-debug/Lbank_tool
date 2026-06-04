# Desktop sync mode

Use this when your home desktop is always on and you want to avoid paying for a VPS.

The desktop reads LBank from your home public IPv4, then pushes only sanitized widget display data to Railway. The phone still reads Railway.

```text
Desktop -> LBank private API
Desktop -> Railway /api/lbank/widget-snapshot
Phone widget -> Railway /api/lbank/widget-summary
```

## What IP goes into LBank

Run this on the home desktop:

```powershell
(Invoke-WebRequest -UseBasicParsing https://api.ipify.org).Content
```

Put that IPv4 into the LBank API IP field.

Important: if your ISP changes this IP, LBank API calls will fail until you update the API whitelist.

## Railway variables

In Railway, add:

```env
LBANK_WIDGET_SOURCE=pushed
LBANK_SYNC_TOKEN=<make-a-long-random-token>
```

Do not put LBank API key or secret in Railway for this mode.

Redeploy Railway after changing variables.

## Desktop variables

On the home desktop, the LBank API key/secret stay local in `.env`:

```env
LBANK_WIDGET_MOCK_MODE=false
LBANK_API_KEY=<your-read-only-contract-key>
LBANK_API_SECRET=<your-secret>
LBANK_SIGNATURE_METHOD=HmacSHA256
LBANK_BASE_URL=https://lbkperp.lbank.com/
```

The API key must be read-only + contract only. Do not enable trading, withdrawal, or transfer.

## Run the desktop backend

From the repo root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Keep that window running.

## Push a snapshot to Railway

Open a second PowerShell window:

```powershell
$env:LBANK_SYNC_TOKEN="<same-token-as-railway>"
python .\desktop_sync\push_snapshot.py --target "https://lbanktool-production.up.railway.app"
```

For continuous sync every 60 seconds:

```powershell
$env:LBANK_SYNC_TOKEN="<same-token-as-railway>"
python .\desktop_sync\push_snapshot.py --target "https://lbanktool-production.up.railway.app" --interval 60
```

## Test from the phone app

Keep the Android app backend URL as:

```text
https://lbanktool-production.up.railway.app
```

Do not add `/healthz`.

## Current limitation

This mode solves the fixed-IP problem. The real LBank read-only position adapter still needs the verified LBank contract position endpoint and response shape before `LBANK_WIDGET_MOCK_MODE=false` can show live positions.
