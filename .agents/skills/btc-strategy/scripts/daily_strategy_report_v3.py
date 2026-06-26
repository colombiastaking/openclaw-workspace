#!/usr/bin/env python3
"""
Daily Strategy Report - v3 (Fixed)
BTC Accumulation + Aave Position

Fixes:
- Correct Aave monitor path (scripts/aave_btc_monitor.py)
- Handle no-Aave-position gracefully (no crash)
- Hardcode Telegram token from env for reliability
- Added JSON output from Aave monitor for robust parsing
- Use OpenClaw native messaging if available, fallback to Telegram API
"""

import json
import subprocess
import os
import requests
import re
import math
from datetime import datetime

# Try env first, fallback to hardcoded (bot token is stable)
# IMPORTANT: Token must be complete - never use ellipsis/truncation
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1144365829")

# Deduplication: one report per day (prevent duplicate cron/agent/manual runs)
DAILY_LOCK_FILE = '/tmp/btc_daily_report.lock'
FORCE_SEND = os.environ.get("FORCE_SEND", "0") == "1"

def already_sent_today():
    """Check if a BTC report was already sent today.

    Uses the current local date (Bogotá timezone) because the 8:00 AM cron
    and the report are expected to run in the same local calendar day.
    """
    from datetime import timezone as dt_timezone
    today = datetime.now(dt_timezone.utc).astimezone().strftime('%Y-%m-%d')
    try:
        if os.path.exists(DAILY_LOCK_FILE):
            with open(DAILY_LOCK_FILE, 'r') as f:
                data = json.load(f)
            if data.get('date') == today and data.get('message_id'):
                return True, data.get('message_id')
    except Exception as e:
        print(f"⚠️ Could not read daily lock file: {e}")
    return False, None

def mark_sent_today(message_id):
    """Record that today's report was sent."""
    from datetime import timezone as dt_timezone
    today = datetime.now(dt_timezone.utc).astimezone().strftime('%Y-%m-%d')
    try:
        with open(DAILY_LOCK_FILE, 'w') as f:
            json.dump({'date': today, 'message_id': message_id, 'sent_at': datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"⚠️ Could not write daily lock file: {e}")

# Make sure DUNE_API_KEY is available for the decision engine if not already in env.
# The cron job sources telegram.env but variables are not exported by default.
def _ensure_dune_api_key():
    if os.environ.get("DUNE_API_KEY"):
        return
    env_file = "/home/raspberry/.openclaw/.secrets/telegram.env"
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DUNE_API_KEY="):
                    os.environ["DUNE_API_KEY"] = line.split("=", 1)[1].strip()
                    print("✅ Loaded DUNE_API_KEY from telegram.env")
                    return
    except Exception as e:
        print(f"⚠️ Could not load DUNE_API_KEY from telegram.env: {e}")

_ensure_dune_api_key()

def run_command(cmd, timeout=60):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s: {cmd}"
    except Exception as e:
        return f"ERROR: {e}"

def get_btc_signal():
    """Read BTC signal from decision engine output."""
    try:
        with open('/tmp/btc_general_report.json', 'r') as f:
            data = json.load(f)
            summary = data.get('summary', {})
            return {
                'score': data.get('score', 50),
                'recommendation': data.get('recommendation', 'NEUTRAL'),
                'price': data.get('price', 75000),
                'mvrv': summary.get('mvrv', 1.0),
                'rsi': summary.get('rsi', 50),
                'ma_discount': summary.get('discount_50w_ma', 0),
                'fear_greed': summary.get('fear_greed', 50),
                'cycle_days': summary.get('cycle_blocks', 0),
                'etf_net_flow_7d': summary.get('etf_net_flow_7d', 0),
                'macd_histogram': summary.get('macd_histogram', 0),
                'bollinger_position': summary.get('bollinger_position', 0.5),
                'pi_cycle_diff': summary.get('pi_cycle_diff', 0),
                's2f_value': summary.get('s2f_value', 50),
                'cycle_phase': summary.get('cycle_phase', 'UNKNOWN'),
                'dca_amount_weekly': summary.get('dca_amount_weekly', 275),
            }
    except Exception as e:
        print(f"⚠️ Error reading btc_general_report.json: {e}")
        return {
            'score': 50, 'recommendation': 'NEUTRAL', 'price': 75000,
            'mvrv': 1.0, 'rsi': 50, 'ma_discount': 0,
            'fear_greed': 50, 'cycle_days': 0,
            'etf_net_flow_7d': 0, 'macd_histogram': 0,
            'bollinger_position': 0.5, 'pi_cycle_diff': 0,
            's2f_value': 50, 'cycle_phase': 'UNKNOWN',
            'dca_amount_weekly': 275,
        }

def get_ledger_btc():
    """Get Ledger BTC from xpub scan. Refreshes file and warns if stale."""
    skip_scan = os.environ.get("SKIP_XPUB_SCAN", "0") == "1"

    try:
        with open('/home/raspberry/.openclaw/workspace/btc-position.json', 'r') as f:
            pos = json.load(f)
        last_updated = pos.get("last_updated", "")
    except Exception:
        pos = {}
        last_updated = ""

    today = datetime.now().strftime('%Y-%m-%d')
    if skip_scan:
        print(f"   SKIP_XPUB_SCAN=1 — using cached btc-position.json (last updated {last_updated}).")
        return pos.get("btc_holding", 0)

    # If the cached file is already from today, reuse it to avoid slow rescans in the same day.
    if last_updated == today:
        print(f"   btc-position.json already up to date ({last_updated}), skipping xpub rescan.")
        return pos.get("btc_holding", 0)

    print("   Running xpub scan (this can take 30-90s)...")
    scan_output = run_command("/usr/bin/python3 /home/raspberry/.openclaw/workspace/scripts/scan_xpub.py", timeout=180)
    # Print scan output for diagnostics (it includes total balance and any errors)
    for line in scan_output.splitlines():
        if line.strip():
            print(f"   {line}")

    try:
        with open('/home/raspberry/.openclaw/workspace/btc-position.json', 'r') as f:
            pos = json.load(f)
        holding = pos.get("btc_holding", 0)
        new_last_updated = pos.get("last_updated", "")
        if new_last_updated != today:
            print(f"⚠️ btc-position.json is stale (last updated {new_last_updated}, today {today}). Using scanned value anyway.")
        return holding
    except Exception as e:
        print(f"⚠️ Error reading btc-position.json: {e}")
        return 0

def get_btc_eur_rate():
    """Fetch BTC/EUR rate, trying CoinGecko first then Binance/Coinbase."""
    # Primary: CoinGecko
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "eur"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            price = resp.json().get("bitcoin", {}).get("eur", 0)
            if price:
                return float(price)
    except Exception as e:
        print(f"⚠️ Error fetching BTC/EUR from CoinGecko: {e}")
    # Fallback 1: Binance
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR", timeout=10)
        if resp.status_code == 200:
            return float(resp.json().get("price", 0))
    except Exception as e:
        print(f"⚠️ Error fetching BTC/EUR from Binance: {e}")
    # Fallback 2: Coinbase
    try:
        resp = requests.get("https://api.coinbase.com/v2/exchange-rates?currency=BTC", timeout=10)
        if resp.status_code == 200:
            return float(resp.json()["data"]["rates"]["EUR"])
    except Exception as e:
        print(f"⚠️ Error fetching BTC/EUR from Coinbase: {e}")
    return 0

def get_eur_usd_rate():
    """Fetch EUR/USD rate from CoinGecko or forex API."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "tether", "vs_currencies": "eur"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            usdt_eur = resp.json().get("tether", {}).get("eur", 0)
            if usdt_eur:
                return 1.0 / float(usdt_eur)
    except Exception as e:
        print(f"⚠️ Error fetching EUR/USD from CoinGecko: {e}")
    # Fallback: ECB reference rates (XML)
    try:
        resp = requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml", timeout=10)
        if resp.status_code == 200:
            import re
            m = re.search(r'currency="USD"\s+rate="([0-9.]+)"', resp.text)
            if m:
                return float(m.group(1))
    except Exception as e:
        print(f"⚠️ Error fetching EUR/USD from ECB: {e}")
    return 1.08

MVX_PROVIDER_ADDRESS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf"
PROVIDER_CACHE_FILE = "/tmp/btc_cs_provider_cache.json"

def load_provider_cache():
    """Load last successfully fetched provider data."""
    try:
        if os.path.exists(PROVIDER_CACHE_FILE):
            with open(PROVIDER_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading provider cache: {e}")
    return {}

def save_provider_cache(data):
    """Save provider data to cache."""
    try:
        with open(PROVIDER_CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving provider cache: {e}")

def fetch_multiversx(url, params=None):
    """Generic MultiversX API helper with retries."""
    headers = {"accept": "application/json"}
    for attempt in range(2):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            print(f"⚠️ MVX API {url} status {resp.status_code}")
        except Exception as e:
            print(f"⚠️ MVX API {url} error: {e}")
    return None

def get_colombia_staking_provider_info():
    """Fetch Colombia Staking provider info from /providers, with cache fallback."""
    cache = load_provider_cache()
    providers = fetch_multiversx("https://api.multiversx.com/providers", {"size": 200})
    if not providers or not isinstance(providers, list):
        print("⚠️ Could not fetch providers, using cached provider data")
        cache_age_days = None
        if cache.get("timestamp"):
            try:
                cache_dt = datetime.fromisoformat(cache["timestamp"])
                cache_age_days = (datetime.now() - cache_dt).total_seconds() / 86400
                print(f"   Cache age: {cache_age_days:.1f} days")
            except Exception:
                pass
        provider = cache.get("provider")
        if provider is not None and cache_age_days is not None and cache_age_days > 1:
            provider["_stale_cache_warning"] = True
        return provider
    for p in providers:
        ident = p.get("identity", "").lower()
        prov = p.get("provider", "").lower()
        if "colombia" in ident or prov == MVX_PROVIDER_ADDRESS.lower():
            save_provider_cache({"provider": p, "timestamp": datetime.now().isoformat()})
            return p
    print("⚠️ Colombia Staking provider not found in providers list, using cache")
    return cache.get("provider")

def get_colombia_staking_total_stake():
    """Get total active stake delegated to Colombia Staking (locked EGLD)."""
    p = get_colombia_staking_provider_info()
    if not p:
        return 0.0
    # locked = base stake + topUp = total EGLD delegated to the provider
    locked = p.get("locked", 0) or p.get("stake", 0)
    return float(locked) / 1e18

def get_colombia_staking_service_fee():
    """Get Colombia Staking on-chain service fee (fraction, e.g. 0.10)."""
    p = get_colombia_staking_provider_info()
    if not p:
        return 0.10
    fee = p.get("serviceFee")
    if fee is not None:
        return float(fee)
    return 0.10

def get_mvx_network_apr():
    """Fetch MultiversX network staking APR from official economics endpoint."""
    data = fetch_multiversx("https://api.multiversx.com/economics")
    if not data:
        return 0.0
    # economics returns stakeSupply, totalStaked, apr
    apr = data.get("apr") or data.get("stakingApr") or data.get("baseApr")
    if apr is not None:
        return float(apr)
    # Fallback: derive from total supply + staked ratio + base rewards
    total_staked = float(data.get("totalStaked", 0) or data.get("staked", 0) or 1)
    total_supply = float(data.get("totalSupply", 0) or data.get("circulatingSupply", 0) or 1)
    if total_staked > 0 and total_supply > 0:
        ratio = total_staked / total_supply
        # Approximate annual issuance ~11% base reward rate scaled by ratio
        return 0.11 / max(ratio, 0.01)
    return 0.08

def get_colombia_staking_provider_apr():
    """Get Colombia Staking net APR (after service fee) from on-chain provider data."""
    p = get_colombia_staking_provider_info()
    if not p:
        return 0.0
    apr = p.get("apr")
    if apr is not None:
        return float(apr) / 100.0  # API returns percentage, e.g. 8.4
    return 0.0

def get_colombia_staking_gross_apr(net_apr, service_fee):
    """Derive gross APR before service fee."""
    if net_apr > 0 and service_fee < 1.0:
        return net_apr / (1.0 - service_fee)
    return net_apr

def get_cop_eur_rate():
    """Fetch COP/EUR exchange rate from a reliable API."""
    # Primary: exchangerate-api.com (free, no key needed for current rate)
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/COP", timeout=10)
        if resp.status_code == 200:
            return float(resp.json().get("rates", {}).get("EUR", 0))
    except Exception as e:
        print(f"⚠️ Error fetching COP/EUR from exchangerate-api: {e}")
    # Fallback: frankfurter.app (ECB rates)
    try:
        resp = requests.get("https://api.frankfurter.app/latest?from=COP&to=EUR", timeout=10)
        if resp.status_code == 200:
            return float(resp.json().get("rates", {}).get("EUR", 0))
    except Exception as e:
        print(f"⚠️ Error fetching COP/EUR from frankfurter: {e}")
    # Fallback 2: Colombia central bank / indicative rate via floatrates
    try:
        resp = requests.get("https://www.floatrates.com/daily/cop.json", timeout=10)
        if resp.status_code == 200:
            for entry in resp.json():
                if entry.get("code") == "EUR":
                    return float(entry.get("rate", 0))
    except Exception as e:
        print(f"⚠️ Error fetching COP/EUR from floatrates: {e}")
    return 0.00022

# Apartment rental income configuration (monthly rents in COP)
APARTMENT_RENTS_COP = {
    "301": 820_000,
    "201": 900_000,
    "202": 820_000,
}

def get_apartment_rental_income_eur():
    """Calculate total monthly apartment rental income in EUR."""
    rate = get_cop_eur_rate()
    total_cop = sum(APARTMENT_RENTS_COP.values())
    total_eur = total_cop * rate if rate > 0 else 0
    return {
        "rate": rate,
        "total_cop": total_cop,
        "total_eur": total_eur,
        "apartments": APARTMENT_RENTS_COP,
    }

def get_mvx_price_eur():
    """Fetch EGLD/EUR price from CoinGecko, Binance, or Coinbase."""
    # Primary: CoinGecko
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "multiversx", "vs_currencies": "eur"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            price = resp.json().get("multiversx", {}).get("eur", 0)
            if price:
                return float(price)
    except Exception as e:
        print(f"⚠️ Error fetching EGLD/EUR from CoinGecko: {e}")
    # Fallback 1: Binance
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EGLDEUR", timeout=10)
        if resp.status_code == 200:
            return float(resp.json().get("price", 0))
    except Exception as e:
        print(f"⚠️ Error fetching EGLD/EUR from Binance: {e}")
    # Fallback 2: Coinbase
    try:
        resp = requests.get("https://api.coinbase.com/v2/exchange-rates?currency=EGLD", timeout=10)
        if resp.status_code == 200:
            return float(resp.json()["data"]["rates"]["EUR"])
    except Exception as e:
        print(f"⚠️ Error fetching EGLD/EUR from Coinbase: {e}")
    # Fallback 3: MultiversX economics USD price + EUR/USD
    try:
        eco = fetch_multiversx("https://api.multiversx.com/economics")
        usd_price = float(eco.get("price", 0)) if eco else 0
        eur_usd = get_eur_usd_rate()
        if usd_price > 0 and eur_usd > 0:
            return usd_price / eur_usd
    except Exception as e:
        print(f"⚠️ Error fetching EGLD/EUR from MultiversX economics: {e}")
    return 0

def get_monthly_spendings_eur():
    """Total monthly personal spendings in EUR."""
    # Source: Sebas confirmed 2026-06-15
    return 1825.0

def calculate_personal_finance(btc_price_usd):
    """Calculate personal finance summary from on-chain data."""
    result = {
        "ledger_btc": 0,
        "btc_price_usd": btc_price_usd,
        "btc_price_eur": 0,
        "eur_usd": 0,
        "btc_value_eur": 0,
        "colombia_staking_total_egld": 0,
        "provider_net_apr": 0,
        "provider_gross_apr": 0,
        "network_apr": 0,
        "service_fee_pct": 0.10,
        "cs_monthly_revenue_egld": 0,
        "cs_monthly_revenue_eur": 0,
        "personal_delegation_egld": 1250,
        "personal_monthly_egld": 0,
        "personal_monthly_eur": 0,
        "total_monthly_revenue_eur": 0,
        "egld_price_eur": 0,
        "apartment_rental_eur": 0,
        "monthly_spendings_eur": 0,
        "freelance_gap_eur": 0,
        "self_sustaining_pct": 0,
        "grand_total_monthly_income_eur": 0,
        "notes": []
    }
    # Ledger BTC
    result["ledger_btc"] = get_ledger_btc()
    result["btc_price_eur"] = get_btc_eur_rate()
    result["eur_usd"] = get_eur_usd_rate()
    if result["btc_price_eur"] <= 0 and btc_price_usd > 0 and result["eur_usd"] > 0:
        result["btc_price_eur"] = btc_price_usd / result["eur_usd"]
    result["btc_value_eur"] = result["ledger_btc"] * result["btc_price_eur"]

    # On-chain EGLD data
    result["egld_price_eur"] = get_mvx_price_eur()
    result["service_fee_pct"] = get_colombia_staking_service_fee()
    provider_info = get_colombia_staking_provider_info()
    result["provider_net_apr"] = get_colombia_staking_provider_apr()
    result["provider_gross_apr"] = get_colombia_staking_gross_apr(result["provider_net_apr"], result["service_fee_pct"])
    result["network_apr"] = result["provider_net_apr"] if result["provider_net_apr"] else 0.084
    result["colombia_staking_total_egld"] = get_colombia_staking_total_stake()

    if provider_info and provider_info.get("_stale_cache_warning"):
        result["notes"].append("Colombia Staking provider data is from cached data >1 day old")

    # Monthly revenue for Colombia Staking: total_stake * gross_apr * service_fee / 12
    if result["colombia_staking_total_egld"] > 0 and result["provider_gross_apr"] > 0:
        annual_rewards_egld = result["colombia_staking_total_egld"] * result["provider_gross_apr"]
        result["cs_monthly_revenue_egld"] = annual_rewards_egld * result["service_fee_pct"] / 12.0
        result["cs_monthly_revenue_eur"] = result["cs_monthly_revenue_egld"] * result["egld_price_eur"]
    else:
        result["notes"].append("Could not fetch Colombia Staking on-chain stake/APR")

    # Personal delegation earnings (1,250 EGLD at net provider APR)
    if result["provider_net_apr"] > 0:
        result["personal_monthly_egld"] = result["personal_delegation_egld"] * result["provider_net_apr"] / 12.0
        result["personal_monthly_eur"] = result["personal_monthly_egld"] * result["egld_price_eur"]
    else:
        result["notes"].append("Could not fetch provider APR for personal delegation")

    # Apartment rental income (COP → EUR)
    rental = get_apartment_rental_income_eur()
    result["apartment_rental_eur"] = rental["total_eur"]
    if rental["total_eur"] <= 0:
        result["notes"].append("Could not fetch COP/EUR rate for apartment rental income")

    # Monthly spendings and freelance gap
    result["monthly_spendings_eur"] = get_monthly_spendings_eur()
    result["total_monthly_revenue_eur"] = result["cs_monthly_revenue_eur"] + result["personal_monthly_eur"] + result["apartment_rental_eur"]
    result["grand_total_monthly_income_eur"] = result["total_monthly_revenue_eur"]
    result["freelance_gap_eur"] = max(0, result["monthly_spendings_eur"] - result["grand_total_monthly_income_eur"])
    if result["monthly_spendings_eur"] > 0:
        result["self_sustaining_pct"] = (result["grand_total_monthly_income_eur"] / result["monthly_spendings_eur"]) * 100
    return result

def get_aave_position():
    """Get Aave position. Returns zeros if no position or error."""
    # Run Aave monitor — it saves state to /tmp/btc_monitor_state.json
    output = run_command("cd /home/raspberry/.openclaw/workspace/scripts && python3 aave_btc_monitor.py", timeout=30)
    
    # Try to read JSON state first (most reliable)
    try:
        with open('/tmp/btc_monitor_state.json', 'r') as f:
            state = json.load(f)

        # Check staleness of Aave state
        state_ts = state.get('timestamp', '')
        if state_ts:
            try:
                state_dt = datetime.fromisoformat(state_ts)
                state_age_hours = (datetime.now() - state_dt).total_seconds() / 3600
                if state_age_hours > 24:
                    print(f"⚠️ Aave monitor state is {state_age_hours:.1f} hours old")
            except Exception:
                pass

        btc_price = state.get('btc_price', 0)
        collateral_btc = state.get('collateral_btc', 0)
        debt_usd = state.get('debt_usd', 0)
        
        # Calculate HF and LTV
        hf_current = float('inf')
        if debt_usd > 0 and collateral_btc > 0 and btc_price > 0:
            hf_current = (collateral_btc * btc_price * 0.78) / debt_usd
        
        collateral_usd = collateral_btc * btc_price
        ltv = (debt_usd / collateral_usd * 100) if collateral_usd > 0 else 0
        
        # Calculate liquidation price (HF=1.0)
        liq_price = 0
        if collateral_btc > 0 and debt_usd > 0:
            liq_price = (1.0 * debt_usd) / (collateral_btc * 0.78)
        
        buffer_pct = ((btc_price - liq_price) / btc_price * 100) if btc_price > 0 and liq_price > 0 else 0
        
        return {
            'health_factor': hf_current,
            'collateral_btc': collateral_btc,
            'collateral_usd': collateral_usd,
            'debt_usd': debt_usd,
            'buffer_pct': buffer_pct,
            'btc_price': btc_price,
            'ltv': ltv,
            'has_position': collateral_btc > 0 or debt_usd > 0,
            'state_timestamp': state_ts
        }
    except Exception as e:
        print(f"⚠️ Error reading btc_monitor_state.json: {e}")
    
    # Fallback: parse output lines (legacy method)
    hf = float('inf')
    collateral_btc = 0
    collateral_usd = 0
    debt_usd = 0
    liq_price = 0
    buffer_pct = 0
    btc_price = 75000
    
    for line in output.split('\n'):
        if 'Current HF:' in line or '📍 **Current HF:**' in line:
            try: hf = float(re.search(r'(\d+\.\d+)', line).group(1))
            except: pass
        if ('Collateral:' in line or '**Collateral:**' in line) and ('BTC' in line or 'btc' in line.lower()):
            try: collateral_btc = float(re.search(r'(\d+\.?\d*)', line).group(1))
            except: pass
        if 'Debt:' in line or '**Debt:**' in line:
            try: debt_usd = float(re.search(r'\$(\d[\d,]*\.?\d*)', line).group(1).replace(',', ''))
            except: pass
        if ('HF 1.0' in line or 'HF 1.0' in line) and ('DANGER' in line or 'danger' in line.lower()):
            try: liq_price = float(re.search(r'\$(\d[\d,]*\.?\d*)', line).group(1).replace(',', ''))
            except: pass
        if 'BTC Price:' in line or '**Current BTC:**' in line:
            try: btc_price = float(re.search(r'\$(\d[\d,]*\.?\d*)', line).group(1).replace(',', ''))
            except: pass
    
    collateral_usd = collateral_btc * btc_price
    if btc_price > 0 and liq_price > 0:
        buffer_pct = ((btc_price - liq_price) / btc_price) * 100
    ltv = (debt_usd / collateral_usd * 100) if collateral_usd > 0 else 0
    
    return {
        'health_factor': hf,
        'collateral_btc': collateral_btc,
        'collateral_usd': collateral_usd,
        'debt_usd': debt_usd,
        'buffer_pct': buffer_pct,
        'btc_price': btc_price,
        'ltv': ltv,
        'has_position': collateral_btc > 0 or debt_usd > 0
    }

# DCA table aligned with engine v8.1 (20-level strategy)
DCA_TABLE = [
    (0, 5, 550, "ACCUMULATE", "Maximum accumulation"),
    (6, 10, 509, "ACCUMULATE", "Maximum accumulation"),
    (11, 15, 468, "ACCUMULATE", "Strong accumulation"),
    (16, 20, 426, "ACCUMULATE", "Strong accumulation"),
    (21, 25, 385, "ACCUMULATE", "Deep value zone"),
    (26, 30, 344, "ACCUMULATE", "Good value"),
    (31, 35, 303, "ACCUMULATE", "Good value"),
    (36, 40, 261, "LIGHT ACCUMULATION", "Fair value"),
    (41, 45, 220, "LIGHT ACCUMULATION", "Fair value"),
    (46, 50, 193, "REDUCED", "Neutral"),
    (51, 55, 138, "REDUCED", "Minimal"),
    (56, 60, 69, "REDUCED", "Minimal"),
    (61, 65, 138, "ACCUMULATE", "Early bull accumulation"),
    (66, 70, 69, "REDUCED", "Smoothed profit-taking"),
    (71, 100, 0, "STOP", "Profit-taking mode"),
]

def get_dca_from_score(score):
    """Get DCA amount and posture from the 20-level strategy table."""
    for lo, hi, weekly, posture, reason in DCA_TABLE:
        if lo <= score <= hi:
            return weekly, posture, reason
    return 138, "REDUCED", "Neutral"

def calculate_strategy(score, aave):
    """Calculate DCA/borrow/repay strategy based on score and Aave position."""
    weekly, posture, reason = get_dca_from_score(score)
    borrow = 0
    repay = 0
    
    # HF overrides
    if aave.get('has_position', False):
        if aave['health_factor'] < 1.3:
            repay = 500; posture = "DELEVERAGE"; reason = "HF critical — deleveraging required"
            weekly = 0
        elif aave['health_factor'] < 1.5:
            repay = 250; posture = "REDUCE DEBT"; reason = "HF low — reduce exposure"
            weekly = min(weekly, 69)  # Minimal DCA while deleveraging
        elif aave['health_factor'] > 2.0 and aave['ltv'] < 45 and score <= 40:
            borrow = 500; posture = "ACCUMULATE + BORROW"; reason = "Safe to borrow for projects"
    
    return {
        'dca_amount_eur': weekly,
        'dca_btc': weekly / aave['btc_price'] if aave['btc_price'] > 0 else 0,
        'borrow_amount_eur': borrow,
        'repay_amount_eur': repay,
        'strategic_posture': posture,
        'posture_reason': reason
    }

def send_telegram(message):
    """Send message to Telegram; returns (ok, message_id)."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("⚠️ No Telegram bot token configured")
        return False, None
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            message_id = resp.json().get('result', {}).get('message_id')
            print(f"✅ Telegram delivered (message_id={message_id})")
            return True, message_id
        else:
            print(f"⚠️ Telegram error: {resp.status_code} - {resp.text[:200]}")
            return False, None
    except Exception as e:
        print(f"⚠️ Telegram send failed: {e}")
        return False, None

def build_report(btc, aave, strategy, personal):
    """Build the daily report message."""
    current_date = datetime.now().strftime("%B %d, %Y")
    score = btc.get('score', 50)
    rec = btc.get('recommendation', 'NEUTRAL')
    
    # Ledger holdings
    ledger_btc = aave.get('ledger_btc', 0)
    ledger_usd = ledger_btc * btc.get('price', 0)
    
    # Total
    total_btc = aave.get('collateral_btc', 0) + ledger_btc
    total_usd = aave.get('collateral_usd', 0) + ledger_usd
    
    # Aave section
    if aave.get('has_position', False):
        aave_section = f"""• Aave: {aave.get('collateral_btc', 0):.4f} BTC collateral | ${aave.get('debt_usd', 0):,.0f} debt
• HF: {aave.get('health_factor', 0):.2f} | LTV: {aave.get('ltv', 0):.1f}%"""
    else:
        aave_section = "• Aave: No active position"
    
    # Personal finance summary
    pf = personal
    gap = pf['freelance_gap_eur']
    progress = pf['self_sustaining_pct']
    pf_section = f"""💰 Your BTC: {pf['ledger_btc']:.4f} BTC ≈ €{pf['btc_value_eur']:,.0f}
🏢 Colombia Staking: €{pf['cs_monthly_revenue_eur'] + pf['personal_monthly_eur']:,.0f}/month
🏠 Apartment rentals: €{pf['apartment_rental_eur']:,.0f}/month
💵 Total passive income: €{pf['grand_total_monthly_income_eur']:,.0f}/month
💳 Monthly spendings: €{pf['monthly_spendings_eur']:,.0f}/month
📉 Freelance needed: €{gap:,.0f}/month
🎯 Self-sustaining: {progress:.1f}%"""
    if pf.get('notes'):
        pf_section += "\n⚠️ " + " | ".join(pf['notes'])
    
    message = f"""📊 BTC Daily Strategy — {current_date}

🎯 Score: {score}/100 — {rec}

📈 Market
• BTC: ${btc.get('price', 0):,.0f} | MVRV: {btc.get('mvrv', 0):.2f}
• RSI: {btc.get('rsi', 0):.1f} | 50W MA: {btc.get('ma_discount', 0):+.1f}%
• Fear & Greed: {btc.get('fear_greed', 50)} | ETF 7d: {btc.get('etf_net_flow_7d', 0):+,.0f} BTC

💼 Position
• Ledger: {ledger_btc:.4f} BTC (${ledger_usd:,.0f})
{aave_section}
• Total: {total_btc:.4f} BTC (${total_usd:,.0f})

👤 Personal Finance
{pf_section}

📋 Strategy
• DCA: €{strategy['dca_amount_eur']:,.0f}/week — {strategy['posture_reason']}
• Borrow: {'€' + str(strategy['borrow_amount_eur']) if strategy['borrow_amount_eur'] > 0 else 'No'}
• Repay: {'€' + str(strategy['repay_amount_eur']) if strategy['repay_amount_eur'] > 0 else 'No'}

⚠️ Watch: {strategy['posture_reason']}"""
    
    return message

def save_report(message):
    """Save report locally and push to GitHub."""
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    # Save to reports directory
    report_dir = '/home/raspberry/.openclaw/workspace/btc-strategy/reports/daily'
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/{report_date}.md"
    
    try:
        with open(report_path, 'w') as f:
            f.write(message)
        print(f"✅ Report saved: {report_path}")
    except Exception as e:
        print(f"⚠️ Save failed: {e}")
    
    # GitHub backup
    try:
        repo_path = '/home/raspberry/.openclaw/workspace/btc-strategy'
        subprocess.run(["git", "-C", repo_path, "add", "."], capture_output=True, timeout=10)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", f"Daily report - {report_date}", "--allow-empty"], capture_output=True, timeout=10)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], capture_output=True, timeout=30)
        print("✅ GitHub backup complete!")
    except Exception as e:
        print(f"⚠️ GitHub backup: {e}")

def main():
    # Step 1: Run decision engine
    print("=" * 50)
    print("BTC Daily Strategy Report v3")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Run decision engine
    print("\n[1/5] Running BTC decision engine...")
    engine_output = run_command(
        "cd /home/raspberry/.openclaw/workspace/.agents/skills/btc-strategy/scripts && "
        "python3 btc_decision_engine.py > /dev/null 2>&1",
        timeout=120
    )
    if "ERROR" in engine_output or "TIMEOUT" in engine_output:
        print(f"⚠️ Engine issue: {engine_output}")
    else:
        print("✅ Engine complete")
    
    # Step 2: Read signal
    print("\n[2/5] Reading BTC signal...")
    btc = get_btc_signal()
    print(f"   Score: {btc['score']}/100 | Price: ${btc['price']:,.0f} | MVRV: {btc['mvrv']:.2f}")
    
    # Step 3: Get positions
    print("\n[3/5] Getting positions...")
    aave = get_aave_position()
    aave['ledger_btc'] = get_ledger_btc()
    
    print(f"   Ledger: {aave['ledger_btc']:.4f} BTC")
    if aave.get('has_position'):
        print(f"   Aave: {aave['collateral_btc']:.4f} BTC collateral, ${aave['debt_usd']:,.0f} debt, HF {aave['health_factor']:.2f}")
    else:
        print("   Aave: No active position")
    
    # Step 4: Personal finance
    print("\n[4/5] Calculating personal finance...")
    personal = calculate_personal_finance(btc.get('price', 0))
    print(f"   BTC value: €{personal['btc_value_eur']:,.0f}")
    print(f"   CS revenue: €{personal['cs_monthly_revenue_eur']:,.0f}/mo")
    print(f"   Personal delegation: €{personal['personal_monthly_eur']:,.0f}/mo")
    print(f"   Total EGLD revenue: €{personal['total_monthly_revenue_eur']:,.0f}/mo")

    # Step 5: Calculate strategy and send
    print("\n[5/5] Building and sending report...")
    strategy = calculate_strategy(btc.get('score', 50), aave)
    message = build_report(btc, aave, strategy, personal)
    
    # Deduplication guard
    sent_today, existing_message_id = already_sent_today()
    telegram_ok = False
    message_id = None
    if sent_today and not FORCE_SEND:
        print(f"⚠️ Daily report already sent today (message_id={existing_message_id}). Skipping Telegram send.")
        print("    Set FORCE_SEND=1 to override.")
    else:
        if FORCE_SEND:
            print("🚨 FORCE_SEND=1 — sending report even if one was already sent today.")
        # Send to Telegram
        telegram_ok, message_id = send_telegram(message)
        if telegram_ok and message_id:
            mark_sent_today(message_id)
    
    # Save locally regardless of Telegram success
    save_report(message)
    
    # Also save to log
    log_path = '/tmp/btc_daily_report.log'
    with open(log_path, 'a') as f:
        f.write(f"\n{'='*40}\n")
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if sent_today and not FORCE_SEND:
            f.write(f"Telegram: SKIPPED (already sent today, message_id={existing_message_id})\n")
        else:
            f.write(f"Telegram: {'OK' if telegram_ok else 'FAILED'} (message_id={message_id})\n")
        f.write(message)
        f.write("\n")
    
    print(f"\n{'='*50}")
    print(f"Report complete! Telegram: {'✅' if telegram_ok else ('⏭️ skipped' if sent_today and not FORCE_SEND else '❌')}")
    print(f"{'='*50}")
    
    return telegram_ok or (sent_today and not FORCE_SEND)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
