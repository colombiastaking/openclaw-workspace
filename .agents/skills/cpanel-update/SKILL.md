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
4. Always upload the complete `build/` folder contents

## Deploy Script

**Use the Python lftp deploy script** — it handles TLS properly and uploads only changed files:

```bash
python3 ~/.openclaw/workspace/scripts/deploy-website.py [en|es|fr|dapp|all]
```

| Flag | Deploys |
|------|---------|
| `en` | EN website → `colombia-staking.com/` |
| `es` | ES website → `esp.colombia-staking.com/` |
| `fr` | FR website → `fr.colombia-staking.com/` |
| `dapp` | DApp → `staking.colombia-staking.com/` |
| `all` | All 4 sites |

**Only deploy what changed** — don't run `all` unless everything changed.

## Server Directory Structure

```
/home/colombia6/
├── public_html/                       ← EN site (index.html at root)
├── esp.colombia-staking.com/          ← ES site (index.html at root)
├── fr.colombia-staking.com/           ← FR site (index.html at root)
└── staking.colombia-staking.com/      ← DApp (index.html at root)
    index.html, manifest.json, node_status.json, etc.
    assets/, build/, leagues/, public/
```

## FTP Configuration

**Single account for all sites** (works with TLS):

```
HOST="colombia-staking.com"
USER="colombia6"
PASS="[REDACTED]"
```

Credentials stored at: `~/.openclaw/secrets/.ftp_credentials`

## DApp Paths (on Pi)

| Item | Local Path |
|------|-----------|
| DApp source | `/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/` |
| DApp build | `/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/build/` |
| DApp GitHub | `https://github.com/colombiastaking/DAPP-V3.git` |

## Website Paths (on Pi)

| Item | Local Path |
|------|-----------|
| Website source | `/home/raspberry/.openclaw/workspace/colombia-staking/Website/` |
| EN | `Website/eng/` → `/public_html/` |
| ES | `Website/esp/` → `/esp.colombia-staking.com/` |
| FR | `Website/fr/` → `/fr.colombia-staking.com/` |
| Website GitHub | `https://github.com/colombiastaking/Website.git` |

## Rebuilding and Deploying DApp

```bash
# 1. Rebuild DApp
cd ~/.openclaw/workspace/colombia-staking/DAPP-V3 && npm run build

# 2. Deploy to cPanel (only DApp changed)
python3 ~/.openclaw/workspace/scripts/deploy-website.py dapp

# 3. Commit to GitHub
cd ~/.openclaw/workspace/colombia-staking/DAPP-V3
git add src/helpers/FallbackProxyNetworkProvider.ts  # or whatever changed
git commit -m "describe change"
git push origin main
```

## Rebuilding and Deploying Websites

```bash
# 1. Commit changes to GitHub
cd ~/.openclaw/workspace/colombia-staking/Website
git add .
git commit -m "describe change"
git push origin main

# 2. Deploy to cPanel
python3 ~/.openclaw/workspace/scripts/deploy-website.py en  # or es fr or all
```

## Manual FTP (curl fallback)

If lftp fails, use curl with explicit FTP:

```bash
# Upload single file
curl -k --ftp-ssl \
  -u "colombia6:[REDACTED]" \
  -T local-file.txt \
  "ftp://colombia-staking.com/remote-file.txt"
```

## DApp Endpoints

| Tool | DApp Route | Data Endpoint |
|------|------------|---------------|
| BTC Strategy | `/tools` | `https://colombia-staking.co/btc-report/summary` |
| Tax Report | `/tools` (sub-page) | `https://colombia-staking.co/tax-query?address=...` |

Both route through kepler-proxy on port 3000 → cloudflared tunnel → Pi.

## Troubleshooting

### LiteSpeed serving stale content
After uploading, LiteSpeed may cache old HTML. Purge via:
cPanel → LiteSpeed Cache → Purge All

### FTP TLS certificate errors
The `colombia6` account handles TLS fine. If cert errors appear, add to lftp script:
```
set ssl:verify-certificate no
```
