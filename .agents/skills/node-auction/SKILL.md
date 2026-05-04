---
name: node-auction
description: |
  MultiversX node economics monitoring - ADD/REMOVE node decisions.
  Use when: (1) deciding whether to add or remove validator nodes, (2) checking auction/queue economics,
  (3) understanding the current market threshold to enter the validator set, (4) node economics questions,
  (5) checking Colombia Staking's current stake per node vs market price.
---

# Node Auction Skill

Economic monitoring for Colombia Staking validator node decisions.

## Core Logic

**Key Formula:**
```
EGLD_per_node = Total_Staked / Num_Nodes
```

**Notification Rules (20 EGLD Margin):**

| Condition | Calculation | Action |
|-----------|-----------|--------|
| ADD alert | `EGLD/(nodes+1) > market + 20` | 🟢 Notify |
| REMOVE alert | `EGLD/nodes < market` | 🔴 Notify |
| HOLD | Neither above | 🟡 No notification |

**Notification Threshold = market_price + 20 EGLD**

This ensures you only get ADD alerts when you have a solid 20 EGLD margin above market price.

## Colombia Staking Config

| Parameter | Value |
|-----------|-------|
| Provider Address | `erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf` |
| Identity | `colombiastaking` |
| Current Nodes | **48** |
| Auto-check | Hourly via `node-alert-check` cron |

## Quick Reference

| Item | Value |
|------|-------|
| **Script** | `~/.openclaw/workspace/.agents/skills/node-auction/scripts/node_monitor.py` |
| **Cron** | `node-alert-check` (every hour, OpenClaw) |
| **Alert Output** | `/tmp/node_monitor_alerts.txt` |
| **State File** | `/tmp/node_monitor_state.json` |
| **Decision** | HOLD / ADD / REMOVE |

## Manual Check

```bash
cd ~/.openclaw/workspace/.agents/skills/node-auction/scripts && python3 node_monitor.py
```

This will:
1. Fetch identity info (validator count)
2. Fetch total staked amount from provider
3. Fetch market threshold (lowest qualified node's qualifiedStake)
4. Calculate EGLD per node
5. Apply 20 EGLD margin rule
6. Determine ADD/REMOVE/HOLD
7. Print full report

## Example Output

```
━━━━━━━━━━━━━━━━━━━━
🔷 **COLOMBIA STAKING NODE MONITOR**
🕐 2026-05-04 13:12 UTC

💰 EGLD: $4.11

📊 **STAKE:**
   Total: 182,394.74 EGLD
   Value: $749,642
   Nodes: 48
   Per node: 3,799.89 EGLD

⚡ **MARKET PRICE:** 3,717.70 EGLD
   → Notify ADD if EGLD/(nodes+1) > 3,737.70 (market + 20 EGLD)
   → Notify REMOVE if EGLD/nodes < 3,717.70

💎 **CALCULATION:**
   182,394.74 / 48 = 3,799.89 EGLD/node
   182,394.74 / 49 = 3,722.34 EGLD/node
   Market price: 3,717.70 EGLD
   Notification threshold: 3,737.70 EGLD (market + 20)

🎯 **VERDICT:**
   🟡 HOLD: per_node_if_add (3,722.34) ≤ threshold (3,737.70)
   Gap: 15.36 EGLD below 20 EGLD margin
━━━━━━━━━━━━━━━━━━━━
```

## Decision Thresholds

```python
# 20 EGLD margin on top of market price
NOTIFICATION_THRESHOLD = market_price + 20.0

if egld_if_add > NOTIFICATION_THRESHOLD:
    action = "🟢 ADD ALERT"
elif egld_per_node < market_price:
    action = "🔴 REMOVE ALERT"
else:
    action = "🟡 HOLD (no alert)"
```

## Important Notes

1. **20 EGLD Buffer:** The notification only fires when the per-node value AFTER adding exceeds market price by at least 20 EGLD. This filters out minor fluctuations.

2. **qualifiedStake vs stake:** The market threshold uses `qualifiedStake` field, NOT `stake + topUp`. These can differ significantly due to auction dynamics.

3. **Queue Position:** Being in the auction list doesn't guarantee a slot. You need `qualifiedStake` >= the lowest qualified node.

4. **48 Nodes Fixed:** For now, Colombia Staking operates exactly 48 nodes. The ADD calculation assumes adding one more (49).

## API Sources

- Identity: `https://api.multiversx.com/identities/colombiastaking`
- Provider: `https://api.multiversx.com/providers/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf`
- Nodes: `https://api.multiversx.com/nodes?size=2000`
- Prices: `https://api.coingecko.com/api/v3/simple/price?ids=elrond-erd-2&vs_currencies=usd`

## Troubleshooting

### No alerts firing
1. Check cron status: `openclaw cron list` (look for `node-alert-check`)
2. Check last run: look at `lastRunStatus` in cron list
3. Manual run: `cd ~/.openclaw/workspace/.agents/skills/node-auction/scripts && python3 node_monitor.py`
4. Check state file: `cat /tmp/node_monitor_state.json`

### API failures
- All APIs are public (no auth needed)
- Check internet connectivity
- Try manual curl: `curl -s "https://api.multiversx.com/identities/colombiastaking" | jq`

### Alert not delivering
- Check Telegram connection
- Cron delivery status: `lastDelivered: true/false`
- If `not-delivered`, check `lastDeliveryStatus`
