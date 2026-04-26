#!/usr/bin/env python3
"""
BTC Strategy Master Script
Aggregates all BTC holdings (wallet + Ledger) and runs decision engine.
"""

import os, sys, json, subprocess

# Paths
LEDGER_TRACKER = "/home/raspberry/.openclaw/workspace/btc-monitor/ledger_btc_tracker.py"
LEDGER_STATE = "/tmp/ledger_btc_state.json"
AAVE_STATE = "/tmp/aave_btc_state.json"

def get_ledger_btc():
    """Run ledger tracker and return total BTC."""
    result = subprocess.run(
        ["/usr/bin/python3", LEDGER_TRACKER],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0 and os.path.exists(LEDGER_STATE):
        with open(LEDGER_STATE) as f:
            state = json.load(f)
        return state.get("total_btc", 0)
    return 0

def get_aave_btc():
    """Get Aave position BTC collateral."""
    if os.path.exists(AAVE_STATE):
        with open(AAVE_STATE) as f:
            state = json.load(f)
        return state.get("collateral_btc", 0)
    return 0

def main():
    print("₿ BTC Strategy Master")
    print("="*50)
    
    # Run ledger tracker
    print("\n📿 Fetching Ledger BTC...")
    ledger_btc = get_ledger_btc()
    print(f"   Ledger BTC: {ledger_btc:.8f}")
    
    # Get Aave position
    aave_btc = get_aave_btc()
    print(f"   Aave BTC: {aave_btc:.8f}")
    
    total_btc = ledger_btc + aave_btc
    print(f"\n💰 TOTAL BTC: {total_btc:.8f}")
    
    # Save combined state for decision engine
    state = {
        "timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
        "ledger_btc": ledger_btc,
        "aave_btc": aave_btc,
        "total_btc": total_btc
    }
    with open("/tmp/btc_strategy_state.json", "w") as f:
        json.dump(state, f, indent=2)
    
    return total_btc

if __name__ == "__main__":
    main()
