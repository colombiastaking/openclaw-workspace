# MEMORY.md - Long-term Memory

## Kepler API Proxy (Tax Tool) - CRITICAL SETUP

**Problem:** After reboot, `/tmp/` is cleared, killing `kepler-proxy.js` → tax tool breaks.

**Fix Applied (2026-03-28):**
- Moved `kepler-proxy.js` from `/tmp/` to `/home/raspberry/.openclaw/kepler/kepler-proxy.js`
- Updated systemd service `kepler-proxy.service` to point to new location
- Updated `start-tax-services.sh` script

**Cloudflare Tunnel:**
- Tunnel: `6429a054-ec31-4f78-9b17-059e14ac58be`
- Hostname: `colombia-staking.co`
- All routes (`/api`, `/gateway`, `/es`, `/tax-query`, `/delegation`, `/images`) → port 3000
- Landing page (`/`): `network-explorer/public/index.html` (landing page with navbar + links)
- Network explorer (`/network/*`): `network-explorer/public/network.html` (full canvas explorer)

**kepler-proxy Routes:**
| Path | Source |
|------|--------|
| `/` | network-explorer/public/index.html |
| `/network/*` | network-explorer/public/ |
| `/network-data.json` | network-explorer/data/ (collector output) |
| `/images/*` | Website/eng/images/ |
| `/colombia-staking/*` | DApp-V3/build/ |
| `/api/*`, `/gateway/*` | → kepler-api.projectx.mx |
| `/tax-query`, `/delegation` | Internal |

**If tax tool breaks:**
1. Check if `kepler-proxy.service` is running: `systemctl --user status kepler-proxy`
2. If not, check if file exists: `ls -la /home/raspberry/.openclaw/kepler/kepler-proxy.js`
3. If missing, copy from backup: `cp ~/.openclaw/alice-backup/kepler-proxy.js ~/.openclaw/kepler/`
4. Restart: `systemctl --user restart kepler-proxy`

**API Key:** `acea534bc927840076692374ffab66fb`

---

## Alice MCP MultiversX Server (Installed 2026-03-30)

**What:** MultiversX MCP server giving Alice typed tools for blockchain operations via Model Context Protocol.

**Setup:**
- Repo: `https://github.com/colombiastaking/alice-mcp-multiversx` (private)
- Location: `/home/raspberry/.openclaw/workspace/alice-mcp-multiversx/`
- Skill: `~/.openclaw/workspace/.agents/skills/alice-mcp-multiversx/`
- Wallet: `erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy`
- Config: `~/.mcporter/mcporter.json`
- mcporter v0.7.3

**If server shows offline:**
```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx && npm run build && mcporter list
```

**Quick test:**
```bash
mcporter call multiversx.get-balance address:erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy
mcporter call multiversx.query-account address:erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy
```

**⚠️ mcporter CLI Integer Limitation:** mcporter parses `amount:10000000000000` as JS number (>2^53 loses precision). For write TX, use direct Node.js call:
```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send-egld","arguments":{"receiver":"<erd1>","amount":"10000000000000000"}}}' | \
  MVX_NETWORK=mainnet MVX_SIGNING_MODE=pem MVX_WALLET_PEM=/home/raspberry/.openclaw/wallet/.private_key \
  node dist/index.js mcp
```

---

## Node Monitoring Infrastructure

### Two Monitoring Systems (Separate)

**1. node_monitor_full.sh (Health - Every 15 min)**
- Location: `/home/raspberry/node_monitor_full.sh`
- System crontab: `*/15 * * * *`
- Checks: HTTP health (CPU, RAM, peers, sync) via port 80/8008
- Alerts: Pushover (DOWN, DESYNC, low peers)
- 4 local validator nodes only

**2. external-ip-monitor.sh (Connectivity - Every 15 min)**
- Location: `/home/raspberry/external-ip-monitor.sh`
- User crontab: `*/15 * * * *`
- Checks: TCP port connectivity (nc -z)
- Alerts: Pushover (after 2 consecutive failures = 30 min)
- 7 nodes monitored:

| Node | IP | Port | Notes |
|------|-----|------|-------|
| Shard0 | 192.168.0.120 | 55332 | Colombia LAN |
| Shard1 | 192.168.0.121 | 55336 | Colombia LAN |
| Shard2 | 192.168.0.122 | 55333 | Colombia LAN |
| Metachain | 192.168.0.124 | 55338 | Colombia LAN |

**Note:** VPS observers (ChagnaieBlanc/ChagnaieNoir/ExternalJuju) were removed from monitoring on 2026-04-21 — Network Explorer now uses only the 4 local LAN nodes.

**Pushover Credentials (both scripts):**
- Token: `anyqi8u1ze9y7w7dxjdh59kssdemgw`
- User: `c7TnDGDLohUS4JzFbxaMcqk2TXBnGs`

**Log files:**
- `/tmp/external_monitor.log`
- `/tmp/external_fail_counts.json` (consecutive failure tracking)

---

## Agent Delegation Strategy (Implemented 2026-04-14)

**Core principle:** Delegate everything possible to free up main for decisions, wallet operations, and direct conversations.

### Three-Agent Setup (All run on Raspberry Pi) — Updated 2026-04-15

| Agent | Model | Context Window | Role | Thinking |
|-------|-------|---------------|------|----------|
| **main** (Alice) | minimax-m2.7:cloud | 204,800 | Coordinator — you + wallet + chain + decisions | Off |
| **researcher** | kimi-k2.5:cloud | 262,144 | Data tasks, reports, research, monitoring | Off |
| **coder** | glm-5.1:cloud | 202,752 | Complex architecture, debugging, heavy builds | On |

**All agents:** Local Pi via Ollama (cloud-proxied models). No external compute.

### Delegated Cron Jobs (All on researcher)

| Job | Schedule | What it does |
|-----|----------|-------------|
| Network Explorer collector | Hourly (`0 * * * *`) | Runs `node server/collector.js` — updates DB + network-data.json |
| BTC Daily Strategy | 8 AM daily | Reads skill → runs master.py + decision engine → sends report to you |
| COLS Distribution summary | 1:15 PM daily | Reads distribution JSONs → posts summary to ColombiaStakingChat group |

### What stays on main
- All on-chain transactions (wallet access required)
- COLS Tax Withdrawal (weekly Mondays 9 AM)
- Decisions with financial impact
- New architecture/design conversations
- Direct messages from you

### Delegation principles
- **Delegate if:** repetitive, data-driven, no wallet access needed, no decision required
- **Keep on main if:** on-chain, financial, creative direction, direct conversation
- **Use coder for:** medium+ debugging, new features, smart contracts, heavy rewrites
- **Use researcher for:** reports, monitoring, research, script execution, data processing

### Skill delegation mapping
| Skill | Best handled by |
|-------|----------------|
| btc-strategy | researcher (daily execution) |
| cols-distribution | researcher (daily execution) |
| node-auction | researcher (monitoring) |
| multiversx-smart-contracts | coder |
| multiversx-dapp-frontend | coder |
| multiversx-dapp-audit | coder |
| kepler-proxy | main (infra) |
| cpanel-update | main (infra + FTP) |
| network-explorer | coder (architecture) |
| btc-monitor | researcher (daily runs) |

---

## Pending Items

- ~~Distribution script bug (March 27 bonus didn't go through)~~
- COLS distribution execution (1:10 PM daily) — still on main, needs wallet
- MSAL OAuth2 setup for Kylian Teams token (auto-refresh) — **REMOVED** (2026-03-29, token couldn't be refreshed)
- Current Kylian plan: "Semana 24-27 de Marzo" (from March 20) — **AUTOMATIONS REMOVED**

---

## Google Calendar - Familia

**Calendar ID:** `5039a61867c5d3d735ff81f91523004e48651cf6b94fd8afc54117da62f2023b@group.calendar.google.com`

**OAuth2 Tokens:** `/home/raspberry/.openclaw/workspace/google-tokens.json`
- Client ID: `495724051011-3l4qn60jg22fl181o1e8dpjibm1j3n62.apps.googleusercontent.com`
- Client Secret: `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`
- Scope: `https://www.googleapis.com/auth/calendar`
- Refresh token: long-lived (still valid as of 2026-03-29)

**Last cleaned:** 2026-03-29 (all old events deleted, calendar is now empty)

---

## Network Explorer (2026-04-14 — Sigma v2 + Mercator + Geo Circles)

**URL:** `https://colombia-staking.co/network/`
**Git repo:** `https://github.com/colombiastaking/network-explorer`
**Primary file:** `~/.openclaw/workspace/network-explorer/public/app.js`
**Serving:** Raspberry Pi → kepler-proxy.js (port 3000) → Cloudflare tunnel

**What it does:** Real-time MultiversX network visualization — 5,355 nodes, 4,821 edges.
- Sigma.js **v2** (NOT v3) with Graphology + ForceAtlas2
- **Web Mercator projection (EPSG:3857)** — nodes at real world lat/lng
- **Leaflet removed** — pure sigma canvas over CSS dark vector grid background
- IP-based clustering: one anchor node per IP at real geo position, cluster members orbit around via ForceAtlas2

**Mercator projection:**
```
x = (lng + 180) * (1440/360)
y = (mercY_raw(lat) - yN) / (yS - yN) * 820
where mercY_raw(lat) = ln(tan(π/4 + lat*π/360))
yN = mercY_raw(85), yS = mercY_raw(-85)
```
- y=0 → lat 85°N (top of map), y=820 → lat -85°S (bottom)
- Camera default: x=720, y=410, ratio=1.0 (world center, full Mercator world fits)
- Coordinate helpers: `_geoToSigma(lat, lng)` and `_sigmaToGeo(sx, sy)` stored as `this._toSigma` / `this._fromSigma`

**Sigma v2 constructor** (matching commit 167ac1a — last working version):
- `allowInvalidContainer: true`
- `enableWheelZoom: true`, `mouseWheelEnabled: true`
- `minCameraRatio: 0.05`, `maxCameraRatio: 20`
- **NO** `autoRescale`, `autoCenter` (v2 defaults are fine)
- `forceAtlas2Settings: { slowDown: 5, iterationsPerRender: 1 }` in constructor

**Init flow:** `init()` → `_doInit()` → `_loadData()` → `_bindEvents()` → `_applyFilters()` → `_rebuildSigma()` → `_initSigmaCore()`
- `_initSigmaCore()` creates Sigma, sets camera, starts ForceAtlas2
- **⚠ CRITICAL:** `init()` must `await this._loadData()` before Sigma init — or graph builds empty (black screen)

**Geo node locking during ForceAtlas2:**
- `isGeo: true` flag on anchor nodes (first node per IP)
- `_fx`/`_fy` frozen on tick 0, restored after each FA2 batch
- Cluster members (`isGeo: false`) freely move via ForceAtlas2 → form circles around anchor

**Bugs fixed 2026-04-14:**
1. `nodeClusterMap.has(n.bls)` → changed to `nodeClusterMap.has(anchorIp)` — old bug: every node was its own anchor (BLS always unique), now only first node per IP is the anchor
2. localStorage posCache was overriding Mercator positions → `const cached = geoPos ? null : posCache.get(n.bls)` skips cache restore for geo nodes
3. `_buildGraph()` used equirectangular formula for `ipGeoMap` → changed to `this._toSigma()` Mercator
4. Third old-formula instance at non-clustered geo node placement → replaced with `this._toSigma()`
5. `toSigma` was local const inside `__initSigmaCore` → stored as `this._toSigma` for `_buildGraph` access
6. Sigma constructor had invalid v3-only options → stripped back to v2-compatible options

**Edge types:**
- 🔴 Red = STEP A (direct P2P observed)
- 🔵 Blue = STEP B (identity multikey)
- 🟢 Green = STEP C (name keyword) / STEP D (location)
- ⚫ Black = Colombia NAT

**STEP C keywords:** vapor, partnerstaking, eapes, ms, fellowship, moonlorian, wavenode, ofero, meria, bober, mregld

**STEP D (geo matching):** For nodes still without IPs after STEP A+B+C, matches by physical location. Uses `_codeToCountry` map to resolve ISO codes (ES, RO) to full names (Spain, Romania) before matching.

**DB bloat fix (2026-04-12):**
- Added `UNIQUE(pid, ip, observer)` on `peer_observations` and `UNIQUE(observer, peer_pid)` on `edge_observations`
- VACUUM after each dedup → stable at ~14-20 MB
- Cron: `0 * * * *` (hourly)

**DB schema:**
- `api_nodes`: ~5,339 rows (bls, name, identity, provider, shard)
- `node_observations`: ~1,400 rows (pid→bls/name/shard/type, **NO identity column**)
- `peer_observations`: ~12,000 rows (deduped)
- `edge_observations`: ~9,700 rows (deduped)
- `geo_cache`: ~561 rows (ip→country/city/org via ip-api.com)

**⚠ Known issues:**
- VPS SSH passphrase: never committed (always used `${SSH_KEY_PASSPHRASE}` env var in Python exec strings since the start) — ✅ CLEAN
- IPINFO_TOKEN (`1d04296b0e5756`): was hardcoded in collector.js lines 955 & 1722 — **REMOVED via git filter-repo** (2026-04-17). Replaced with `process.env.IPINFO_TOKEN || ''`. GitHub history now shows `***REMOVED***` for old commits. Token stored in `/home/raspberry/.openclaw/.env` ✅
- `edge_observations` table missing `step` column — needs DB migration
- esm.sh CDN dependency — consider bundling with esbuild

**Deploy:** `git add -A && git commit -m "..." && git push` → live immediately

---

## Backup System

**Location:** `~/.openclaw/alice-backup/`
**Repo:** `https://github.com/colombiastaking/alice-backup`
**Schedule:** Daily 6 PM via system cron (`backup.sh`)
**Password:** stored in `.backup_password`

**Smart features (since 2026-04-15):**
- Change detection: compares git diff since last commit → reports what changed
- Secrets drop folder: `~/.openclaw/.secrets/` → auto-encrypted in backups
- BACKUP_INDEX.md: auto-updated after each backup with change log + inventory
- Encrypted: wallet, tokens, credentials, config, memory, Telegram, secrets folder

**Drop secrets here:** `~/.openclaw/.secrets/` (auto-included in encrypted backup)

**Recovery:** See `RESTORE.md` in the alice-backup repo for full procedure.

---

## GitHub Repos

All modifications to these repos MUST be committed and pushed to GitHub:

| Repo | Local Path | Purpose |
|------|-----------|---------|
| `colombiastaking/DAPP-V3` | `workspace/DAPP-V3/` | Colombia Staking DApp |
| `colombiastaking/Website` | `workspace/Website/` | Website (3 languages: eng, esp, fr) |
| `colombiastaking/btc-strategy` | `workspace/btc-strategy/` | BTC AI strategy |
| `colombiastaking/network-explorer` | `workspace/network-explorer/` | Network explorer visualization |
| `colombiastaking/alice-backup` | `.openclaw/alice-backup/` | Disaster recovery backup |
| `colombiastaking/tax-report-payment` | `workspace/tax-report-payment/` | Tax payment smart contract (Rust/WASM) |

**Rule:** After ANY modification to any of these, immediately commit and push to the relevant repo.

**Auto-push already configured:**
- `alice-backup`: Daily at 6:00 PM via `alice-daily-backup` cron
- `btc-strategy`: Daily reports auto-commit to GitHub

**Manual push required for:**
- DAPP-V3 changes
- Website changes
- tax-payment-smart-contract changes
- network-explorer changes
- Any other repo not covered by auto-backup

---

---

## Website/DApp cPanel Incident (2026-04-15)

**What happened:** During cleanup of junk folders from bad uploads, the DApp's `build/` folder was wiped and the EN/ES site files were in wrong nested folders. The DApp was left with a white screen.

**Root causes:**
1. `cleanup_junk.py` ran recursively and wiped `build/` when processing `__MACOSX.DELETEME` on the DApp
2. EN site files (`eng/`) and ES site files (`esp/`) were uploaded to wrong nested paths during earlier parallel upload attempts
3. DApp `index.html` was at `/build/index.html` instead of root `/staking.colombia-staking.com/index.html`
4. Stale `assets/` files (old hash filenames) persisted on server from previous deploys

**Correct server structure (confirmed working):**
```
colombia-staking.com/ (main hosting via cPanel)
  /public_html/                    ← EN site (index.html at root)
  /esp.colombia-staking.com/       ← ES site (index.html at root)
  /fr.colombia-staking.com/        ← FR site (index.html at root)
  /staking.colombia-staking.com/   ← DApp (index.html at ROOT, NOT in build/)
    index.html, manifest.json, node_status.json, etc.
    assets/                          ← JS/CSS bundles (at root, not in build/)
    leagues/                        ← images
```

**Never again:**
- Never recursively delete `*DELETEME*`, `__MACOSX`, `*zombie*` patterns on live server without verifying the path doesn't contain live content
- Always check `build/` folder before any DApp cleanup — it may be the live DApp location
- DApp `index.html` lives at root, not in `build/`
- After DApp restore, re-upload `build/assets/` to confirm correct hash filenames
- EN/ES/FR site files go DIRECTLY to FTP root path (already contains language folder)

**Skill updated:** `~/.openclaw/workspace/.agents/skills/cpanel-update/SKILL.md`

---

## Ledger BTC Position (Integrated 2026-04-08)

**xpub:** `xpub6CjqJTKYKEYHJxJWePZ44hAM5EDrJ58sJLDWgNGcbRd2VKmHo8UPRJQbtBeaMZpA1BpByPXdge5wxcVtbJMKAnEhNtGWcC584EJc8Ba7gWS`
**Derivation:** BIP84 Native SegWit — m/84'/0'/0'/0/i
**Known funded address:** `bc1qa90vtxkj0umyfzs5m2cr3n4c8f5pxnenfah4e0` (index 26)
**Balance:** ~0.058 BTC (5,844,519 sats) — confirmed via blockstream + xpub derivation

**Integration:** Since 2026-04-08, `btc_strategy_master.py` runs `ledger_btc_tracker.py` and adds Ledger BTC to total holdings for HF calculations and Telegram report display.

**Files:**
- Tracker: `/home/raspberry/.openclaw/workspace/btc-monitor/ledger_btc_tracker.py`
- Master script: `/home/raspberry/.openclaw/workspace/btc-strategy/scripts/btc_strategy_master.py`

---

## Network Explorer — Data Folder Consolidation (2026-04-16)

**Problem:** Multiple `data/` folders causing confusion and data loss risk.

- `data/` — correct location, held real files
- `public/data/` — stale orphaned copy (gitignored empty placeholder, never updated by collector)
- `server/data/` — empty placeholder files (collector writes to `../data/` not `server/data/`)


**Also:** Path mismatch in `research-sync.js` — it wrote to `server/data/research-db.json` but `collector.js` reads from `data/research-db.json`. The file got lost during today's cleanup.

**Fixes applied:**
1. Restored `research-db.json` with 74 provider countries via `research-sync.js`
2. Fixed `scripts/research-sync.js` path → writes to `data/` (matches `collector.js`)
3. Cleaned up empty `server/data/` placeholder files
4. Symlink no longer needed — file now in correct `data/` location

**Current structure:**
```
network-explorer/
  data/
  ├── network_explorer.db   (live DB)
  ├── network-data.json      (live, 4373 geo nodes)
  ├── network-data-backup.json
  ├── identity-country-map.json (72 entries)
  └── research-db.json         (74 manualIntel countries ✅)
  public/
  └── network-data.json       (served live at /network/)
  server/
  └── (empty, no data files)
```

**Map health:** 4,373 nodes with geo ✅

**Git commit:** `9009234` — "fix: consolidate data folders + restore research-db.json"


---

## DApp FTP Access & .htaccess Fix (2026-04-18)

### FTP Credentials (4 separate accounts)

| Site | User | Password | Status |
|------|------|----------|--------|
| **DApp** staking.colombia-staking.com | `AliceDapp@staking.colombia-staking.com` | `vXQln+-JsMLNz)0V` | ✅ Working |
| **EN** colombia-staking.com | `AliceEng@colombia-staking.com` | `0w3ikUp^?k,1s@ET` | ✅ Working |
| **ES** esp.colombia-staking.com | `AliceEsp@esp.colombia-staking.com` | `?jTL&[YOwIoo#Pmh` | ❌ No home dir |
| **FR** fr.colombia-staking.com | `AliceFr@fr.colombia-staking.com` | `qy+EN{rqa.u;9.%` | ❌ No home dir |

**Credentials stored at:** `~/.openclaw/secrets/.ftp_credentials`

### DApp 404 Fix (CRITICAL)

**Problem:** DApp routes (`/tools`, `/lock`, etc.) returned 404. Root `/` worked.

**Root cause:** `.htaccess` file was corrupted during upload with old credentials.

**Fix:**
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

**After uploading ANY file to DApp:** Always re-upload .htaccess to clear LiteSpeed cache.

### DApp Endpoints
| Tool | DApp Route | API Endpoint |
|------|------------|--------------|
| BTC Strategy | `/tools` | `https://colombia-staking.co/btc-report/summary` |
| Tax Report | `/tools` | `https://colombia-staking.co/tax-query?address=...` |

Both route through kepler-proxy (port 3000) → cloudflared → Pi.

---

## BTC Report DApp — Fixes (2026-04-19)

### Bug 1: Black page when report not available
**Problem:** API returns `{"error": "Report not available yet..."}` but component tried to render `report.score.toFixed(1)` → TypeError crash.

**Fix in `BTCReportTool.tsx`:** Added error check in fetchBTCReport `.then()`:
```typescript
if ('error' in data) {
  setError(data.error as string);
  setIsLoading(false);
  return;
}
```

**Commited:** `daa31c9` - "fix(BTCReportTool): handle API error response when report not available yet"

### Bug 2: DApp fully broken after rebuild
**Problem:** Uploaded new `index.html` referencing new JS files (`index-6ea07f4a.js`) but didn't upload the new JS files → 'text/html is not valid JavaScript' MIME type error.

**Fix:** Upload all new build assets alongside index.html.

### BTC Report Service (btc-general-report)
- **Service:** `btc-general-report.service` (systemd user service)
- **Script:** `/home/raspberry/.openclaw/workspace/btc-general-report/generate_report.py`
- **Data source:** `/tmp/btc_decision_alert.json` (from `btc_decision_engine.py`)
- **Cache file:** `/tmp/btc_general_report.json`
- **Endpoint:** `http://localhost:3000/btc-report/summary` → served via kepler-proxy

**If report shows "not available":**
1. Run decision engine: `python3 /home/raspberry/.openclaw/workspace/scripts/btc_decision_engine.py`
2. Restart service: `systemctl --user restart btc-general-report`

---

## Daily Strategy Report — Message Splitting Fix (2026-04-19)

**Problem:** Cron job failed with "message is too long" (400 Bad Request).

**Fix in `scripts/daily_strategy_report.py`:** Added `send_telegram()` splitting for messages > 4000 chars.

---

## Last Updated

- 2026-04-22: Website paths fixed — EN was uploading to wrong directory (`/colombia-staking.com/` instead of `/public_html/`). Videos fixed (ES/FR). About pages updated with live node count and infrastructure cards. OpenClaw updated to 2026.4.21.
- 2026-04-19: BTC Report DApp fixed — error handling for unavailable report, DApp redeploy missing JS files, message splitting for Telegram.
- 2026-04-18: Network Explorer data folder consolidation — research-db.json restored with 74 provider countries, map back to 4,373 geo nodes.
- 2026-04-15: Agent delegation strategy fully implemented — researcher handles BTC strategy, COLS summary, Network Explorer collector. main now freed for wallet/chain/decisions only.
- 2026-04-14: Network Explorer fully rebuilt — Sigma v2 (not v3), Mercator projection, geo circles (anchor per IP), nodeClusterMap fix, posCache fix, all old equirectangular formulas replaced with `this._toSigma()`.

---

## Website Deployment — Python FTPS (2026-04-21, FIXED 2026-04-22)

**Deploy script:** `~/.openclaw/workspace/scripts/deploy-website.py` (Python ftplib.FTP_TLS)
```bash
python3 ~/.openclaw/workspace/scripts/deploy-website.py all   # All 3 sites + DApp
python3 ~/.openclaw/workspace/scripts/deploy-website.py en   # EN only
python3 ~/.openclaw/workspace/scripts/deploy-website.py dapp # DApp only
```

**Why Python instead of bash/curl?** curl/ftp CLI hangs on TLS negotiation (421 cleartext not accepted).
Python `ftplib.FTP_TLS` with `prot_p()` works every time.

**⚠️ CRITICAL PATH FIX (2026-04-22):** EN site was uploading to `/colombia-staking.com/` (WRONG) instead of `/public_html/` (CORRECT). LiteSpeed was serving stale cached files from public_html while new uploads went to the wrong directory.

**Server paths (from colombia6 root):**
```
colombia6@colombia-staking.com (root)
├── /public_html/                   ← EN site (index.html at ROOT, NOT in subdirectory)
├── /esp.colombia-staking.com/     ← ES site
├── /fr.colombia-staking.com/      ← FR site
└── /staking.colombia-staking.com/ ← DApp
```

**Credentials:** `colombia6/sMGi6hW3vikr` (stored in `~/.openclaw/secrets/.ftp_credentials`)

**Deploy status (2026-04-22):**
- EN site: ✅ live at `colombia-staking.com/` (embed=1, About infra cards, live node count)
- ES site: ✅ live at `esp.colombia-staking.com/` (video fixed, About infra cards)
- FR site: ✅ live at `fr.colombia-staking.com/` (video fixed, About infra cards)
- DApp: ✅ live at `staking.colombia-staking.com/`
- Videos: `colombia-20staking-2025-low.mp4` uploaded to ES/FR video/ directories (47MB each, HTTP 200)
- About pages: Live node count (49), infrastructure cards (5.75kW solar, 60 CPU cores, 9 machines, 4 ISPs)

**Git commits (2026-04-22):**
- `f4c99c2` — fix: EN site path was /colombia-staking.com instead of /public_html
- `516040c` — About page updates: live node count + infrastructure cards + video files

## cPanel API Token (Stored 2026-04-20)

**Token:** `6FI7UC2CSJKTDLX5499DAOI8NWPP8DKM`
**Stored at:** `~/.openclaw/.secrets/.cpanel_api_token`
**Included in:** Daily encrypted backup (AES-256)

**Limitation:** LiteSpeed API module not installed on server — cannot auto-purge cache via API.

## DApp FTP Access

**Working account:** `colombia6` (all sites)
**Credentials stored at:** `~/.openclaw/secrets/.ftp_credentials`

### DApp Endpoints
| Tool | DApp Route | API Endpoint |
|------|------------|--------------|
| BTC Strategy | `/tools` | `https://colombia-staking.co/btc-report/summary` |
| Tax Report | `/tools` | `https://colombia-staking.co/tax-query?address=...` |

Both route through kepler-proxy (port 3000) → cloudflared → Pi.
