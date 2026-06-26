# MEMORY.md - Long-term Memory

## ⚠️ CRITICAL: Keep this file ≤12,000 chars

## Active Mission: Lagos Harbor Survey (2026-05)

**Mission:** Snake Island Port Pre-Dredging Survey  
**Vessel:** Bitam  
**Client:** DEME / ITB Nigeria  
**IHO Order:** Special Order  
**Hydrographer:** Sébastien (Cat A, 15 years)  
**Assistant:** Alice (Mission Recorder)  
**Status:** PRE-DEPLOYMENT

**Project path:** `~/.openclaw/workspace/missions/2026-05-LAGOS-HARBOR-GABON/`  
**Mission diary:** `MISSION-DIARY.md` (master log, auto-updated)  
**Daily notes:** `daily-notes/YYYY-MM-DD/`

**Alice's role:** Full-time mission assistant. Register all field data (photos, calibrations, sketches, benchmarks, systems), compile reports, maintain diary, flag missing info. Autonomous updates — Sebas feeds data, Alice organizes. Sebas is Cat A hydrographer — Alice follows technical decisions, asks only when genuinely unclear.

---

## Kepler Proxy (Tax Tool)

**Location:** `/home/raspberry/.openclaw/kepler/kepler-proxy.js`
**Service:** `kepler-proxy.service` (systemd user)
**API Key:** `acea534bc927840076692374ffab66fb`
**Upstream:** `kepler-api.projectx.mx`

**Cloudflare Tunnel:** `6429a054-ec31-4f78-9b17-059e14ac58be` → `colombia-staking.co`
Routes: `/api`, `/gateway`, `/es`, `/tax-query`, `/delegation`, `/images` → port 3000

**If broken after reboot:**
1. `systemctl --user status kepler-proxy`
2. If missing: `cp ~/.openclaw/alice-backup/kepler-proxy.js ~/.openclaw/kepler/`
3. `systemctl --user restart kepler-proxy`

---

## OpenClaw Agent Setup

**Single model:** `ollama/kimi-k2.6:cloud` — all tasks, no agent splitting.

**Web search:** `ollama` (via `http://127.0.0.1:11434/api/experimental/web_search`) — default provider, enabled for all research queries.

**Cron jobs run as subagents** (same model, isolated context):
- BTC strategy (11 AM daily)
- COLS distribution summary (~1:15 PM daily)
- Network Explorer collector (hourly)

---

## Alice MCP MultiversX

**Wallet:** `erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt`
**Config:** `~/.mcporter/mcporter.json`

**⚠️ Write TX — use Node.js directly (mcporter CLI loses precision on large integers):**
```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send-egld","arguments":{"receiver":"<erd1>","amount":"10000000000000000"}}}' | \
  MVX_NETWORK=mainnet MVX_SIGNING_MODE=pem MVX_WALLET_PEM=/home/raspberry/.openclaw/wallet/.private_key \
  node dist/index.js mcp
```

---

## Node Monitoring

**Scripts:** `/home/raspberry/node_monitor_full.sh` (system cron, 15 min) + `/home/raspberry/external-ip-monitor.sh` (user cron, 15 min)

| Node | IP | Port |
|------|-----|------|
| Shard0 | 192.168.0.120 | 55332 |
| Shard1 | 192.168.0.121 | 55336 |
| Shard2 | 192.168.0.122 | 55333 |
| Metachain | 192.168.0.124 | 55338 |

**Pushover:** token=`[REDACTED]` / user=`[REDACTED]` (see `~/.openclaw/.secrets/monitoring.env`)

---

## Network Explorer

**URL:** `https://colombia-staking.co/network/`
**Repo:** `https://github.com/colombiastaking/network-explorer`
**Data:** `~/.openclaw/workspace/network-explorer/data/network-data.json` (~4,400 geo nodes)
**DB:** `~/.openclaw/workspace/network-explorer/data/network_explorer.db` (~15 MB)
**Collector:** Hourly via researcher cron

**Key:** Sigma v2 + Mercator projection. Cluster members orbit anchor nodes at real geo coords.

---

## Website / DApp Deploy

**Script:** `~/.openclaw/workspace/scripts/deploy-website.py`
**Account:** `[REDACTED]` (password in `~/.openclaw/.env`)

| Site | Path |
|------|------|
| EN | `/public_html/` |
| ES | `/esp.colombia-staking.com/` |
| FR | `/fr.colombia-staking.com/` |
| DApp | `/staking.colombia-staking.com/` |

**Deploy:** `python3 deploy-website.py en` (or `es`, `fr`, `dapp`, `all`)
**⚠️ EN uploads to `/public_html/` — NOT `/colombia-staking.com/`**

---

## GitHub Repos

| Repo | Path |
|------|------|
| DAPP-V3 | `workspace/colombia-staking/DAPP-V3/` |
| Website | `workspace/colombia-staking/Website/` |
| network-explorer | `workspace/network-explorer/` |
| btc-strategy | `workspace/.agents/skills/btc-strategy/` |
| alice-backup | `.openclaw/alice-backup/` |

---

## Backup System

**Location:** `/home/raspberry/alice-backup/`
**Script:** `/home/raspberry/alice-backup/backup.sh`
**Schedule:** Daily 18:00 (system cron)
**Log:** `/tmp/alice-backup.log`
**Password:** in `/home/raspberry/alice-backup/.backup_password` (not in git)
**Drop secrets:** `~/.openclaw/.secrets/` (auto-included, encrypted — includes `telegram.env`, `monitoring.env`, `github_token`)
**GitHub:** `https://github.com/colombiastaking/alice-backup`
**Restore:** See `RESTORE.md` in alice-backup repo.

**Last verified backup:** 2026-06-18 08:22 — commit `59ad00b`, all critical files present.

---

## Google Calendar - Familia

**Calendar ID:** `5039a61867c5d3d735ff81f91523004e48651cf6b94fd8afc54117da62f2023b@group.calendar.google.com`
**Tokens:** `~/.openclaw/workspace/google-tokens.json`

---

## BTC / Ledger

**xpub:** `xpub6CjqJTKYKEYHJxJWePZ44hAM5EDrJ58sJLDWgNGcbRd2VKmHo8UPRJQbtBeaMZpA1BpByPXdge5wxcVtbJMKAnEhNtGWcC584EJc8Ba7gWS`
**Derivation:** BIP84 Native SegWit — m/84'/0'/0'/0/i
**Known funded:** `bc1qa90vtxkj0umyfzs5m2cr3n4c8f5pxnenfah4e0` (index 26)

**8 AM Telegram report now includes personal finance (2026-06-15):**
- BTC holdings in EUR
- Colombia Staking monthly income from on-chain provider data (provider + personal 1,250 EGLD delegation)
- Apartment rental income (3 apartments in Colombia, COP → EUR live rate)
- Monthly spendings: €1,825
- Freelance income gap and self-sustaining %
- Provider: `erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf`

---

## Deployment Rule

**After EVERY website/DApp FTP deploy → immediately commit + push to GitHub.**
Never skip this step. Repos:
- DAPP-V3 → `colombiastaking/DAPP-V3`
- Website → `colombiastaking/Website`
- Network Explorer → `colombiastaking/network-explorer`

## Pending Items

- BTC report cron (8 AM) — sometimes missed if gateway restarts mid-window
- COLS distribution (1:10 PM daily) — needs wallet on main
- Workspace git pile — many uncommitted changes (node monitor, BTC position, website/DApp updates, missions, DXF files, memory files)
- MEMORY.md oversize — keep trimmed to ≤12k chars
