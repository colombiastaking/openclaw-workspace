#!/usr/bin/env python3
"""
MultiversX Node Monitor for Colombia Staking - Simple Version

Logic:
- EGLD per node = Total Staked / 48
- If EGLD/(nodes+1) > threshold → CAN ADD node
- If EGLD/nodes < threshold → NEED TO REMOVE node
"""

import requests
from datetime import datetime

PROVIDER_ADDRESS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf"
IDENTITY_NAME = "colombiastaking"  # For fetching validator count

def get_identity_info():
    """Get Colombia Staking identity info including validator count"""
    try:
        r = requests.get(f"https://api.multiversx.com/identities/{IDENTITY_NAME}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                'validators': data.get('validators', 48),
                'stake': int(data.get('stake', 0)) / 10**18,
                'topUp': int(data.get('topUp', 0)) / 10**18
            }
    except:
        pass
    return None

def get_egld_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": "elrond-erd-2", "vs_currencies": "usd"}, timeout=10)
        return float(r.json()["elrond-erd-2"]["usd"]) if r.status_code == 200 else None
    except:
        return None

def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": "bitcoin", "vs_currencies": "usd"}, timeout=10)
        return float(r.json()["bitcoin"]["usd"]) if r.status_code == 200 else None
    except:
        return None

def get_provider_info():
    """Get provider stake info"""
    try:
        r = requests.get(f"https://api.multiversx.com/providers/{PROVIDER_ADDRESS}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            stake = int(data.get('stake', 0)) / 10**18
            topup = int(data.get('topUp', 0)) / 10**18
            return stake + topup, data.get('apr', 0)
    except:
        pass
    return None, None

def get_market_threshold():
    """Get the market price to enter the auction/validator queue
    
    This is the qualifiedStake of the LOWEST qualified node.
    To enter the queue and get a spot, you need to stake at least this much.
    
    MultiversX uses 'qualifiedStake' field which is different from stake + topUp.
    The qualifiedStake includes the auction top-up and determines eligibility.
    """
    try:
        r = requests.get("https://api.multiversx.com/nodes?size=2000", timeout=15)
        if r.status_code == 200:
            data = r.json()
            auction = [n for n in data if n.get('auctioned')]
            qualified = [n for n in auction if n.get('auctionQualified')]
            
            if not qualified:
                return None
            
            # Get the LOWEST qualified node by qualifiedStake - this is the market threshold
            # IMPORTANT: Use qualifiedStake field, NOT stake + topUp (they can differ!)
            by_qualified = sorted(qualified, key=lambda x: int(x.get('qualifiedStake', 0)))
            lowest = by_qualified[0]
            qualified_stake = int(lowest.get('qualifiedStake', 0)) / 10**18
            return qualified_stake
    except:
        pass
    return None

def check():
    """Check if we need to add or remove nodes"""
    
    print("🔷 Fetching data...")
    
    # Get all data
    identity = get_identity_info()
    total_staked, apr = get_provider_info()
    market_price = get_market_threshold()
    egld_price = get_egld_price()
    btc_price = get_btc_price()
    
    if identity is None:
        return "❌ Could not fetch identity info", None
    
    total_nodes = identity['validators']
    
    if total_staked is None or market_price is None:
        return "❌ Could not fetch data", None
    
    # Calculate
    egld_per_node = total_staked / total_nodes
    
    # Can we add? Check if adding one more node would still be above market price
    egld_with_extra = total_staked / (total_nodes + 1)
    can_add = egld_with_extra > market_price
    
    # Do we need to remove? Check if current per-node is below market price
    need_remove = egld_per_node < market_price
    
    # Calculate margins
    margin_add = egld_with_extra - market_price if can_add else 0
    margin_remove = egld_per_node - market_price if need_remove else 0
    
    # Action decision
    actions = []
    if need_remove:
        actions.append(f"🔴 REMOVE: EGLD/node ({egld_per_node:.2f}) is BELOW market price ({market_price:.2f})")
    elif can_add:
        actions.append(f"🟢 ADD: Can add 1 node (EGLD/(nodes+1) = {egld_with_extra:.2f} > {market_price:.2f})")
    else:
        actions.append("🟡 HOLD: No action needed")
    
    # Status
    status = []
    status.append("━━━━━━━━━━━━━━━━━━━━")
    status.append("🔷 **COLOMBIA STAKING NODE MONITOR**")
    status.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    status.append("")
    egld_str = f"${egld_price:,.2f}" if egld_price else "$N/A"
    btc_str = f"${btc_price:,.0f}" if btc_price else "$N/A"
    status.append(f"💰 EGLD: {egld_str} | BTC: {btc_str}")
    status.append("")
    status.append("📊 **STAKE:**")
    status.append(f"   Total: {total_staked:,.2f} EGLD")
    if egld_price:
        status.append(f"   Value: ${total_staked * egld_price:,.0f}")
    else:
        status.append(f"   Value: $N/A")
    status.append(f"   Nodes: {total_nodes}")
    status.append(f"   Per node: {egld_per_node:.2f} EGLD")
    status.append("")
    status.append(f"⚡ **MARKET PRICE:** {market_price:.2f} EGLD")
    status.append(f"   → Add if EGLD/(nodes+1) > {market_price:.2f}")
    status.append(f"   → Remove if EGLD/nodes < {market_price:.2f}")
    status.append("")
    status.append("💎 **CALCULATION:**")
    status.append(f"   {total_staked:,.2f} / {total_nodes} = {egld_per_node:.2f} EGLD/node")
    status.append(f"   {total_staked:,.2f} / {total_nodes+1} = {egld_with_extra:.2f} EGLD/node")
    status.append(f"   Market price: {market_price:.2f} EGLD")
    status.append("")
    status.append("🎯 **VERDICT:**")
    for a in actions:
        status.append(f"   {a}")
    status.append("━━━━━━━━━━━━━━━━━━━━")
    
    report = "\n".join(status)
    
    # Save state
    with open("/tmp/node_monitor_alerts.txt", "w") as f:
        if actions:
            f.write("\n".join(actions))
        else:
            f.write("NO_ALERTS")
    
    with open("/tmp/node_monitor_state.json", "w") as f:
        import json
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_staked": total_staked,
            "nodes": total_nodes,
            "egld_per_node": egld_per_node,
            "market_price": market_price,
            "can_add": can_add,
            "need_remove": need_remove,
            "egld_price": egld_price
        }, f, indent=2)
    
    return report, actions

if __name__ == "__main__":
    report, actions = check()
    if report:
        print("\n" + report)
    else:
        print("✅ NO ACTION NEEDED")
