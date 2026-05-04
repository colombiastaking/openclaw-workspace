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

**Decision Rules:**
- If `EGLD_per_node < Market_Threshold` → **REMOVE node** (unprofitable)
- If `EGLD/(nodes+1) > Market_Threshold` → **ADD node** (economically viable)
- Otherwise → **HOLD**

**User Threshold:** If margin > 20 EGLD, consider ADD action

**Market Threshold** = The `qualifiedStake` of the lowest qualified auction node.
This is what you need to stake to secure a validator slot.

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
5. Determine ADD/REMOVE/HOLD
6. Print full report

## Decision Thresholds

| Condition | Action | Alert |
|-----------|--------|-------|
| `EGLD/nodes < market_threshold` | REMOVE | 🔴 Telegram alert |
| `EGLD/(nodes+1) > market_threshold + 20 EGLD margin` | ADD | 🟢 Telegram alert |
| `EGLD/(nodes+1) > market_threshold` but < 20 EGLD margin | HOLD (weak signal) | 🟡 No alert |
| Both false | HOLD | No alert |

## Cron Job

**Job:** `node-alert-check` (OpenClaw cron)
**Schedule:** Every hour at :00
**Behavior:**
- Runs `node_monitor.py`
- If output says "HOLD" → sends nothing
- If output says ADD with margin > 20 EGLD → sends Telegram alert to Sebas
- If output says REMOVE → sends Telegram alert to Sebas

## State File

Check `/tmp/node_monitor_state.json` for last run data:

```json
{
  "timestamp": "2026-05-04T13:12:00",
  "total_staked": 182394.74,
  "nodes": 48,
  "egld_per_node": 3799.89,
  "market_price": 3717.70,
  "margin": 82.19,
  "user_threshold": 20.0,
  "can_add": true,
  "need_remove": false,
  "egld_price": 4.11
}
```

## Example Output

```
━━━━━━━━━━━━━━━━━━━━
🔷 **COLOMBIA STAKING NODE MONITOR**
🕐 2026-05-04 13:12 UTC

💰 EGLD: $4.11 | BTC: $80,380

📊 **STAKE:**
   Total: 182,394.74 EGLD
   Value: $749,642
   Nodes: 48
   Per node: 3,799.89 EGLD

⚡ **MARKET PRICE:** 3,717.70 EGLD
   → Add if EGLD/(nodes+1) > 3,717.70 + 20 EGLD margin
   → Remove if EGLD/nodes < 3,717.70

💎 **CALCULATION:**
   182,394.74 / 48 = 3,799.89 EGLD/node
   182,394.74 / 49 = 3,722.34 EGLD/node
   Market price: 3,717.70 EGLD

🎯 **VERDICT:**
   🟢 ADD: Can add 1 node (margin = 82.19 EGLD > 20 EGLD threshold)
━━━━━━━━━━━━━━━━━━━━
```

## Margin Calculation

```python
margin = egld_per_node - market_price
if margin > user_threshold:
    alert = "🟢 ADD"
elif margin < -user_threshold:
    alert = "🔴 REMOVE"  
else:
    alert = "🟡 HOLD"
```

Default `user_threshold` = 20.0 EGLD

## Important Notes

1. **qualifiedStake vs stake:** The market threshold uses `qualifiedStake` field, NOT `stake + topUp`. These can differ significantly due to auction dynamics.

2. **Queue Position:** Being in the auction list doesn't guarantee a slot. You need `qualifiedStake` >= the lowest qualified node.

3. **48 Nodes Fixed:** For now, Colombia Staking operates exactly 48 nodes. The ADD calculation assumes adding one more (49).

4. **20 EGLD Threshold:** The notification only fires if margin > 20 EGLD. This prevents noise from minor fluctuations.

## API Sources

- Identity: `https://api.multiversx.com/identities/colombiastaking`
- Provider: `https://api.multiversx.com/providers/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf`
- Nodes: `https://api.multiversx.com/nodes?size=2000`
- Prices: CoinGecko API

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
