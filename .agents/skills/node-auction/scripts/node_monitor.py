#!/usr/bin/env python3
"""
Node Monitor for Colombia Staking
Checks if adding a validator node is economically viable.

NOTIFICATION RULES:
- ADD alert: Only if EGLD/(nodes+1) > market_price + 20 EGLD
- REMOVE alert: If EGLD/nodes < market_price
- Otherwise: HOLD (no notification)

This ensures a 20 EGLD safety margin above market price before notifying ADD.
"""

import requests
import json
import sys
from datetime import datetime, timezone

PROVIDER = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf"
IDENTITY = "colombiastaking"

API_BASE = "https://api.multiversx.com"
COINGECKO = "https://api.coingecko.com/api/v3/simple/price?ids=elrond-erd-2&vs_currencies=usd"

def get_egld_price():
    try:
        r = requests.get(COINGECKO, timeout=10)
        data = r.json()
        return float(data['elrond-erd-2']['usd'])
    except:
        return None

def get_provider_info():
    try:
        r = requests.get(f"{API_BASE}/providers/{PROVIDER}", timeout=10)
        return r.json()
    except:
        return None

def get_identity_nodes():
    try:
        r = requests.get(f"{API_BASE}/identities/{IDENTITY}", timeout=10)
        data = r.json()
        return int(data.get('validators', 0))
    except:
        return 0

def get_market_threshold():
    """Get lowest qualified stake from auction list."""
    try:
        r = requests.get(f"{API_BASE}/nodes?from=0&size=2000&auctionList=true", timeout=30)
        nodes = r.json()
        
        # API returns list directly, not dict with 'nodes' key
        if isinstance(nodes, dict):
            nodes = nodes.get('nodes', [])
        
        # Filter qualified nodes in auction
        qualified = [n for n in nodes if isinstance(n, dict) and n.get('auctionQualified', False)]
        if not qualified:
            return None
        
        # Sort by qualifiedStake ascending
        qualified.sort(key=lambda x: float(x.get('qualifiedStake', 999999)))
        lowest = qualified[0]
        return float(lowest.get('qualifiedStake', 0)) / 10**18
    except:
        return None

def main():
    price = get_egld_price()
    provider = get_provider_info()
    nodes = get_identity_nodes()
    market = get_market_threshold()
    
    if not all([price, provider, market]):
        print("❌ Failed to fetch data")
        sys.exit(1)
    
    total_staked = float(provider.get('locked', 0)) / 10**18
    
    if nodes <= 0:
        print("❌ No active nodes found for identity")
        sys.exit(1)
    
    # MAX NODES CAP: Cannot exceed 50 nodes per entity
    MAX_NODES = 50
    at_max_nodes = nodes >= MAX_NODES
    
    egld_per_node = total_staked / nodes
    egld_if_add = total_staked / (nodes + 1)
    
    # 20 EGLD margin on top of market price
    margin_threshold = 20.0
    notification_threshold = market + margin_threshold
    
    # Decisions
    can_add = (egld_if_add > notification_threshold) and not at_max_nodes
    need_remove = egld_per_node < market
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━")
    print("🔷 **COLOMBIA STAKING NODE MONITOR**")
    print(f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print()
    print(f"💰 EGLD: ${price:,.2f}")
    print()
    print("📊 **STAKE:**")
    print(f"   Total: {total_staked:,.2f} EGLD")
    print(f"   Value: ${total_staked * price:,.0f}")
    print(f"   Nodes: {nodes}")
    if at_max_nodes:
        print(f"   ⚠️  MAX NODES: {MAX_NODES} — Cannot add more")
    print(f"   Per node: {egld_per_node:,.2f} EGLD")
    print()
    print(f"⚡ **MARKET PRICE:** {market:,.2f} EGLD")
    print(f"   → ADD if EGLD/{nodes+1} > {notification_threshold:,.2f} (market + {margin_threshold} EGLD)")
    print(f"   → REMOVE if EGLD/{nodes} < {market:,.2f}")
    if at_max_nodes:
        print(f"   → ADD BLOCKED: Max {MAX_NODES} nodes reached")
    print()
    print("💎 **CALCULATION:**")
    print(f"   {total_staked:,.2f} / {nodes} = {egld_per_node:,.2f} EGLD/node")
    print(f"   {total_staked:,.2f} / {nodes+1} = {egld_if_add:,.2f} EGLD/node")
    print(f"   Market price: {market:,.2f} EGLD")
    print(f"   Notification threshold: {notification_threshold:,.2f} EGLD")
    if at_max_nodes:
        print(f"   Status: MAX NODES ({nodes}/{MAX_NODES}) — Add disabled")
    print()
    
    if can_add:
        margin = egld_if_add - notification_threshold
        verdict = f"🟢 ADD: Notify! per_node_if_add ({egld_if_add:,.2f}) > threshold ({notification_threshold:,.2f})"
        verdict += f"\n   Margin: +{margin:,.2f} EGLD above threshold"
    elif need_remove:
        verdict = f"🔴 REMOVE: per_node ({egld_per_node:,.2f}) < market ({market:,.2f})"
    else:
        gap = notification_threshold - egld_if_add
        verdict = f"🟡 HOLD: per_node_if_add ({egld_if_add:,.2f}) ≤ threshold ({notification_threshold:,.2f})"
        verdict += f"\n   Gap: {gap:,.2f} EGLD below 20 EGLD margin"
        if at_max_nodes:
            verdict += f"\n   Also blocked: Max nodes reached ({nodes}/{MAX_NODES})"
    
    print(f"🎯 **VERDICT:**")
    print(f"   {verdict}")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    # Save state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_staked": total_staked,
        "nodes": nodes,
        "max_nodes": MAX_NODES,
        "at_max_nodes": at_max_nodes,
        "egld_per_node": egld_per_node,
        "market_price": market,
        "notification_threshold": notification_threshold,
        "margin_threshold": margin_threshold,
        "egld_if_add": egld_if_add,
        "can_add": can_add,
        "need_remove": need_remove,
        "egld_price": price
    }
    
    with open('/tmp/node_monitor_state.json', 'w') as f:
        json.dump(state, f, indent=2)
    
    # Write alert if notification needed
    if can_add or need_remove:
        with open('/tmp/node_monitor_alerts.txt', 'a') as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {verdict}\n")
    
    return state

if __name__ == '__main__':
    main()
