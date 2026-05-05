#!/usr/bin/env python3
"""
Xpub Scanner — scans all BIP84 addresses from xpub
Updates btc-position.json with total balance
"""

import json
import hashlib
import requests
import time
import bech32
from bip_utils import Bip32Slip10Secp256k1

XPUB = "xpub6CjqJTKYKEYHJxJWePZ44hAM5EDrJ58sJLDWgNGcbRd2VKmHo8UPRJQbtBeaMZpA1BpByPXdge5wxcVtbJMKAnEhNtGWcC584EJc8Ba7gWS"
GAP_LIMIT = 20
MAX_INDEX = 200  # Safety limit

def pubkey_to_bech32(pub_key_bytes):
    sha256 = hashlib.sha256(pub_key_bytes).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()
    data = bech32.convertbits(ripemd160, 8, 5)
    return bech32.bech32_encode('bc', [0] + data) if data else None

def check_address(addr):
    try:
        resp = requests.get(f"https://mempool.space/api/address/{addr}", timeout=10)
        data = resp.json()
        funded = data['chain_stats']['funded_txo_sum']
        spent = data['chain_stats']['spent_txo_sum']
        balance = (funded - spent) / 1e8
        txs = data['chain_stats']['tx_count']
        mempool_funded = data.get('mempool_stats', {}).get('funded_txo_sum', 0)
        mempool_spent = data.get('mempool_stats', {}).get('spent_txo_sum', 0)
        mempool_bal = (mempool_funded - mempool_spent) / 1e8
        return balance + mempool_bal, txs
    except Exception:
        return 0, 0

def scan_chain(external, chain_name, start=0):
    total = 0
    funded = []
    gap = 0
    last_funded_idx = -1
    max_idx = start + MAX_INDEX
    
    for i in range(start, max_idx):
        child = external.ChildKey(i)
        pub_key = child.PublicKey().RawCompressed().ToBytes()
        addr = pubkey_to_bech32(pub_key)
        if not addr:
            continue
        
        bal, txs = check_address(addr)
        
        if bal > 0:
            funded.append({"index": i, "address": addr, "balance": bal})
            total += bal
            gap = 0
            last_funded_idx = i
        elif txs > 0:
            gap = 0
            last_funded_idx = i
        else:
            gap += 1
            if gap > GAP_LIMIT and last_funded_idx >= 0:
                break
        
        time.sleep(0.1)  # Rate limit
    
    return total, funded

def main():
    print("🔍 Scanning xpub addresses...")
    bip32_pub = Bip32Slip10Secp256k1.FromExtendedKey(XPUB)
    
    # Scan receiving (0) and change (1) chains
    external = bip32_pub.ChildKey(0)
    recv_total, recv_addrs = scan_chain(external, "receiving")
    print(f"  Receiving addresses: {recv_total:.8f} BTC ({len(recv_addrs)} funded)")
    
    change = bip32_pub.ChildKey(1)
    chg_total, chg_addrs = scan_chain(change, "change")
    print(f"  Change addresses: {chg_total:.8f} BTC ({len(chg_addrs)} funded)")
    
    grand_total = recv_total + chg_total
    
    # Get current BTC price
    btc_price = 75000
    try:
        r = requests.get("https://mempool.space/api/v1/prices", timeout=10)
        btc_price = r.json().get("USD", 75000)
    except:
        pass
    
    # Update btc-position.json
    position = {
        "source": "ledger",
        "btc_holding": round(grand_total, 8),
        "btc_address": recv_addrs[0]["address"] if recv_addrs else "",
        "xpub": XPUB,
        "derivation": "BIP84 Native SegWit — m/84'/0'/0'/0/i",
        "last_updated": time.strftime("%Y-%m-%d"),
        "last_scan": {
            "receiving_addresses": recv_addrs,
            "change_addresses": chg_addrs,
            "total_balance": round(grand_total, 8),
            "btc_price_usd": btc_price,
            "total_usd": round(grand_total * btc_price, 0)
        },
        "notes": "Ledger cold storage. Funds spread across multiple receiving and change addresses. Auto-scanned via xpub."
    }
    
    with open("/home/raspberry/.openclaw/workspace/btc-position.json", "w") as f:
        json.dump(position, f, indent=2)
    
    print(f"\n📊 Total: {grand_total:.8f} BTC (${grand_total * btc_price:,.0f})")
    print(f"✅ Saved to btc-position.json")

if __name__ == "__main__":
    main()
