#!/usr/bin/env python3
"""
BTC Price Monitor for Aave V3 Position
Calculates dynamic BTC price thresholds based on current position
Alerts when BTC price drops to levels that risk the position
"""

import json
import requests
from datetime import datetime

WALLET = "0xb88da656FEe3CA19A70993684aDF1A7409ac37E6"
BLOCKSCOUT_API = "https://eth.blockscout.com/api/v2/addresses/{address}/tokens?type=ERC-20"

def get_blockscout_tokens(address):
    """Fetch all ERC-20 tokens from Blockscout"""
    url = BLOCKSCOUT_API.format(address=address)
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Blockscout API error: {e}")
    return None

def get_btc_price():
    """Get BTC price from CoinGecko with fallback to Binance"""
    # Try CoinGecko first
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=10
        )
        if response.status_code == 200:
            return float(response.json()["bitcoin"]["usd"])
        elif response.status_code == 429:
            print("CoinGecko rate limited")
    except Exception as e:
        print(f"CoinGecko error: {e}")
    
    # Fallback to Binance
    try:
        response = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        if response.status_code == 200:
            return float(response.json()["price"])
    except Exception as e:
        print(f"Binance fallback error: {e}")
    
    return None

def get_position():
    """Get current Aave position"""
    tokens_data = get_blockscout_tokens(WALLET)
    if not tokens_data or "items" not in tokens_data:
        return None, None
    
    collateral_btc = 0
    debt_usd = 0
    
    for item in tokens_data.get("items", []):
        token = item.get("token", {})
        symbol = token.get("symbol", "")
        value = int(item.get("value", 0))
        
        if symbol == "AWBTC" and value > 0:
            collateral_btc = value / 1e8  # 8 decimals
        elif symbol == "variableDebtEthUSDC" and value > 0:
            debt_usd = value / 1e6  # 6 decimals
    
    return collateral_btc, debt_usd

def calculate_btc_thresholds(collateral_btc, debt_usd):
    """Calculate BTC price thresholds for different HF levels"""
    if collateral_btc <= 0 or debt_usd <= 0:
        return None
    
    thresholds = {}
    
    # HF = (collateral_btc * btc_price * 0.78) / debt_usd
    # btc_price_at_hf = (HF * debt_usd) / (collateral_btc * 0.78)
    
    for hf_level, name in [(1.5, "caution"), (1.2, "warning"), (1.0, "danger")]:
        threshold = (hf_level * debt_usd) / (collateral_btc * 0.78)
        thresholds[name] = {
            "hf": hf_level,
            "btc_price": threshold
        }
    
    return thresholds

def check_alerts(btc_price, thresholds):
    """Check if current BTC price triggers any alerts"""
    alerts = []
    
    if btc_price <= thresholds["danger"]["btc_price"]:
        alerts.append({
            "level": "danger",
            "message": f"🔴 DANGER: BTC at ${btc_price:,.2f} - LIQUIDATION IMMINENT! (HF would be ~1.0)"
        })
    elif btc_price <= thresholds["warning"]["btc_price"]:
        alerts.append({
            "level": "warning", 
            "message": f"🟠 WARNING: BTC at ${btc_price:,.2f} - Position at risk! (HF would be ~1.2)"
        })
    elif btc_price <= thresholds["caution"]["btc_price"]:
        alerts.append({
            "level": "caution",
            "message": f"🟡 CAUTION: BTC at ${btc_price:,.2f} - HF dropping (would be ~1.5)"
        })
    
    return alerts

def format_report(btc_price, collateral_btc, debt_usd, thresholds, alerts):
    """Format the BTC monitoring report"""
    
    hf_current = (collateral_btc * btc_price * 0.78) / debt_usd if debt_usd > 0 else float('inf')
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "₿ **BTC PRICE MONITOR**",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"**Current BTC:** ${btc_price:,.2f}",
        "",
        "📊 **Position Thresholds:**",
        f"   🟡 HF 1.5 at: ${thresholds['caution']['btc_price']:,.2f}",
        f"   🟠 HF 1.2 at: ${thresholds['warning']['btc_price']:,.2f}",
        f"   🔴 HF 1.0 at: ${thresholds['danger']['btc_price']:,.2f}",
        "",
        f"📍 **Current HF:** {hf_current:.3f}",
    ]
    
    if alerts:
        lines.append("")
        lines.append("🚨 **ALERTS:**")
        for alert in alerts:
            lines.append(f"   {alert['message']}")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)

def save_state(btc_price, collateral_btc, debt_usd, thresholds, alerts):
    """Save current state"""
    
    state = {
        "timestamp": datetime.now().isoformat(),
        "btc_price": btc_price,
        "collateral_btc": collateral_btc,
        "debt_usd": debt_usd,
        "thresholds": {k: {"hf": v["hf"], "btc_price": v["btc_price"]} for k, v in thresholds.items()},
        "alerts": alerts
    }
    
    with open("/tmp/btc_monitor_state.json", "w") as f:
        json.dump(state, f, indent=2)
    
    with open("/tmp/btc_monitor_alerts.txt", "w") as f:
        if alerts:
            for alert in alerts:
                f.write(f"{alert['level']}: {alert['message']}\n")
        else:
            pass  # No alerts - file will be empty

def main():
    print("₿ Fetching BTC price and position data...")
    
    # Get data
    btc_price = get_btc_price()
    collateral_btc, debt_usd = get_position()
    
    if btc_price is None:
        print("❌ Could not fetch BTC price")
        return
    
    if collateral_btc is None or debt_usd is None:
        print("❌ Could not fetch position data")
        return
    
    print(f"   BTC Price: ${btc_price:,.2f}")
    print(f"   Collateral: {collateral_btc:.6f} BTC")
    print(f"   Debt: ${debt_usd:,.2f}")
    
    # Calculate thresholds
    thresholds = calculate_btc_thresholds(collateral_btc, debt_usd)
    
    print(f"\n📊 Threshold BTC prices:")
    print(f"   HF 1.5 (CAUTION): ${thresholds['caution']['btc_price']:,.2f}")
    print(f"   HF 1.2 (WARNING): ${thresholds['warning']['btc_price']:,.2f}")
    print(f"   HF 1.0 (DANGER): ${thresholds['danger']['btc_price']:,.2f}")
    
    # Check alerts
    alerts = check_alerts(btc_price, thresholds)
    
    # Format and print report
    report = format_report(btc_price, collateral_btc, debt_usd, thresholds, alerts)
    print("\n" + report)
    
    # Save state
    save_state(btc_price, collateral_btc, debt_usd, thresholds, alerts)
    
    if alerts:
        print("\n🚨 ALERTS TRIGGERED:")
        for alert in alerts:
            print(f"   {alert['message']}")

if __name__ == "__main__":
    main()
