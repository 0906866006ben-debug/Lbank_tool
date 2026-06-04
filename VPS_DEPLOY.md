# VPS deploy guide

This deploys the read-only backend on a VPS with a fixed public IPv4 address.
Use that VPS IPv4 in the LBank API IP whitelist.

## 1. Rent a VPS

Pick Ubuntu 22.04 or 24.04 from Vultr, DigitalOcean, Linode, Contabo, etc.

Copy the server public IPv4, for example:

```text
123.45.67.89
```

In LBank API creation:

- IP address: the VPS public IPv4
- Signature: HmacSHA256
- Permissions: read-only + contract only
- Do not enable trading, withdrawal, or transfer

## 2. SSH into the VPS

```bash
ssh root@123.45.67.89
```

Install Docker:

```bash
apt update
apt install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 3. Clone the repo

```bash
git clone https://github.com/0906866006ben-debug/Lbank_tool.git /opt/lbank-tool
cd /opt/lbank-tool
```

## 4. Create the VPS env file

Use `sslip.io` first so you do not need to buy a domain:

```bash
cp .env.example .env
nano .env
```

Set:

```env
APP_DOMAIN=123.45.67.89.sslip.io
LBANK_WIDGET_MOCK_MODE=true
LBANK_API_KEY=
LBANK_API_SECRET=
LBANK_SIGNATURE_METHOD=HmacSHA256
LBANK_BASE_URL=https://lbkperp.lbank.com/
LBANK_DB_URL=sqlite:////data/lbank_widget.db
```

Keep `LBANK_WIDGET_MOCK_MODE=true` until the real LBank read-only position endpoint is implemented and tested.

## 5. Open firewall ports

If UFW is enabled:

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Your VPS provider may also have a cloud firewall. Allow inbound TCP `80` and `443`.

## 6. Start the backend

```bash
docker compose -f docker-compose.vps.yml up -d --build
docker compose -f docker-compose.vps.yml ps
```

Check logs if needed:

```bash
docker compose -f docker-compose.vps.yml logs -f
```

## 7. Test HTTPS

Open:

```text
https://123.45.67.89.sslip.io/healthz
```

Expected:

```json
{"status":"ok","mock_mode":true,...}
```

Then use this base URL in the Android app:

```text
https://123.45.67.89.sslip.io
```

Do not add `/healthz` or `/api/lbank/widget-summary`.

## 8. Update after code changes

```bash
cd /opt/lbank-tool
git pull
docker compose -f docker-compose.vps.yml up -d --build
```
