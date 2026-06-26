# Alice Restore Guide 🚀

## Complete Disaster Recovery Procedure

If the Raspberry Pi dies, follow this guide to restore Alice exactly as she was.

**Last verified:** 2026-04-14
**Backup system:** `backup.sh` in `~/.openclaw/alice-backup/` — runs daily at 6 PM via OpenClaw cron
**Encryption password:** stored in `.backup_password` (inside this repo)

---

## What Gets Backed Up

| Category | Files | Encrypted |
|----------|-------|-----------|
| OpenClaw config | `alice_config.enc`, `alice_env.enc` | ✅ AES-256-CBC |
| Credentials | `credentials.tar.enc` (Telegram, WhatsApp, OpenClaw pairing) | ✅ |
| Devices | `devices.tar.enc` (paired devices/sessions) | ✅ |
| Memory | `memory.tar.enc` (daily session logs) | ✅ |
| Telegram | `telegram.tar.enc` (Telegram session) | ✅ |
| Wallet | `wallet.tar.enc` (wallet-backup/) | ✅ |
| Tokens | `google-tokens.enc`, `microsoft-tokens.enc`, `git-credentials.enc` | ✅ |
| Identity | `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `HEARTBEAT.md`, `TOOLS.md`, `MEMORY.md`, `CRON.md`, `RESTORE.md` | ❌ plaintext |
| Skills | `skills/` (all agent skills) | ❌ plaintext |
| Scripts | `external-ip-monitor.sh`, `node_monitor_full.sh`, `daily_ip.sh` | ❌ plaintext |
| Distribution | `scripts/run_distribution_cron.sh`, `scripts/daily_distribution.sh` | ❌ plaintext |
| Systemd | `systemd/*.service` (kepler-proxy, openclaw-gateway, cloudflared-tunnel) | ❌ plaintext |
| Crontab | `crontab.txt` | ❌ plaintext |
| Cloudflare | `config.yml` (tunnel) | ❌ plaintext |
| Kepler proxy | `kepler-proxy.js` | ❌ plaintext |
| MCP server | `alice-mcp-multiversx/` | ❌ plaintext |
| Network explorer | `network-explorer/` | ❌ plaintext |
| Git repos | `colombia-staking/` (DAPP-V3, Website, tax-report-payment) | ❌ plaintext |
| BTC strategy | `btc-strategy/` | ❌ plaintext |
| Monitors | `aave-monitor/`, `btc-monitor/`, `node-monitor/` | ❌ plaintext |
| Memory daily | `memory/` (daily logs) | ❌ plaintext |
| Kylian | `kylian/` (school files) | ❌ plaintext |

---

## Prerequisites

1. Fresh Raspberry Pi OS installation
2. Git installed: `sudo apt install git`
3. Clone this repo:
```bash
git clone https://github.com/colombiastaking/alice-backup.git ~/.openclaw/alice-backup
```

---

## Step 1: Base Setup

```bash
# Install required packages
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm unzip bc jq curl wget ncdu

# Install OpenClaw
npm install -g openclaw

# Create directories
mkdir -p ~/.openclaw
mkdir -p ~/.config/systemd/user
mkdir -p ~/.openclaw/kepler
mkdir -p ~/.openclaw/workspace
mkdir -p ~/.mcporter
mkdir -p /tmp
```

---

## Step 2: Restore Encrypted Files

**IMPORTANT:** You need the encryption password (same one used by backup.sh). It's stored in `.backup_password` inside this repo.

```bash
cd ~/.openclaw/alice-backup

# Read password variable
PASS=$(cat .backup_password)

# Alice config → OpenClaw main config
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in alice_config.enc -out ~/.openclaw/openclaw.json -pass pass:"$PASS"

# Alice env → environment variables
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in alice_env.enc -out ~/.openclaw/.env -pass pass:"$PASS"

# Credentials (Telegram, WhatsApp, OpenClaw pairing)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in credentials.tar.enc -out credentials.tar -pass pass:"$PASS"
tar -xf credentials.tar -C ~

# Devices (paired devices/sessions)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in devices.tar.enc -out devices.tar -pass pass:"$PASS"
tar -xf devices.tar -C ~

# Memory (daily session logs)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in memory.tar.enc -out memory.tar -pass pass:"$PASS"
tar -xf memory.tar -C ~/.openclaw/workspace/ 2>/dev/null || true

# Telegram session
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in telegram.tar.enc -out telegram.tar -pass pass:"$PASS"
tar -xf telegram.tar -C ~

# Wallet backup
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in wallet.tar.enc -out wallet.tar -pass pass:"$PASS"
tar -xf wallet.tar -C ~

# Google tokens (Calendar API)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in google-tokens.enc -out google-tokens.json -pass pass:"$PASS"

# Microsoft tokens (Teams - may be expired)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in microsoft-tokens.enc -out microsoft-tokens.json -pass pass:"$PASS"

# GitHub credentials (for automated backup push)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in git-credentials.enc -out ~/.git-credentials -pass pass:"$PASS"
chmod 600 ~/.git-credentials

# mcporter config (MultiversX MCP server)
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in mcporter-config.enc -out ~/.mcporter/mcporter.json -pass pass:"$PASS"
chmod 600 ~/.mcporter/mcporter.json

# Cloudflare tunnel credentials
mkdir -p ~/.cloudflared
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in cloudflared-credentials.enc \
  -out ~/.cloudflared/credentials.json -pass pass:"$PASS"
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
  -in cloudflared-config.enc \
  -out ~/.cloudflared/config.yml -pass pass:"$PASS"
chmod 600 ~/.cloudflared/credentials.json
```

---

## Step 3: Restore Workspace Files

```bash
cd ~/.openclaw/alice-backup

# Core identity files
cp AGENTS.md SOUL.md USER.md IDENTITY.md HEARTBEAT.md TOOLS.md \
   MEMORY.md CRON.md RESTORE.md ~/.openclaw/workspace/

# Memory daily files
mkdir -p ~/.openclaw/workspace/memory
cp -r memory/* ~/.openclaw/workspace/memory/ 2>/dev/null || true

# Kylian school files
cp -r kylian/* ~/.openclaw/workspace/ 2>/dev/null || true

# Agent skills
mkdir -p ~/.openclaw/workspace/.agents
cp -r skills/* ~/.openclaw/workspace/.agents/skills/ 2>/dev/null || true
```

---

## Step 4: Restore Git Repos

```bash
cd ~/.openclaw/alice-backup

# Colombia Staking repos (already extracted from tar)
cp -r colombia-staking/DAPP-V3 ~/.openclaw/workspace/
cp -r colombia-staking/Website ~/.openclaw/workspace/
cp -r colombia-staking/tax-report-payment ~/.openclaw/workspace/

# BTC strategy (separate repo, also included here)
cp -r btc-strategy ~/.openclaw/workspace/
```

---

## Step 5: Restore Monitoring Scripts

```bash
cd ~/.openclaw/alice-backup

# Copy monitoring scripts to Pi home
cp external-ip-monitor.sh node_monitor_full.sh daily_ip.sh /home/raspberry/
chmod +x /home/raspberry/*.sh

# Copy monitor directories
cp -r aave-monitor btc-monitor node-monitor ~/.openclaw/workspace/ 2>/dev/null || true

# Copy distribution scripts
mkdir -p ~/.openclaw/workspace/scripts
cp -r scripts/* ~/.openclaw/workspace/scripts/ 2>/dev/null || true
```

---

## Step 6: Restore Systemd Services

```bash
cd ~/.openclaw/alice-backup

# All systemd services
cp systemd/*.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload
```

---

## Step 7: Restore Crontab

```bash
cd ~/.openclaw/alice-backup
crontab crontab.txt
crontab -l  # verify
```

---

## Step 8: Restore Cloudflare Tunnel

```bash
cd ~/.openclaw/alice-backup

# Cloudflare tunnel config
mkdir -p ~/.cloudflared
cp config.yml ~/.cloudflared/

# Tunnel ID: 6429a054-ec31-4f78-9b17-059e14ac58be
# (cloudflared credentials also in credentials.tar)
```

---

## Step 9: Restore Kepler Proxy

```bash
cd ~/.openclaw/alice-backup
cp kepler-proxy.js ~/.openclaw/kepler/
```

---

## Step 10: Restore MCP MultiversX Server

```bash
cd ~/.openclaw/alice-backup
cp -r alice-mcp-multiversx ~/.openclaw/workspace/

# Build the MCP server
cd ~/.openclaw/workspace/alice-mcp-multiversx
npm install
npm run build

# Verify
mcporter list
mcporter call multiversx.get-balance address:erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt
```

---

## Step 11: Restore Network Explorer

```bash
cd ~/.openclaw/alice-backup
cp -r network-explorer ~/.openclaw/workspace/
```

---

## Step 12: Enable and Start Services

```bash
# Enable lingering (required for user services to run after logout)
loginctl enable-linger $(whoami)

# Start OpenClaw gateway
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway

# Start Kepler proxy
systemctl --user enable kepler-proxy
systemctl --user start kepler-proxy

# Start Cloudflare tunnel
systemctl --user enable cloudflared-tunnel
systemctl --user start cloudflared-tunnel
```

---

## Step 13: Install NPM Packages

```bash
# Install global npm packages
npm install -g openclaw
npm install -g agent-browser

# Install agent-browser chromium
agent-browser install --force
```

---

## Step 14: Rebuild MCP Server (after npm install)

```bash
cd ~/.openclaw/workspace/alice-mcp-multiversx
npm run build

# Test
mcporter list
mcporter call multiversx.query-account address:erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt
```

---

## Step 15: Verify Everything

```bash
# Check OpenClaw status
openclaw status

# Check cron jobs (both system and OpenClaw)
crontab -l
openclaw cron list

# Check services
systemctl --user list-units --type=service

# Test monitoring scripts
/home/raspberry/external-ip-monitor.sh

# Test MCP server
mcporter call multiversx.query-account address:erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt
```

---

## Cron Jobs Summary

### OpenClaw Cron (managed via `openclaw cron list`)

| Name | Schedule | Purpose |
|------|----------|---------|
| `network-explorer-collector` | `0 * * * *` (hourly) | researcher — keeps DB + JSON fresh |
| `alice-daily-backup` | `0 18 * * *` (6 PM) | Full backup to GitHub |
| `Daily Strategy Report` | `0 11 * * *` (11 AM) | BTC strategy + Aave |
| `daily-distribution-execution` | `10 13 * * *` (1:10 PM) | COLS distribution |
| `daily-distribution-summary` | `35 13 * * *` (1:35 PM) | Distribution summary |
| `node-alert-check` | `0 * * * *` (hourly) | Node economics |
| `kylian-weekly-plan-check` | `30 19 * * 0` (Friday 7:30 PM) | Kylian next week |
| `kylian-daily-homework-check` | `0 7 * * 1-5` (Mon-Fri 7 AM) | Kylian homework |
| `kylian-friday-plan-check` | `0 18 * * 5` (Friday 6 PM) | Kylian Friday |

### System Crontab (managed via `crontab -e`)

```
*/15 * * * * /home/raspberry/external-ip-monitor.sh >> /tmp/external-ip-monitor.log 2>&1
*/15 * * * * /home/raspberry/node_monitor_full.sh >> /tmp/node_monitor_full.log 2>&1
0 0 * * * /home/raspberry/daily_ip.sh
0 4 * * * openclaw plugins update @martian-engineering/lossless-claw >> /tmp/lossless-claw-update.log 2>&1
0 5 * * 0 npm install -g agent-browser >> /tmp/agent-browser-update.log 2>&1
0 5 * * 0 agent-browser install --force >> /tmp/agent-browser-chromium.log 2>&1
```

---

## Systemd Services Summary

| Service | File | Purpose |
|---------|------|---------|
| `openclaw-gateway.service` | `systemd/openclaw-gateway.service` | Main OpenClaw gateway |
| `kepler-proxy.service` | `systemd/kepler-proxy.service` | Tax tool proxy (port 3000) |
| `cloudflared-tunnel.service` | `systemd/cloudflared-tunnel.service` | Cloudflare tunnel |

---

## Pushover Integration (monitoring alerts)

- **Token:** `[REDACTED]`
- **User:** `[REDACTED]`
- **Location:** `~/.openclaw/.secrets/monitoring.env`

---

## What's NOT Backed Up (must be re-entered manually)

These are intentionally NOT backed up for security:
- GitHub personal access token (restore via `git-credentials.enc` or manually)
- Encryption password (stored in `.backup_password` — without it, encrypted files are unrecoverable!)
- Wallet private keys (in `wallet-backup/` — encrypted, same `.backup_password`)

**Before disaster strikes:**
1. ✅ Know your GitHub token
2. ✅ Know the encryption password (in `.backup_password`)
3. ✅ Test the restore process on a spare SD card

---

## If Pi Dies — Quick Checklist

- [ ] Clone repo: `git clone https://github.com/colombiastaking/alice-backup.git ~/.openclaw/alice-backup`
- [ ] Install packages
- [ ] Decrypt all `.enc` files (need password from `.backup_password`)
- [ ] Restore plaintext files
- [ ] Restore systemd services + crontab
- [ ] Rebuild MCP server (`npm run build`)
- [ ] Start services
- [ ] Verify everything works

---

## Questions?

If something is unclear or missing from this guide, update this file and commit!
