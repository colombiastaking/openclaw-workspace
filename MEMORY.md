# MEMORY.md - Long-term Memory

## ⚠️ CRITICAL: Keep this file ≤12,000 chars

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

## OpenClaw Agents (3-agent setup)

| Agent | Model | Role |
|-------|-------|------|
| **main** | minimax-m2.7:cloud | Wallet, chain, decisions |
| **researcher** | kimi-k2.5:cloud | Data, reports, monitoring |
| **coder** | glm-5.1:cloud | Debugging, heavy builds |

**Delegated to researcher:** BTC strategy (8 AM), COLS summary (1:15 PM), Network Explorer collector (hourly)
**Delegated to coder:** Smart contracts, dApp frontend, complex debugging

---

## Alice MCP MultiversX

**Wallet:** `erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy`
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

**Pushover:** token=`anyqi8u1ze9y7w7dxjdh59kssdemgw` / user=`c7TnDGDLohUS4JzFbxaMcqk2TXBnGs`

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
**Account:** `colombia6 / sMGi6hW3vikr`

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

**Location:** `~/.openclaw/alice-backup/`
**Schedule:** Daily 6 PM (system cron `backup.sh`)
**Password:** in `.backup_password`
**Drop secrets:** `~/.openclaw/.secrets/` (auto-included, encrypted)
**Restore:** See `RESTORE.md` in alice-backup repo.

---

## Google Calendar - Familia

**Calendar ID:** `5039a61867c5d3d735ff81f91523004e48651cf6b94fd8afc54117da62f2023b@group.calendar.google.com`
**Tokens:** `~/.openclaw/workspace/google-tokens.json`

---

## BTC / Ledger

**xpub:** `xpub6CjqJTKYKEYHJxJWePZ44hAM5EDrJ58sJLDWgNGcbRd2VKmHo8UPRJQbtBeaMZpA1BpByPXdge5wxcVtbJMKAnEhNtGWcC584EJc8Ba7gWS`
**Derivation:** BIP84 Native SegWit — m/84'/0'/0'/0/i
**Known funded:** `bc1qa90vtxkj0umyfzs5m2cr3n4c8f5pxnenfah4e0` (index 26)

---

## Pending Items

- BTC report cron (8 AM) — sometimes missed if gateway restarts mid-window
- COLS distribution (1:10 PM daily) — needs wallet on main
- MEMORY.md oversize — keep trimmed to ≤12k chars
