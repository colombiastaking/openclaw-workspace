---
name: cols-distribution
description: |
  COLS (Colombia Staking) daily token distribution system.
  Use when: (1) running daily distribution, (2) troubleshooting failed distributions,
  (3) checking distribution status, (4) re-running missed distributions, (5) understanding
  the three-pool system (BONUS/GOLD/DAO), (6) checking blockchain transactions.
---

# COLS Distribution Skill

Daily COLS token distribution system for Colombia Staking rewards.

## Overview

The distribution runs **every day at 1:10 PM Colombia time** via OpenClaw cron. The cron does a **preview only** (`calc`) and reports to Sebas. **No transactions are sent without explicit approval.**

### Three Pool System

| Pool | Recipients | Amount | Contract |
|------|------------|--------|----------|
| **BONUS** | COLS stakers | 2/3 of buyback | ESDT transfers to stakers |
| **GOLD** | Gold NFT holders | Daily rebate | ESDT transfers to NFT holders |
| **DAO** | PeerMe | 1/3 of buyback | Single tx to PeerMe contract |

## Cron Job

| Job ID | Schedule | Purpose |
|--------|----------|---------|
| `76f919d1-306a-4f32-ba29-1e44c737cb67` | 1:10 PM daily | Runs `run_distribution_cron.sh` → `execute_distribution_fixed.cjs` |
| `807e54ab-c369-428a-8415-bc7c8dae2c16` | 1:15 PM daily | Posts summary to Telegram group |

**Current flow:** Cron automatically executes distribution (not preview-only). Uses `agentTurn` trigger for reliability. State files prevent double-execution.

**⚠️ Warning:** Previously used `systemEvent` payload which was unreliable — always use `agentTurn` for distribution cron.

## Distribution Flow

```
Daily 1:10 PM (auto):
    bash run_distribution.sh calc
    → Announces preview to Sebas's DM
    → Waits for "yes" approval

If approved:
    yes | bash run_distribution.sh execute
    → Sends DAO + BONUS + GOLD on-chain
```

## Key Files

### Scripts
| Script | Purpose |
|--------|---------|
| `run_distribution.sh` | Bash orchestrator: `calc`, `execute`, `gold` commands |
| `run_distribution_cron.sh` | OpenClaw cron entry point (runs `calc` then `execute` if approved) |
| `execute_distribution_fixed.cjs` | **Main distribution script** — DAO + BONUS + GOLD combined with on-chain verification |
| `calculate_gold_distribution.mjs` | Calculate GOLD pool per NFT holder |

### Output Files (in `/tmp/cols_distribution/`)
| File | Content |
|------|---------|
| `bonus_distribution_YYYY-MM-DD.json` | BONUS calculations (recipients + amounts) |
| `gold_distribution_YYYY-MM-DD.json` | GOLD calculations (NFT holders + amounts) |
| `results_YYYY-MM-DD.json` | On-chain transaction results (hashes) |
| `gold_nft_owners.json` | Current Gold NFT owner list |
| `state.json` | Execution state |
| `gold_state.json` | GOLD execution state |

### Logs
| File | Content |
|------|---------|
| `/tmp/cols_distribution_cron.log` | Full execution log |

## Manual Run

### Preview only (no TXs)
```bash
cd ~/.openclaw/workspace/DAPP-V3/scripts
bash run_distribution.sh calc
```

### Full distribution (requires approval)
```bash
cd ~/.openclaw/workspace/DAPP-V3/scripts
bash run_distribution.sh calc          # Preview first
yes | bash run_distribution.sh execute  # Then execute
```

### Individual pools
```bash
# GOLD only
node calculate_gold_distribution.mjs
yes | bash run_distribution.sh gold

# BONUS dry-run
node execute_bonus_distribution_v3.cjs --dry-run
```

### Check last distribution
```bash
ls -la /tmp/cols_distribution/results_*.json | tail -3
cat /tmp/cols_distribution/results_YYYY-MM-DD.json
```

## BONUS Calculation Formula

```
Ratio = (COLS_stake × COLS_price) / (EGLD_stake × EGLD_price)
Normalized = (Ratio - min) / (max - min)
APR_bonus = binary_search(normalized)  // from APR lookup table
Daily_bonus = (APR_bonus / 100) × EGLD_stake × EGLD_price / 365 / COLS_price
```

**Key parameters:**
- Base APR: ~8.45%
- Service fee: 10%
- Max bonus: ~15% APR (for highest ratio stakers)

## Blockchain Contracts

| Contract | Address |
|----------|---------|
| Delegation Manager | `erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf` |
| PeerMe Entity | `erd1qqqqqqqqqqqqqpgq7khr5sqd4cnjh5j5dz0atfz03r3l99y727rsulfjj0` |
| PeerMe Claim | `erd1qqqqqqqqqqqqqpgqjhn0rrta3hceyguqlmkqgklxc0eh0r5rl3tsv6a9k0` |
| COLS Token | `COLS-9d91b7` |
| Distribution Wallet | `erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy` |

## ⚠️ CRITICAL: Wallet Private Key

**The distribution wallet key is NOT the same as the MCP server key.**

| Wallet | Key | Address |
|--------|-----|---------|
| **Distribution** (COLS sends) | `[REDACTED - see wallet_raw.enc]` | `erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy` |
| **MCP server** (alice-mcp-multiversx) | `[REDACTED - see wallet_raw.enc]` | `erd1j8dn54q9wmzdydr5llmsst2wgll42aj9psrpz2h0n8ud6ak3xkusxewvne` |

**Private key file location:** `/home/raspberry/.openclaw/wallet/.private_key` (raw 64-char hex)

**Key restoration history (2026-04-26):**
- Original PEM was lost after a gateway crash
- Key `bf17d85f...` was recovered from `secrets.enc` (WALLET_PRIVATE_KEY field)
- Previous attempts used the wrong conversion from PEM → hex
- Always use the raw hex from `secrets.enc` as source of truth

**⚠️ Never overwrite the private key without verifying the address it generates.**

## Troubleshooting

### Distribution didn't run today
1. Check cron status: `openclaw cron list` → look for `cols-distribution`
2. Run manually: `cd ~/.openclaw/workspace/DAPP-V3/scripts && bash run_distribution.sh calc`
3. Check results: `ls -la /tmp/cols_distribution/*.json`

### Some recipients didn't get tokens
1. Check results file: `cat /tmp/cols_distribution/results_YYYY-MM-DD.json | jq '.failed'`
2. Re-run with state cleared: `rm /tmp/cols_distribution/gold_state.json`
3. **Rate limit issue (2026-04-26):** MultiversX API returns 429 after ~73 calls. The dedup check has retry logic with exponential backoff (5 attempts). If still hitting 429, recipients are skipped to avoid double-pay — they miss the distribution.
4. To re-run skipped recipients: `node execute_distribution_fixed.cjs --bonus --force`

### Transaction failures
1. Check log for errors: `grep -i error /tmp/cols_distribution_cron.log`
2. Verify wallet has sufficient COLS
3. Check nonce issues: `cat /tmp/cols_distribution/state.json`

### State file issues (already distributed today)
```bash
# View state
cat /tmp/cols_distribution/state.json
cat /tmp/cols_distribution/gold_state.json

# Reset to allow re-run
rm /tmp/cols_distribution/state.json
rm /tmp/cols_distribution/gold_state.json
rm /tmp/cols_distribution/results_YYYY-MM-DD.json
```

### Key mismatch (wrong address derived)
1. Verify key: `cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx && node -e "const {UserSecretKey}=require('@multiversx/sdk-core'); const sk=UserSecretKey.fromString(require('fs').readFileSync('/home/raspberry/.openclaw/wallet/.private_key','utf8').trim()); console.log(sk.generatePublicKey().toAddress().toBech32());"`
2. Should return: `erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy`
3. If wrong: restore from `secrets.enc` or `alice-backup/wallet_raw.enc`

## Distribution Summary Format

Preview announced to Sebas's DM:

```
🎀 COLS Distribution Preview — 2026-04-26
━━━━━━━━━━━━━━━━━━━━━━
📦 BONUS Pool: 24.20 COLS → 104 recipients
💰 GOLD Pool: 4.32 COLS → 21 recipients
🏦 DAO Pool: 12.08 COLS → PeerMe
━━━━━━━━━━━━━━━━━━━━━━
💵 Total: 40.60 COLS
Wallet: 490.82 COLS available

Say "yes" to execute, or "no" to skip.
```
