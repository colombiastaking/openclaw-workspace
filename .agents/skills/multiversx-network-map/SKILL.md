---
name: multiversx-network-map
description: MultiversX blockchain network map explorer — Sigma.js v3 WebGL force graph visualization with graphology. Use when working with the MultiversX Network Explorer at colombia-staking.co/network/ or when asked to work on the network map, graph view, node topology, or validator visualization. Also use for any changes to the explorer UI, data collection pipeline, or website integration.
---

# MultiversX Network Map

Interactive Sigma.js v3 WebGL force-directed graph of the MultiversX validator/observer network with **real P2P edges** from 8 observer nodes.

**Live:** `https://colombia-staking.co/network/`

---

## Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│  Raspberry Pi (raspberry.local)                               │
│                                                                 │
│  /home/raspberry/.openclaw/workspace/network-explorer/        │
│      ├── public/                  ← served to browsers         │
│      ├── data/                    ← collector writes here      │
│      │   ├── network-data.json                                 │
│      │   └── network_explorer.db  ← SQLite (~14-20 MB stable) │
│      └── server/                                               │
│          ├── collector.js       ← main data collector           │
│          ├── db.js              ← SQLite persistence layer     │
│          └── serve.js           ← dev static server :8081       │
│                                                                 │
│  kepler-proxy.js (port 3000) ─ serves /network/ → public/     │
│  Cloudflare Tunnel ──────────────→ colombia-staking.co/network/│
└─────────────────────────────────────────────────────────────────┘
```

**The Network Explorer is served from the Raspberry Pi, NOT from the VPS.**

### How data flows

```
Colombia LAN observers ───┐
VPS observers via SSH ────┼──→ collector.js ──→ SQLite DB ──→ network-data.json ──→ public/
(82.66.243.38:8080-8083) │        │
                          │        ▼
                          └────────┘ (each run INSERTs then DEDUPs immediately)
```

**Data sync:** `collector.js` writes output to `data/network-data.json`. The web server (kepler-proxy.js) serves from `public/network-data.json`. After every collector run, the file is synced automatically.

---

## Observers — 8 Total

| Observer | Source | Endpoint | Notes |
|----------|--------|----------|-------|
| Colombia-Shard0 | LAN | `192.168.0.120:80` | Direct LAN |
| Colombia-Shard1 | LAN | `192.168.0.121:8008` | Direct LAN |
| Colombia-Shard2 | LAN | `192.168.0.122:8008` | Direct LAN |
| Colombia-Metachain | LAN | `192.168.0.124:8008` | Direct LAN |
| VPS-Shard0 | SSH | `82.66.243.38:55332 → localhost:8080` | Via SSH tunnel |
| VPS-Shard1 | SSH | `82.66.243.38:55332 → localhost:8081` | Via SSH tunnel |
| VPS-Shard2 | SSH | `82.66.243.38:55332 → localhost:8082` | Via SSH tunnel |
| VPS-Metachain | SSH | `82.66.243.38:55332 → localhost:8083` | Via SSH tunnel |

**VPS SSH credentials:**
- Key: `/home/raspberry/.ssh/nodes-juju`
- Passphrase: `NKYhPiVpr9sWyioC7CRAfqgQmy8`
- User: `nodes-juju`
- Port: `55332`
- VPS nodes run as systemd units: `elrond-node-0` through `elrond-node-3`
- Observer REST ports (8080-8083) are bound to localhost only

---

## Running the Collector

```bash
cd /home/raspberry/.openclaw/workspace/network-explorer
bash run.sh
```

**Collector run time:** ~70-120s

**Cron schedule:** Hourly via OpenClaw cron `network-explorer-collector` (`0 * * * *`). **Never run more than once per hour** — each run dedups immediately and the DB stays stable.

---

## Architecture

```
network-explorer/
├── public/
│   ├── index.html          ← explorer UI shell (Sigma.js v3)
│   ├── app.js              ← NetworkExplorer class (ESM, ~980 lines)
│   └── style.css
├── server/
│   ├── collector.js       ← fetches from 8 observers, writes to SQLite + JSON
│   ├── db.js               ← SQLite persistence (better-sqlite3)
│   └── serve.js            ← dev static server :8081
├── data/
│   ├── network-data.json   ← ~9MB JSON, rebuilt from DB each run
│   └── network_explorer.db ← permanent SQLite history (~14-20 MB stable)
└── run.sh                  ← wrapper (auto-syncs data → public/)
```

---

## Four Edge Types (Sigma.js rendering)

| Color | Meaning | Source | How assigned |
|-------|---------|--------|--------------|
| 🔴 Red | Real P2P peer → IP anchor | Peer BLS → `ext:IP` diamond | STEP A: direct peer observation |
| 🔵 Blue | Multikey IP assignment | Node BLS → `ext:IP` diamond | STEP B: identity multikey (round-robin) |
| 🟢 Green | Location-matched IP | Node BLS → `ext:IP` diamond | STEP D: geo-location country match |
| ⚫ Black | Synthetic Colombia NAT | Colombia observer BLS | Hardcoded `186.99.3.198` |

**Green edges (STEP D)** were added 2026-04-12 to fix providers whose validators are in a country where the network has observer presence but no direct IP match was found via STEP B/C.

**IP diamond nodes:** Diamond-shaped nodes representing public IPs seen in peerinfo.

**Blue edge behavior — important:** Blue edges aggregate ALL IPs from ALL observers of an identity across ALL shards and distribute round-robin. This means if provider X has observers on shards 0, 1, and 2, ALL of X's validators get IPs from ALL 3 shards. This is working as designed — it's not a bug. Many different providers legitimately share the same IPs at shared datacenter/VPS providers (OVH, DigitalOcean, Hetzner, etc.).

---

## Four-Pass IP Assignment System

### STEP A — Direct PID→IP (via peer_observations)
Nodes observed directly as P2P peers get their IPs from `peer_observations` table. Produces **red edges**.

### STEP B — Identity Multikey (API-based grouping)
Groups API nodes by `identity` field. For each identity group, finds observer nodes in peer data that match that identity (via stripped name or `identity` field), then propagates their IPs to **all** nodes in the group (all shards) via round-robin. Produces **blue edges**.

### STEP C — Name-Keyword Matching
For nodes still without IPs after STEP A+B, uses keyword extraction from `node_observations.name` to match against known provider patterns. Produces **green edges** (fallback).

**STEP_C_KEYWORDS:**
```javascript
const STEP_C_KEYWORDS = [
  'vapor', 'partnerstaking', 'eapes', 'ms', 'fellowship',
  'moonlorian', 'wavenode', 'ofero', 'meria', 'bober', 'mregld', 'inception'
];
```

### STEP D — Location-Based IP Assignment
For nodes **still** without IPs after STEP A+B+C, matches by physical location. If a multikey provider's validators are in a country where the observer network has IPs, STEP D round-robins those IPs across all validators of that provider in that country.

**LOCATION_TO_COUNTRIES:**
```javascript
const LOCATION_TO_COUNTRIES = {
  'Spain': ['ES'],
  'Romania': ['RO'],
  // ...
};
```

**Name normalization (shared by STEP B, C, D):**
- Strips numeric suffixes: `TrustStaking-63` → `truststaking`
- Handles bare observers: `TrustStaking` → `truststaking`
- Handles `.tld` suffix: `smartchainconnection.com` → `smartchainconnection`
- **Strips hyphens:** `fellowship-07` and `fellowship-staking` both normalize to `fellowship`
- Handles `identityKey.` prefix stripping

**BLS dedup fix:** When the same BLS key appears in both API nodes and peer data, the merge prefers the non-empty `identity`.

**STEP D fix (2026-04-12):** Was comparing ISO codes (`"ES"`) against full country names (`"Spain"`) — always failed silently. Fixed via `_codeToCountry` reverse map.

---

## SQLite Database (db.js)

**Location:** `data/network_explorer.db`

**DB size:** ~14-20 MB (stable, VACUUMed after each dedup pass)

**Schema:**
```sql
peer_observations   -- pid, ip, observer → UNIQUE constraint prevents duplicates
edge_observations  -- observer ↔ peer_pid → UNIQUE constraint prevents duplicates
node_observations  -- pid → bls, name, shard, type (no identity column!)
api_nodes          -- bls → name, identity, provider, shard, stake, etc.
observer_runs      -- collector run metadata
geo_cache          -- ip → country, region, city, latitude, longitude, org
```

**Row counts (after hourly dedup):**
| Table | Approx. rows |
|-------|-------------|
| api_nodes | ~5,339 |
| node_observations | ~1,400 |
| peer_observations | ~12,000 |
| edge_observations | ~9,700 |
| observer_runs | ~24/day |
| geo_cache | ~553 |

**Deduplication (2026-04-12):**
- `peer_observations`: `UNIQUE(pid, ip, observer)` — insert then delete dupes (keeps oldest ts)
- `edge_observations`: `UNIQUE(observer, peer_pid)` — insert then delete dupes
- VACUUM run after each dedup to reclaim free pages

**⚠️ `node_observations` has NO `identity` column.** Schema is `ts, pid, bls, name, shard, type, source`. Any query for `node_observations.identity` will throw `SqliteError: no such column: identity`. Identity must be looked up via `api_nodes` (via `pidToInfo`) or from peer data enrichment.

---

## Sigma.js v3 Critical API Notes

⚠️ **Camera is an EventEmitter** — use `.on()`, NOT `addEventListener()`.

```javascript
// ✅ CORRECT
camera.on('updated', handler);
sigma.on('clickNode', ({ node }) => { ... });

// ❌ WRONG
camera.addEventListener('coordinatesUpdated', handler);
```

```javascript
// Camera state
camera.ratio;              // zoom ratio (NOT camera.position.z!)
camera.isAnimated();       // true if animating (NOT isMoving())
camera.animatedReset();    // reset with animation

// ForceAtlas2 import — must use direct .mjs URL
import('https://esm.sh/graphology-layout-forceatlas2@0.10.1/es2022/graphology-layout-forceatlas2.mjs?target=es2022')
// assign is a named export on the module, NOT on .default
```

---

## Frontend Edge Rendering (app.js)

**Edge color logic:**
- `edge.isColombiaNode === true` → 🟢 green (Colombia NAT synthetic)
- `edge.isMultikey === true` → 🔵 blue (multikey STEP B)
- Otherwise → 🔴 red (direct P2P STEP A)

**Edge size:** green=1.2, blue=0.8, red=1.0

**Edge attributes:** `isRealP2P`, `isMultikeyP2P`, `isColombiaNatP2P`

**Node→edge mapping:** `blsToNode[edge.peerBls]` lookup finds the peer node; `peerNode.isColombia` flags Colombia nodes.

**Shard display:** `getShardKey()` converts `shard === 4294967295` (metachain sentinel) to `'meta'` for rendering.

---

## Mobile UI (Bottom Drawer)

**Structure:**
- ⚙ filter button (bottom-right, shown only ≤768px)
- Sidebar transforms to fixed bottom drawer (55vh, slides up)
- Tap overlay or ✕ Close to dismiss
- Tapping any filter chip auto-closes the drawer

**CSS breakpoints:**
- `≤768px`: sidebar → bottom drawer, ⚙ button visible
- `≤480px`: header compact (smaller logo, hidden subtitle/accent), stats values-only

---

## Known Issues

### 1. ⚠️ GitHub secret leak (commit `7683b61`)
The VPS SSH passphrase `NKYhPiVpr9sWyioC7CRAfqgQmy8` is permanently committed to GitHub in `collector.js`.
**Fix:** Generate a new SSH key pair on the VPS, update `collector.js` with the new public key, and send Alice the new private key via Telegram.

### 2. `ofero` — 0 green edges
Ofero has ~40 API nodes but 0 green edges because no observer PIDs in `node_observations` match the `ofero` keyword. The ofero observers may use a different naming pattern not captured by the STEP_C_KEYWORDS list.

### 3. `hasApiIdentity` guard in `findObserverIPsForGroup`
The `hasApiIdentity` check in `findObserverIPsForGroup` skips PIDs that are also validators (have a BLS key) even if they have no API identity but a valid name match. This affects STEP B only. STEP C bypasses this check entirely.

---

## Deployment

```bash
cd /home/raspberry/.openclaw/workspace/network-explorer

# Edit, commit and push
git add -A && git commit -m "describe change" && git push

# Sync is automatic via run.sh
```

**Stable commits (2026-04-12):**
| Commit | Change |
|--------|--------|
| `526f683` | Green edges for Colombia NAT synthetic connections (app.js) |
| `4c8ed2c` | STEP D geo normalization fix |
| `df99aeb` | DB UNIQUE constraints + dedup (current HEAD) |

---

## Check tunnel/proxy status

```bash
systemctl --user status cloudflared    # Cloudflare tunnel
systemctl --user status kepler-proxy  # Node.js proxy
systemctl --user restart cloudflared
systemctl --user restart kepler-proxy
```

## Check live data

```bash
curl -s https://colombia-staking.co/network/network-data.json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Nodes: {len(d[\"nodes\"])}, Edges: {len(d[\"allEdges\"])}')"
```

---

## Git

`https://github.com/colombiastaking/network-explorer`
