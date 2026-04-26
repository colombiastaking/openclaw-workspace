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

| Job | Schedule | Purpose |
|-----|----------|---------|
| `cols-distribution` | 1:10 PM daily | Preview only — reports calculations, no TXs sent |

**⚠️ Important:** Cron runs preview (`bash run_distribution.sh calc`), announces to Sebas's DM, and waits for approval before any real TXs.

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

### Scripts (from commit abd9e3ea)
| Script | Purpose |
|--------|---------|
| `run_distribution.sh` | Bash orchestrator: `calc`, `execute`, `gold` commands |
| `execute_bonus_distribution_v3.cjs` | BONUS pool — SDK with on-chain TX verification |
| `execute_gold_distribution.cjs` | GOLD pool — SDK with state tracking |
| `execute_distribution.cjs` | DAO pool (PeerMe) + BONUS combined |
| `daily_distribution.mjs` | Calculate BONUS pool per staker |
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

## Troubleshooting

### Distribution didn't run today
1. Check cron status: `openclaw cron list` → look for `cols-distribution`
2. Run manually: `cd ~/.openclaw/workspace/DAPP-V3/scripts && bash run_distribution.sh calc`
3. Check results: `ls -la /tmp/cols_distribution/*.json`

### Some recipients didn't get tokens
1. Check results file: `cat /tmp/cols_distribution/results_YYYY-MM-DD.json | jq '.failed'`
2. Re-run with state cleared: `rm /tmp/cols_distribution/gold_state.json`

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
```

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
