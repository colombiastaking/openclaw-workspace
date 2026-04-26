---
description: Upload Colombia Staking Website and DApp via FTP to cPanel hosting. Use when updating the websites or DApp on the live server.
---

# cPanel/FTP Update Skill - Colombia Staking

Update Colombia Staking websites and DApp via FTP to cPanel hosting.

## ⚠️ IMPORTANT: Upload ALL Build Assets

When rebuilding and redeploying the DApp:
1. **Upload index.html** AND **all new JS/CSS files** from `build/assets/`
2. New builds create new hash filenames (e.g., `index-6ea07f4a.js` vs old `index-cd871205.js`)
3. If you only upload index.html without the new JS files → "text/html is not valid JavaScript" error
4. Always upload the complete `build/` folder contents:

```bash
# Upload index.html + all assets
curl -s -k --ftp-ssl -u "AliceDapp@..." -T build/index.html "ftp://.../index.html"
for f in build/assets/*; do
  curl -s -k --ftp-ssl -u "AliceDapp@..." -T "$f" "ftp://.../$f"
done
```

## ⚠️ ES/FR FTP Accounts

ES and FR FTP users exist but have **no home directory** configured on the server (421 error).

To fix: cPanel → FTP Accounts → Edit AliceEsp/AliceFr → set home directory:
- AliceEsp: `/home/colombia6/esp.colombia-staking.com`
- AliceFr: `/home/colombia6/fr.colombia-staking.com`

**Not blocking HTTP** — EN/ES/FR sites work fine via HTTP. FTP is just for maintenance.

**The server has SSL issues with lftp (timeout problems). Use curl instead.**

## ⚠️ CRITICAL: .htaccess Corruption Fix

If DApp routes return 404, the .htaccess may be corrupted. **Re-upload a clean .htaccess**:

```bash
# Create clean .htaccess
cat > /tmp/clean_htaccess.htaccess << 'HTACCESS'
RewriteEngine On
RewriteBase /
RewriteRule ^index\.html$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
HTACCESS

# Upload with AliceDapp credentials
curl -s -k --ftp-ssl \
  -u "AliceDapp@staking.colombia-staking.com:vXQln+-JsMLNz)0V" \
  -T /tmp/clean_htaccess.htaccess \
  "ftp://staking.colombia-staking.com/.htaccess"
```

Always use **new credentials** (not old colombia6/sMGi6hW3vikr) to avoid corruption.

## FTP Configuration

Credentials stored at: `~/.openclaw/secrets/.ftp_credentials`

### Individual Site Credentials (updated 2026-04-18)

**DApp (staking.colombia-staking.com):**
```
DAPP_HOST="staking.colombia-staking.com"
DAPP_USER="AliceDapp@staking.colombia-staking.com"
DAPP_PASS="vXQln+-JsMLNz)0V"
```

**EN Website (colombia-staking.com):**
```
ENG_HOST="colombia-staking.com"
ENG_USER="AliceEng@colombia-staking.com"
ENG_PASS="0w3ikUp^?k,1s@ET"
```

**ES Website (esp.colombia-staking.com):**
```
ESP_HOST="esp.colombia-staking.com"
ESP_USER="AliceEsp@esp.colombia-staking.com"
ESP_PASS="?jTL&[YOwIoo#Pmh"
```

**FR Website (fr.colombia-staking.com):**
```
FR_HOST="fr.colombia-staking.com"
FR_USER="AliceFr@fr.colombia-staking.com"
FR_PASS="qy+EN{rqa.u;9.%-"
```

**ES/FR FTP users** — Home directory not yet configured on server. cPanel → FTP Accounts to fix.

### Legacy (for backwards compatibility):
```
HOST="colombia-staking.com"
USER="colombia6"
PASS="sMGi6hW3vikr"
```

## Server Directory Structure

```
/home/colombia6/
├── public_html/                    ← EN site (index.html at root)
├── esp.colombia-staking.com/       ← ES site (index.html at root)
├── fr.colombia-staking.com/        ← FR site (index.html at root)
└── staking.colombia-staking.com/   ← DApp (index.html at root)
    index.html, manifest.json, node_status.json, etc.
    assets/, build/, leagues/, public/
```

## DApp Upload Process

```bash
# 1. Build the DApp
cd ~/.openclaw/workspace/DAPP-V3 && npm run build

# 2. Upload with new credentials
curl -s -k --ftp-ssl \
  -u "AliceDapp@staking.colombia-staking.com:vXQln+-JsMLNz)0V" \
  -T build/index.html \
  "ftp://staking.colombia-staking.com/index.html"

# 3. Re-upload .htaccess AFTER any file upload (LiteSpeed cache issue)
curl -s -k --ftp-ssl \
  -u "AliceDapp@staking.colombia-staking.com:vXQln+-JsMLNz)0V" \
  -T /tmp/clean_htaccess.htaccess \
  "ftp://staking.colombia-staking.com/.htaccess"
```

⚠️ **After uploading ANY file to DApp, always re-upload .htaccess** — LiteSpeed caches files aggressively and only clears on .htaccess re-upload.

## DApp Endpoints

| Tool | DApp Route | Data Endpoint |
|------|------------|---------------|
| BTC Strategy | `/tools` | `https://colombia-staking.co/btc-report/summary` |
| Tax Report | `/tools` (sub-page) | `https://colombia-staking.co/tax-query?address=...` |

Both endpoints route through kepler-proxy on port 3000 → cloudflared tunnel → Pi.

## FTP Helper Script

```bash
~/.openclaw/workspace/.agents/skills/cpanel-update/scripts/ftp-helper.sh <action>
```

Actions: `test`, `list-dapp`, `list-eng`, `list-esp`, `list-fr`, `upload-dapp <f> <r>`, etc.
