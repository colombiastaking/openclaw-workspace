#!/usr/bin/env python3
"""
BTC Accumulation Decision Engine v7.5 - COMPOSITE + DUNE REALIZED PRICE
Professional-grade multi-indicator scoring system for LONG-TERM HOLDERS

*** KEY CHANGE v7.5 ***
RESTORED Dune Analytics integration for real on-chain realized price.
MVRV now uses actual blockchain data instead of 365-day MA proxy.

v7.4: REPLACED price-based profit-taking with INDICATOR-BASED
v7.5: RESTORED Dune realized price (lost in v7.0 rewrite)

MAX SELL: 25% of BTC position (keeps 75%+ compounding)
Profit-taking tiers based on SCORE + SYNERGIES (not price):

| Tier | Score > | Bull Synergies | MVRV | RSI | F&G | Sell % | Cumulative |
|------|---------|----------------|------|-----|-----|--------|------------|
| 1    | 55      | 1+             | 1.5  | 60  | 70  | 5%     | 5%         |
| 2    | 65      | 2+             | 2.0  | 70  | 80  | 10%    | 15%        |
| 3    | 75      | 3+ (all)       | 2.5  | 75  | 85  | 10%    | 25% max    |
| 4    | 85      | MAX            | 3.0  | 80  | 90  | STOP   | 25% max    |

Trigger: ANY condition met at tier level (not ALL)

Goals:
1. Clear Aave debt during bull runs
2. Build stablecoin reserves for future DCA
3. Never sell more than 25% - keep 75%+ compounding

Usage: python3 btc_decision_engine.py
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import math

# ======================
# CONFIGURATION
# ======================

COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/v2"

# ======================
# DUNE ANALYTICS CONFIGURATION
# ======================
# Dune Analytics - Free on-chain data platform
# Get your API key from: https://dune.com/settings/api
# Public query for Bitcoin Realized Price: https://dune.com/queries/1936502
DUNE_API_KEY = os.environ.get("DUNE_API_KEY", "")
DUNE_API_URL = "https://api.dune.com/api/v1"
DUNE_REALIZED_PRICE_QUERY_ID = "1936502"  # Public query: "Bitcoin : Realized Price"

# ======================
# DUNE DATA FETCHER
# ======================

def get_dune_realized_price():
    """
    Fetch real on-chain realized price from Dune Analytics.
    Falls back to 365-day MA proxy if Dune API is not available.
    
    Realized price is the weighted average cost basis of all Bitcoin,
    calculated from blockchain UTXO data.
    """
    if not DUNE_API_KEY:
        return None, "no_api_key"
    
    try:
        url = f"{DUNE_API_URL}/query/{DUNE_REALIZED_PRICE_QUERY_ID}/results"
        headers = {
            "x-dune-api-key": DUNE_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            result_data = data.get("result", {})
            rows = result_data.get("rows", [])
            
            if rows:
                latest = rows[0]
                if isinstance(latest, dict):
                    realized_price = latest.get("REALIZED_PRICE", latest.get("realized_price", latest.get("price", None)))
                    if realized_price:
                        timestamp = latest.get("time", latest.get("date", None))
                        return {
                            "realized_price": float(realized_price),
                            "timestamp": timestamp,
                            "source": "dune_onchain"
                        }, "success"
            
            return None, "no_data"
        elif response.status_code == 401 or response.status_code == 403:
            return None, "auth_error"
        else:
            return None, f"http_{response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "timeout"
    except Exception as e:
        return None, f"error_{str(e)}"
    
    return None, "unknown_error"

def get_realized_price_with_fallback():
    """
    Get realized price with fallback:
    1. Try Dune Analytics (real on-chain data)
    2. Fall back to 365-day MA proxy
    """
    # Try Dune first
    dune_result, status = get_dune_realized_price()
    
    if status == "success" and dune_result:
        return dune_result, "dune"
    
    # Fall back to 365-day MA proxy
    hist_data = get_historical_btc_prices(365)
    if hist_data:
        ma_365 = hist_data.get("ma_365", 0)
        if ma_365 > 0:
            return {
                "realized_price": ma_365,
                "timestamp": datetime.now().isoformat(),
                "source": "ma_365_proxy"
            }, "ma_365"
    
    # Last resort: use current price (MVRV = 1.0)
    btc_data = get_btc_price_data()
    if btc_data:
        return {
            "realized_price": btc_data["current_price"],
            "timestamp": datetime.now().isoformat(),
            "source": "current_price_fallback"
        }, "current_price"
    
    return None, "failed"

# ======================
# DATA FETCHERS
# ======================

def get_btc_price_data():
    """Get current BTC price and key metrics from CoinGecko"""
    try:
        url = f"{COINGECKO_API}/coins/bitcoin"
        params = {
            "localization": False,
            "tickers": False,
            "community_data": False,
            "developer_data": False,
            "sparkline": False
        }
        headers = {"accept": "application/json"}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", {})
            
            return {
                "current_price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "price_change_percentage_24h": market_data.get("price_change_percentage_24h", 0),
                "ath": market_data.get("ath", {}).get("usd", 0),
                "atl": market_data.get("atl", {}).get("usd", 0),
                "market_cap_rank": data.get("market_cap_rank", 0),
                "circulating_supply": market_data.get("circulating_supply", 0),
                "total_supply": market_data.get("total_supply", 0),
                "max_supply": market_data.get("max_supply", 0)
            }
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
    
    return None

def get_historical_btc_prices(days=365):
    """Get historical BTC prices for MA and indicator calculations"""
    try:
        url = f"{COINGECKO_API}/coins/bitcoin/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily"
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            prices = data.get("prices", [])
            
            if not prices:
                return None
            
            # Extract prices
            price_list = [p[1] for p in prices]
            
            # Calculate Moving Averages
            ma_50 = sum(price_list[-50:]) / 50 if len(price_list) >= 50 else price_list[-1]
            ma_200 = sum(price_list[-200:]) / 200 if len(price_list) >= 200 else price_list[-1]
            ma_365 = sum(price_list) / len(price_list) if len(price_list) >= 365 else price_list[-1]
            
            # 50 Week MA (350 days approximation)
            ma_50_week = sum(price_list[-350:]) / 350 if len(price_list) >= 350 else price_list[-1]
            
            # 111 Day MA (used in Pi Cycle indicator)
            ma_111 = sum(price_list[-111:]) / 111 if len(price_list) >= 111 else price_list[-1]
            
            # 350 Day MA (used in Pi Cycle indicator - requires 350+ days of data)
            ma_350 = sum(price_list[-350:]) / 350 if len(price_list) >= 350 else sum(price_list) / len(price_list)
            
            # Calculate RSI (14-day)
            gains = []
            losses = []
            for i in range(1, min(15, len(price_list))):
                change = price_list[-i] - price_list[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs)) if avg_loss > 0 else 100
            
            # Calculate MACD (12, 26, 9)
            ema_12 = calculate_ema(price_list, 12)
            ema_26 = calculate_ema(price_list, 26)
            macd = ema_12 - ema_26
            signal = calculate_ema([macd] * 9, 9)
            macd_histogram = macd - signal
            
            # Bollinger Bands (20-day standard)
            ma_20 = sum(price_list[-20:]) / 20 if len(price_list) >= 20 else price_list[-1]
            std_dev = math.sqrt(sum((p - ma_20) ** 2 for p in price_list[-20:]) / 20) if len(price_list) >= 20 else 0
            bb_upper = ma_20 + (2 * std_dev)
            bb_lower = ma_20 - (2 * std_dev)
            
            # %B (Bollinger Position): Where is price relative to bands?
            # 0 = at lower band, 1 = at upper band, >1 = above upper, <0 = below lower
            if bb_upper > bb_lower:
                bb_position = (price_list[-1] - bb_lower) / (bb_upper - bb_lower)
            else:
                bb_position = 0.5
            
            # Bandwidth (for squeeze detection)
            bb_bandwidth = ((bb_upper - bb_lower) / ma_20 * 100) if ma_20 > 0 else 0
            
            # Historical bandwidth comparison (percentile)
            bandwidths = []
            for i in range(max(0, len(price_list)-100), len(price_list)-19):
                if i >= 0 and i+20 <= len(price_list):
                    ma = sum(price_list[i:i+20]) / 20
                    sd = math.sqrt(sum((p - ma) ** 2 for p in price_list[i:i+20]) / 20)
                    bw = ((ma + 2*sd) - (ma - 2*sd)) / ma * 100 if ma > 0 else 0
                    bandwidths.append(bw)
            
            bb_bandwidth_percentile = 50  # Default neutral
            if bandwidths:
                sorted_bw = sorted(bandwidths)
                bb_bandwidth_percentile = (sorted_bw.index(bb_bandwidth) / len(sorted_bw) * 100) if bb_bandwidth in sorted_bw else 50
            
            # Volume analysis (24h volume relative to 30-day avg)
            volumes = [p[1] for p in data.get("volumes", [])[-30:]] if "volumes" in data else [1]
            avg_volume = sum(volumes) / len(volumes) if volumes else 1
            volume_ratio = data.get("total_volumes", [[0, 1]])[-1][1] / avg_volume if avg_volume > 0 else 1
            
            return {
                "current_price": price_list[-1],
                "ma_50": ma_50,
                "ma_200": ma_200,
                "ma_365": ma_365,
                "ma_50_week": ma_50_week,
                "ma_111": ma_111,
                "ma_350": ma_350,
                "rsi": rsi,
                "macd": macd,
                "macd_histogram": macd_histogram,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
                "bb_position": bb_position,
                "volume_ratio": volume_ratio,
                "prices": price_list
            }
    except Exception as e:
        print(f"Error fetching historical prices: {e}")
    
    return None

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def get_weekly_btc_prices():
    """
    Get WEEKLY BTC price data for long-term momentum indicators.
    All momentum indicators (RSI, MACD, Bollinger Bands) on WEEKLY timeframes
    to eliminate "daily trader noise" for long-term holders.
    """
    try:
        # Fetch 365 days of daily data
        url = f"{COINGECKO_API}/coins/bitcoin/market_chart"
        params = {
            "vs_currency": "usd",
            "days": 365,
            "interval": "daily"
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            daily_prices = data.get("prices", [])
            
            if not daily_prices:
                return None
            
            # Aggregate daily data into weekly candles
            # Each week starts on Sunday (day 0)
            weekly_candles = {}
            for timestamp, price in daily_prices:
                import datetime
                dt = datetime.datetime.fromtimestamp(timestamp / 1000)
                # Get the Sunday of this week
                week_start = dt - datetime.timedelta(days=dt.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weekly_candles:
                    weekly_candles[week_key] = {'open': price, 'high': price, 'low': price, 'close': price}
                else:
                    weekly_candles[week_key]['high'] = max(weekly_candles[week_key]['high'], price)
                    weekly_candles[week_key]['low'] = min(weekly_candles[week_key]['low'], price)
                    weekly_candles[week_key]['close'] = price
            
            # Convert to sorted list of closing prices
            sorted_weeks = sorted(weekly_candles.keys())
            weekly_closes = [weekly_candles[w]['close'] for w in sorted_weeks]
            weekly_highs = [weekly_candles[w]['high'] for w in sorted_weeks]
            weekly_lows = [weekly_candles[w]['low'] for w in sorted_weeks]
            
            if len(weekly_closes) < 20:
                return None
            
            # Calculate weekly RSI (20-week - more smoothing, fewer false signals)
            gains = []
            losses = []
            for i in range(1, min(21, len(weekly_closes))):
                change = weekly_closes[-i] - weekly_closes[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / 20 if gains else 0
            avg_loss = sum(losses) / 20 if losses else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            weekly_rsi = 100 - (100 / (1 + rs)) if avg_loss > 0 else 100
            
            # Calculate weekly MACD (12, 26, 9 on weekly data)
            ema_12_weekly = calculate_ema(weekly_closes[-26:], 12) if len(weekly_closes) >= 26 else weekly_closes[-1]
            ema_26_weekly = calculate_ema(weekly_closes[-52:], 26) if len(weekly_closes) >= 26 else weekly_closes[-1]
            weekly_macd = ema_12_weekly - ema_26_weekly
            
            # Signal line (9-week EMA of MACD)
            macd_values = []
            for i in range(26, len(weekly_closes)):
                e12 = calculate_ema(weekly_closes[max(0,i-12):i+1], 12)
                e26 = calculate_ema(weekly_closes[max(0,i-26):i+1], 26)
                macd_values.append(e12 - e26)
            weekly_signal = calculate_ema(macd_values[-9:], 9) if len(macd_values) >= 9 else macd_values[-1]
            weekly_macd_histogram = weekly_macd - weekly_signal
            
            # Weekly Bollinger Bands (20-week)
            ma_20_weekly = sum(weekly_closes[-20:]) / 20
            std_dev = math.sqrt(sum((p - ma_20_weekly) ** 2 for p in weekly_closes[-20:]) / 20)
            bb_upper_weekly = ma_20_weekly + (2 * std_dev)
            bb_lower_weekly = ma_20_weekly - (2 * std_dev)
            
            if bb_upper_weekly > bb_lower_weekly:
                bb_position_weekly = (weekly_closes[-1] - bb_lower_weekly) / (bb_upper_weekly - bb_lower_weekly)
            else:
                bb_position_weekly = 0.5
            
            # Bandwidth (weekly)
            bb_bandwidth_weekly = ((bb_upper_weekly - bb_lower_weekly) / ma_20_weekly * 100) if ma_20_weekly > 0 else 0
            
            return {
                "weekly_rsi": weekly_rsi,
                "weekly_macd": weekly_macd,
                "weekly_macd_histogram": weekly_macd_histogram,
                "bb_upper": bb_upper_weekly,
                "bb_lower": bb_lower_weekly,
                "bb_position": bb_position_weekly,
                "ma_20_weekly": ma_20_weekly,
                "bb_bandwidth": bb_bandwidth_weekly,
                "weekly_closes": weekly_closes,
                "note": "All momentum indicators on WEEKLY timeframes for long-term signals"
            }
    except Exception as e:
        print(f"Error fetching weekly BTC data: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def get_fear_and_greed():
    """Get Fear & Greed Index from Alternative.me"""
    try:
        response = requests.get(FEAR_GREED_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            fg_data = data.get("data", {})
            return {
                "value": list(fg_data.values())[0].get("value", 50) if fg_data else 50,
                "value_classification": list(fg_data.values())[0].get("value_classification", "Neutral") if fg_data else "Neutral"
            }
    except Exception as e:
        print(f"Error fetching Fear & Greed: {e}")
    return {"value": 50, "value_classification": "Neutral"}

def load_etf_cache():
    """Load ETF flow cache from disk"""
    try:
        cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etf_flow_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to load ETF cache: {e}")
    return {"flows": [], "holdings": {}}


def save_etf_cache(cache):
    """Save ETF flow cache to disk"""
    try:
        cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etf_flow_cache.json")
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Failed to save ETF cache: {e}")


def fetch_etf_flows():
    """Fetch current ETF flows from btcetfdata.com"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        url = 'https://btcetfdata.com/'
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            import re
            tr_pattern = r'<tr[^>]*>(.*?)</tr>'
            trs = re.findall(tr_pattern, response.text, re.DOTALL)
            
            etfs = []
            for tr in trs:
                td_pattern = r'<td[^>]*>(.*?)</td>'
                tds = re.findall(td_pattern, tr, re.DOTALL)
                if tds:
                    clean_tds = [re.sub('<[^>]+>', '', td).strip() for td in tds]
                    if len(clean_tds) >= 5 and clean_tds[0] not in ['Ticker', 'Description', 'Holdings']:
                        try:
                            holdings = float(clean_tds[2].replace(',', ''))
                            change = float(clean_tds[3].replace(',', ''))
                            etfs.append({
                                'ticker': clean_tds[0],
                                'holdings_btc': holdings,
                                'change_btc': change,
                            })
                        except:
                            pass
            
            if etfs:
                return {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_holdings_btc": sum(e['holdings_btc'] for e in etfs),
                    "net_flow_24h": sum(e['change_btc'] for e in etfs),
                    "inflow_count": len([e for e in etfs if e['change_btc'] > 0]),
                    "outflow_count": len([e for e in etfs if e['change_btc'] < 0]),
                    "etfs": etfs
                }
    except Exception as e:
        print(f"btcetfdata.com fetch failed: {e}")
    return None


def update_etf_cache(cache, today_flow):
    """Add today's flow to cache, prune old entries beyond 35 days"""
    if today_flow is None:
        return cache
    
    if 'flows' not in cache:
        cache['flows'] = []
    
    today_str = today_flow['date']
    existing_idx = None
    for i, f in enumerate(cache['flows']):
        if f.get('date') == today_str:
            existing_idx = i
            break
    
    if existing_idx is not None:
        cache['flows'][existing_idx] = today_flow
    else:
        cache['flows'].append(today_flow)
    
    cache['holdings'] = {
        "total_holdings_btc": today_flow['total_holdings_btc'],
        "date": today_flow['date']
    }
    
    # Prune flows older than 35 days
    cutoff = datetime.now() - timedelta(days=35)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    cache['flows'] = [f for f in cache['flows'] if f.get('date', '') >= cutoff_str]
    cache['flows'].sort(key=lambda x: x.get('date', ''))
    
    return cache


def calculate_etf_trends(cache):
    """Calculate trend indicators from cached flow data"""
    flows = cache.get('flows', [])
    
    if len(flows) < 2:
        return {"trend_7d": 0, "trend_30d": 0, "ma_7d": 0, "ma_30d": 0, "trend_direction": "unknown", "days_of_data": len(flows)}
    
    recent_7d = flows[-7:] if len(flows) >= 7 else flows
    recent_30d = flows[-30:] if len(flows) >= 30 else flows
    
    ma_7d = sum(f['net_flow_24h'] for f in recent_7d) / len(recent_7d)
    ma_30d = sum(f['net_flow_24h'] for f in recent_30d) / len(recent_30d) if len(recent_30d) > 0 else 0
    
    if len(flows) >= 6:
        recent_3_avg = sum(f['net_flow_24h'] for f in flows[-3:]) / 3
        prev_3_avg = sum(f['net_flow_24h'] for f in flows[-6:-3]) / 3
        trend_delta = recent_3_avg - prev_3_avg
    else:
        trend_delta = 0
    
    if ma_7d > 500:
        trend_direction = "strong_inflow"
    elif ma_7d > 100:
        trend_direction = "inflow"
    elif ma_7d < -500:
        trend_direction = "strong_outflow"
    elif ma_7d < -100:
        trend_direction = "outflow"
    elif abs(trend_delta) < 100:
        trend_direction = "stable"
    elif trend_delta > 0:
        trend_direction = "improving"
    else:
        trend_direction = "worsening"
    
    return {"trend_7d": ma_7d, "trend_30d": ma_30d, "ma_7d": ma_7d, "ma_30d": ma_30d, "trend_direction": trend_direction, "trend_delta": trend_delta, "days_of_data": len(flows)}


def build_etf_response_from_cache(cache):
    """Build ETF sentiment response from cached data"""
    flows = cache.get('flows', [])
    holdings = cache.get('holdings', {})
    
    if not flows:
        return None
    
    trends = calculate_etf_trends(cache)
    latest = flows[-1] if flows else {}
    
    if trends['days_of_data'] < 2:
        effective_trend = latest.get('net_flow_24h', 0)
        trend_note = f"First day - using 24h: {effective_trend:+.0f} BTC"
    else:
        effective_trend = trends['ma_7d']
        trend_note = f"7d avg: {trends['ma_7d']:+.0f} BTC/day"
    
    inflow_days_7d = len([f for f in flows[-7:] if f.get('net_flow_24h', 0) > 0])
    outflow_days_7d = len([f for f in flows[-7:] if f.get('net_flow_24h', 0) < 0])
    
    return {
        "total_holdings_btc": holdings.get('total_holdings_btc', 0),
        "holdings_date": holdings.get('date', ''),
        "net_flow_24h": latest.get('net_flow_24h', 0),
        "flow_date": latest.get('date', ''),
        "trend_7d": effective_trend,
        "trend_30d": trends['ma_30d'],
        "trend_direction": trends['trend_direction'],
        "inflow_days_7d": inflow_days_7d,
        "outflow_days_7d": outflow_days_7d,
        "days_of_data": trends['days_of_data'],
        "data_source": "btcetfdata.com (cached)",
        "data_note": trend_note,
        "avg_daily_flow": effective_trend  # For scoring compatibility
    }


def get_etf_sentiment():
    """
    Get Bitcoin ETF sentiment using multi-source system with caching
    
    SOURCES (in priority order):
    1. btcetfdata.com with cache (7-day and 30-day trend tracking)
    2. SoSoValue API
    3. BTC Dominance proxy (CoinGecko)
    
    CACHE: Stores daily flows in etf_flow_cache.json with 35-day retention
    """
    # Primary: Try btcetfdata.com with cache system
    cache = load_etf_cache()
    today_flow = fetch_etf_flows()
    
    if today_flow is None:
        # No new data, use cached data
        if cache and 'flows' in cache and len(cache['flows']) > 0:
            return build_etf_response_from_cache(cache)
        # Fall through to SoSoValue
    else:
        # Update cache with today's flow
        cache = update_etf_cache(cache, today_flow)
        save_etf_cache(cache)
        return build_etf_response_from_cache(cache)
    
    # Secondary: Try SoSoValue API
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        url = "https://sosovalue.com/api/bitcoin-etf"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            total_aum = data.get("total_aum", 0)
            total_volume = data.get("total_volume_24h", 0)
            etf_list = data.get("etf_list", [])
            
            net_flow_7d = 0
            inflow_days = 0
            outflow_days = 0
            
            for etf in etf_list:
                flow_7d = etf.get("flow_7d", 0)
                net_flow_7d += flow_7d
                if flow_7d > 0:
                    inflow_days += 1
                elif flow_7d < 0:
                    outflow_days += 1
            
            avg_daily_flow = net_flow_7d / 7 if etf_list else 0
            
            return {
                "total_aum": total_aum,
                "total_volume_24h": total_volume,
                "net_flow_7d": net_flow_7d,
                "avg_daily_flow": avg_daily_flow,
                "inflow_days": inflow_days,
                "outflow_days": outflow_days,
                "data_source": "SoSoValue API",
                "data_note": "Live ETF flow data"
            }
    except Exception as e:
        print(f"SoSoValue API unavailable: {e}")
    
    # Tertiary: Use BTC Dominance as ETF sentiment proxy
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            btc_dominance = data.get("data", {}).get("market_cap_percentage", {}).get("btc", 50)
            
            return {
                "total_aum": 0,
                "total_volume_24h": 0,
                "net_flow_7d": 0,
                "avg_daily_flow": 0,
                "inflow_days": 0,
                "outflow_days": 0,
                "data_source": "CoinGecko (BTC Dominance Proxy)",
                "data_note": f"BTC Dominance: {btc_dominance}%. Rising = ETF inflows, Falling = outflows",
                "btc_dominance": btc_dominance
            }
    except Exception as e:
        print(f"Fallback ETF proxy also failed: {e}")
    
    return None

# ======================
# BTC BLOCK HEIGHT FOR CYCLE POSITION
# ======================

def get_blocks_since_halving():
    """
    Get BTC blocks since last halving using actual block height.
    
    Halving #4: April 19, 2024 at block 840,000
    Each halving is 210,000 blocks.
    
    Returns blocks since halving, or falls back to calendar estimate.
    """
    HALVING_4_BLOCK = 840_000
    
    try:
        # Try to get current block height from blockchain.info
        url = "https://blockchain.info/q/getblockcount"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            current_block = int(response.text.strip())
            blocks_since = current_block - HALVING_4_BLOCK
            if blocks_since > 0:
                return blocks_since
    except Exception as e:
        print(f"Block height fetch failed: {e}")
    
    # Fallback: Estimate from calendar date (approximate)
    # Average 144 blocks per day (6 blocks × 24 hours)
    halving_date = datetime(2024, 4, 19)
    days_since = (datetime.now() - halving_date).days
    estimated_blocks = days_since * 144
    print(f"Using calendar estimate: ~{estimated_blocks:,} blocks (fetch failed)")
    return estimated_blocks


def get_market_status():
    """Get all market data and compute key metrics"""
    try:
        btc_data = get_btc_price_data()
        hist_data = get_historical_btc_prices(365)
        weekly_data = get_weekly_btc_prices()  # Weekly candles for long-term momentum
        
        if not btc_data or not hist_data:
            return None
        
        current_price = btc_data["current_price"]
        ath = btc_data["ath"]
        
        # Use WEEKLY RSI instead of daily for long-term signals
        rsi = weekly_data["weekly_rsi"] if weekly_data else hist_data["rsi"]
        
        # Get realized price from Dune (real on-chain data) with fallback to 365-day MA
        realized_data, realized_source = get_realized_price_with_fallback()
        
        if realized_data:
            realized_price = realized_data["realized_price"]
            realized_price_source = realized_data["source"]
        else:
            realized_price = hist_data["ma_365"] if hist_data else current_price
            realized_price_source = "ma_365_proxy"
        
        # Estimated MVRV ratio
        estimated_mvrv = current_price / realized_price if realized_price > 0 else 1.0
        
        # BTC Block Height for cycle position (more accurate than calendar date)
        # Halving #4 occurred at block 840,000 on April 19, 2024
        blocks_since_halving = get_blocks_since_halving()
        
        # Pi Cycle indicator: 111 MA * 2 vs 350 MA crossover
        pi_cycle_value = (hist_data.get("ma_111", current_price) * 2) if hist_data else current_price * 2
        pi_cycle_350 = hist_data.get("ma_350", current_price) if hist_data else current_price
        pi_cycle_diff = ((pi_cycle_value - pi_cycle_350) / pi_cycle_350 * 100) if pi_cycle_350 > 0 else 0
        
        # Stock-to-Flow calculation
        blocks_per_day = 6 * 24  # Post-2024 halving
        btc_per_block = 3.125
        annual_production = blocks_per_day * btc_per_block * 365
        circulating_supply = btc_data.get("circulating_supply", 19500000)
        s2f_ratio = circulating_supply / annual_production if annual_production > 0 else 100
        s2f_value = s2f_ratio
        
        # Use WEEKLY Bollinger Bands for long-term signals
        if weekly_data:
            bb_position = weekly_data["bb_position"]
            bb_upper = weekly_data["bb_upper"]
            bb_lower = weekly_data["bb_lower"]
            bb_bandwidth = weekly_data.get("bb_bandwidth", 0)
            macd = weekly_data["weekly_macd"]
            macd_histogram = weekly_data["weekly_macd_histogram"]
        else:
            bb_position = hist_data.get("bb_position", 0.5)
            bb_upper = hist_data.get("bb_upper", current_price)
            bb_lower = hist_data.get("bb_lower", current_price)
            bb_bandwidth = 0
            macd = hist_data.get("macd", 0)
            macd_histogram = hist_data.get("macd_histogram", 0)
        
        return {
            "current_price": current_price,
            "estimated_mvrv": estimated_mvrv,
            "realized_price": realized_price,
            "realized_price_source": realized_price_source,
            "ath": ath,
            "ath_percentage": (current_price / ath * 100) if ath > 0 else 0,
            "blocks_since_halving": blocks_since_halving,
            "ma_50": hist_data.get("ma_50", current_price),
            "ma_200": hist_data.get("ma_200", current_price),
            "ma_50_week": hist_data.get("ma_50_week", current_price),
            "ma_111": hist_data.get("ma_111", current_price),
            "ma_350": hist_data.get("ma_350", current_price),
            "rsi": rsi,  # WEEKLY RSI
            "macd": macd,  # WEEKLY MACD
            "macd_histogram": macd_histogram,  # WEEKLY MACD HISTOGRAM
            "bb_position": bb_position,  # WEEKLY BOLLINGER
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_bandwidth": bb_bandwidth,
            "volume_ratio": hist_data.get("volume_ratio", 1),
            "pi_cycle_value": pi_cycle_value,
            "pi_cycle_350": pi_cycle_350,
            "pi_cycle_diff": pi_cycle_diff,
            "s2f_ratio": s2f_ratio,
            "s2f_value": s2f_value,
            "etf_data": get_etf_sentiment(),
            "weekly_data": weekly_data is not None,
            "note": "Momentum indicators (RSI, MACD, Bollinger) now on WEEKLY timeframes"
        }
    except Exception as e:
        print(f"Error getting market status: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def get_geopolitical_risk():
    """
    Assess current geopolitical risk level using market-based proxies.
    
    Uses:
    - VIX (^VIX): CBOE Volatility Index - spikes during crises
    - DXY (DX-Y.NYB): US Dollar Index - strengthens during risk-off
    
    Returns dynamic assessment instead of static hardcoded values.
    Higher VIX/DXY = higher crisis risk = potentially better for BTC safe haven.
    """
    try:
        vix_value = None
        dxy_value = None
        
        # Fetch VIX
        try:
            vix_url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX"
            params = {"interval": "1d", "range": "5d"}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(vix_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                if closes:
                    vix_value = closes[-1]  # Latest close
        except Exception as e:
            print(f"VIX fetch error: {e}")
        
        # Fetch DXY (US Dollar Index)
        try:
            dxy_url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"
            params = {"interval": "1d", "range": "5d"}
            resp = requests.get(dxy_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                if closes:
                    dxy_value = closes[-1]  # Latest close
        except Exception as e:
            print(f"DXY fetch error: {e}")
        
        # Determine risk level from VIX
        if vix_value is None:
            vix_risk = 0.65  # Default moderate if fetch fails
            vix_signal = "Unknown (fetch failed)"
        elif vix_value < 15:
            vix_risk = 0.80  # Low risk, normal market
            vix_signal = f"Normal ({vix_value:.1f})"
        elif vix_value < 20:
            vix_risk = 0.70  # Mild elevated
            vix_signal = f"Mild ({vix_value:.1f})"
        elif vix_value < 25:
            vix_risk = 0.55  # Elevated concern
            vix_signal = f"Elevated ({vix_value:.1f})"
        elif vix_value < 30:
            vix_risk = 0.40  # High crisis
            vix_signal = f"High ({vix_value:.1f})"
        else:
            vix_risk = 0.25  # Extreme crisis
            vix_signal = f"Extreme ({vix_value:.1f})"
        
        # Determine risk level from DXY (USD strength = risk-off)
        if dxy_value is None:
            dxy_signal = "Unknown (fetch failed)"
        elif dxy_value < 100:
            dxy_signal = f"Risk-on ({dxy_value:.1f})"
        elif dxy_value < 104:
            dxy_signal = f"Neutral ({dxy_value:.1f})"
        elif dxy_value < 108:
            dxy_signal = f"Risk-off ({dxy_value:.1f})"
        else:
            dxy_signal = f"Strong risk-off ({dxy_value:.1f})"
        
        # Combine signals - weight toward VIX as primary crisis indicator
        if vix_risk < 0.50 and dxy_value is not None and dxy_value > 104:
            combined_risk = min(vix_risk, 0.35)  # Both agree on crisis
        else:
            combined_risk = vix_risk  # VIX is primary
        
        # Interpretation for BTC
        if vix_value is not None and vix_value > 30:
            interpretation = f"EXTREME CRISIS ({vix_value:.0f}) - Safe haven narrative strongest"
        elif vix_value is not None and vix_value > 25:
            interpretation = f"HIGH CRISIS ({vix_value:.0f}) - BTC safe haven bid"
        elif vix_value is not None and vix_value > 20:
            interpretation = f"ELEVATED TENSIONS ({vix_value:.0f}) - BTC mixed/hold"
        elif vix_value is not None and vix_value > 15:
            interpretation = f"MODERATE ({vix_value:.0f}) - BTC neutral"
        else:
            interpretation = "LOW GLOBAL RISK - Risk-on environment"
        
        return {
            "vix": vix_value,
            "dxy": dxy_value,
            "vix_signal": vix_signal,
            "dxy_signal": dxy_signal,
            "combined_risk": combined_risk,
            "interpretation": interpretation,
            "dynamic": True
        }
    except Exception as e:
        print(f"Error assessing geopolitical risk: {e}")
    
    return {"vix": None, "dxy": None, "combined_risk": 0.65, "interpretation": "Stable", "dynamic": False}

def get_geopolitical_interpretation(overall_risk, war_risk):
    if war_risk < 0.60:
        return "HIGH CRISIS - Safe haven narrative strengthens"
    elif war_risk < 0.75:
        return "ELEVATED TENSIONS - BTC benefits as hedge"
    elif overall_risk < 0.70:
        return "MODERATE RISK - BTC neutral/mixed"
    else:
        return "LOW GLOBAL RISK - Risk-on environment"

# ======================
# v7.2 SCORING ENGINE WITH COMPOSITES AND SYNERGY
# ======================

def score_mvrv(mvrv):
    """Score MVRV indicator (v7.9a: 10 steps reflecting historical cycle patterns)"""
    # Historical context:
    #   <0.75 = generational bottoms (2015, 2018, 2022 capitulation)
    #   0.75-0.90 = deep bear accumulation
    #   0.90-1.00 = fair value / neutral accumulation
    #   1.00-1.30 = post-halving bull early phase
    #   1.30-1.60 = mid-bull, getting warm
    #   1.60-2.50 = late bull / euphoria building
    #   >2.50 = historical bubble territory (2017, 2021 tops)
    if mvrv < 0.75:
        return 5, "🟢 GENERATIONAL BOTTOM"
    elif mvrv < 0.85:
        return 12, "🟢 DEEP BEAR ACCUMULATION"
    elif mvrv < 0.95:
        return 20, "🟢 ACCUMULATION ZONE"
    elif mvrv < 1.00:
        return 28, "🟢 SLIGHTLY BELOW FAIR"
    elif mvrv < 1.10:
        return 35, "🟡 FAIR VALUE"
    elif mvrv < 1.30:
        return 42, "🟡 ELEVATED / EARLY BULL"
    elif mvrv < 1.60:
        return 52, "🟠 MID-BULL WARMING"
    elif mvrv < 2.00:
        return 62, "🟠 LATE BULL"
    elif mvrv < 2.50:
        return 75, "🔴 VERY EXPENSIVE"
    else:
        return 90, "🔴 HISTORICAL BUBBLE"

def score_rsi(rsi):
    """Score Weekly RSI (v7.9a: 10 steps, smoothed transitions)"""
    # RSI behavior on weekly timeframe:
    #   <25 = rare capitulation (generational buys)
    #   25-35 = oversold accumulation
    #   35-42 = early buy zone
    #   42-48 = neutral-bullish transition
    #   48-52 = true neutral (50 = no momentum bias)
    #   52-58 = mild bullish momentum
    #   58-65 = overbought warning
    #   65-72 = strongly overbought
    #   72-80 = extreme (distribution zone)
    #   >80 = parabolic / unsustainable
    if rsi < 25:
        return 5, "🟢 EXTREME OVERSOLD"
    elif rsi < 35:
        return 15, "🟢 OVERSOLD"
    elif rsi < 42:
        return 22, "🟢 ACCUMULATE"
    elif rsi < 48:
        return 28, "🟢 BUY ZONE — EARLY"
    elif rsi < 52:
        return 35, "🟡 NEUTRAL-BULLISH"
    elif rsi < 58:
        return 45, "🟡 NEUTRAL"
    elif rsi < 65:
        return 55, "🟠 SLIGHTLY OVERBOUGHT"
    elif rsi < 72:
        return 68, "🟠 OVERBOUGHT"
    elif rsi < 80:
        return 78, "🔴 STRONGLY OVERBOUGHT"
    else:
        return 90, "🔴 PARABOLIC / UNSUSTAINABLE"

def score_50w_ma_discount(discount):
    """Score 50 Week MA discount (v7.9a: 10 steps with crash tier)"""
    # Historical context:
    #   < -50% = generational crashes (Mar 2020, Dec 2018, 2014)
    #   -35% to -50% = severe corrections (rare, strong accumulation)
    #   -25% to -35% = deep bear (2022 bottom, 2015)
    #   -18% to -25% = significant correction (current -21% falls here)
    #   -10% to -18% = moderate dip (normal pullbacks)
    #   -5% to -10% = slight dip (healthy consolidation)
    #   0% to -5% = near MA (trend continuation)
    #   0% to +10% = above MA but not extreme
    #   +10% to +25% = extended rally
    #   >+25% = parabolic / unsustainable
    if discount < -50:
        return 5, "🟢 GENERATIONAL CRASH"
    elif discount < -35:
        return 12, "🟢 SEVERE CORRECTION"
    elif discount < -25:
        return 20, "🟢 DEEP BEAR DISCOUNT"
    elif discount < -18:
        return 28, "🟢 SIGNIFICANT DISCOUNT"  # Current -21.3% lands here
    elif discount < -10:
        return 35, "🟢 MODERATE DISCOUNT"
    elif discount < -5:
        return 42, "🟢 SLIGHT DISCOUNT"
    elif discount < 0:
        return 48, "🟡 JUST BELOW MA"
    elif discount < 10:
        return 55, "🟡 NEAR MA"
    elif discount < 25:
        return 68, "🟠 PREMIUM"
    else:
        return 85, "🔴 EXTREME PREMIUM"

def score_cycle_position(blocks):
    """
    Score cycle position using BLOCK HEIGHT (v7.9a: historically corrected).
    
    KEY INSIGHT: Historical peaks happen at ~70-80K blocks (~1.3-1.5 years),
    NOT at 104K+. The old model misaligned peaks by ~6 months.
    
    Historical cycle data:
    - 2016 halving → Peak Dec 2017 (~78K blocks post-halving)
    - 2020 halving → Peak Nov 2021 (~78K blocks post-halving)
    - 2024 halving → Peak Mar 2025 (~70K blocks post-halving)
    
    Therefore:
    - 0-52K: Post-halving hype (elevated risk)
    - 52K-78K: Early pump (peak building)
    - 78K-104K: HISTORICAL PEAK ZONE (most dangerous for new buys)
    - 104K+: Post-peak → BEAR ACCUMULATION (best for DCA)
    """
    if blocks < 26000:  # ~0-6 months
        return 55, "🔴 POST-HALVING HYPE"
    elif blocks < 52000:  # ~6-12 months
        return 62, "🔴 EARLY PUMP"
    elif blocks < 78000:  # ~12-18 months (HISTORICAL PEAK ZONE)
        return 72, "🔴 PEAK ZONE"
    elif blocks < 104000:  # ~18-24 months (POST-PEAK CORRECTION)
        return 42, "🟡 POST-PEAK"
    elif blocks < 130000:  # ~24-30 months
        return 28, "🟢 EARLY BEAR ACCUMULATION"
    elif blocks < 156000:  # ~30-36 months
        return 18, "🟢 MID BEAR"
    elif blocks < 208000:  # ~36-48 months
        return 10, "🟢 MAXIMUM ACCUMULATION"
    elif blocks < 234000:  # ~48-54 months
        return 20, "🟢 PRE-HALVING RECOVERY"
    else:  # ~54+ months (approaching next halving)
        return 35, "🟡 APPROACHING HALVING"

def score_fear_greed(fg):
    """Score Fear & Greed Index (lower = better for accumulation)"""
    if fg < 20:
        return 5, "🟢 EXTREME FEAR"
    elif fg < 30:
        return 18, "🟢 FEAR"
    elif fg < 45:
        return 30, "🟢 CAUTIOUS"
    elif fg < 55:
        return 45, "🟡 NEUTRAL"
    elif fg < 70:
        return 65, "🟠 GREED"
    elif fg < 85:
        return 82, "🔴 EXTREME GREED"
    else:
        return 95, "🔴 BUBBLE"

def score_etf_sentiment(etf_data):
    """Score ETF sentiment (v7.9a: calibrated for modern ETF era)"""
    if not etf_data:
        return 50, "🟡 UNAVAILABLE"
    
    avg_daily_flow = etf_data.get("avg_daily_flow", 0)
    
    # v7.9a: More granular thresholds for modern ETF market dynamics
    # Pre-2024: ETFs were new → 500 BTC/day was massive
    # Post-2024: ETFs mature → need higher thresholds
    if avg_daily_flow > 5000:
        return 5, "🟢 MASSIVE INFLOWS"
    elif avg_daily_flow > 3000:
        return 12, "🟢 STRONG INFLOWS"
    elif avg_daily_flow > 1500:
        return 20, "🟢 SOLID INFLOWS"
    elif avg_daily_flow > 500:
        return 30, "🟢 POSITIVE"
    elif avg_daily_flow > -200:
        return 42, "🟡 SLIGHTLY POSITIVE"
    elif avg_daily_flow > -1000:
        return 52, "🟡 NEUTRAL/MILD OUTFLOWS"
    elif avg_daily_flow > -2500:
        return 65, "🟠 MODERATE OUTFLOWS"
    elif avg_daily_flow > -5000:
        return 78, "🔴 HEAVY OUTFLOWS"
    elif avg_daily_flow > -10000:
        return 88, "🔴 EXTREME OUTFLOWS"
    else:
        return 95, "🔴 CAPITULATION"

def score_macd(macd_histogram):
    """Score Weekly MACD histogram (lower = better for accumulation)"""
    # v7.9a: More granular thresholds — reduces false extreme signals
    if macd_histogram < -10000:
        return 5, "🟢 EXTREME BEAR MOMENTUM"
    elif macd_histogram < -5000:
        return 12, "🟢 STRONG BEAR MOMENTUM"
    elif macd_histogram < -2000:
        return 22, "🟢 BEAR WEAKENING"
    elif macd_histogram < -500:
        return 32, "🟢 EARLY ACCUMULATION"
    elif macd_histogram < 0:
        return 42, "🟡 SLIGHTLY BEARISH"
    elif macd_histogram < 1000:
        return 50, "🟡 NEUTRAL"
    elif macd_histogram < 2500:
        return 58, "🟠 MILD BULL MOMENTUM"
    elif macd_histogram < 5000:
        return 68, "🟠 STRONG BULL"
    elif macd_histogram < 10000:
        return 78, "🔴 EXTREME BULL"
    else:
        return 90, "🔴 PARABOLIC MOMENTUM"

def score_bollinger(bb_position):
    """Score Weekly Bollinger Bands position (lower = better for accumulation)"""
    if bb_position < 0:
        return 5, "🟢 BELOW LOWER BAND"
    elif bb_position < 0.2:
        return 12, "🟢 NEAR LOWER BAND"
    elif bb_position < 0.4:
        return 22, "🟢 LOWER HALF"
    elif bb_position < 0.6:
        return 45, "🟡 MIDDLE"
    elif bb_position < 0.8:
        return 60, "🟠 UPPER HALF"
    elif bb_position < 1.0:
        return 75, "🔴 NEAR UPPER BAND"
    else:
        return 88, "🔴 ABOVE UPPER BAND"

def score_geopolitical(geo_risk):
    """Score geopolitical risk using VIX + DXY market data"""
    # Use combined_risk from VIX/DXY (dynamic) instead of static values
    combined = geo_risk.get("combined_risk", 0.65)
    vix = geo_risk.get("vix")
    interpretation = geo_risk.get("interpretation", "Unknown")
    
    if combined < 0.4:
        return 15, f"🟢 EXTREME CRISIS (VIX: {vix})"
    elif combined < 0.5:
        return 25, f"🟢 HIGH CRISIS (VIX: {vix})"
    elif combined < 0.6:
        return 35, f"🟡 ELEVATED (VIX: {vix})"
    elif combined < 0.7:
        return 45, f"🟡 MODERATE (VIX: {vix})"
    else:
        return 40, f"🟢 LOW RISK (VIX: {vix})"

def score_pi_cycle(pi_diff):
    """Score Pi Cycle indicator (v7.9a: fixed bullish interpretation)"""
    # Pi Cycle diff positive = price BELOW 350d MA x2 = BULLISH (not topped)
    # Pi Cycle diff negative = price ABOVE 350d MA x2 = BEARISH (potential top)
    if pi_diff < -50:
        return 8, "🟢 DEEP BOTTOM PATTERN"
    elif pi_diff < -20:
        return 15, "🟢 BOTTOM FORMING"
    elif pi_diff < -5:
        return 25, "🟢 EARLY RECOVERY"
    elif pi_diff < 10:
        return 35, "🟡 NORMAL BULL"
    elif pi_diff < 30:
        return 42, "🟡 BULL CONTINUATION"
    elif pi_diff < 50:
        return 50, "🟠 EXTENDED BUT NOT TOPPED"
    elif pi_diff < 75:
        return 60, "🟠 LATE CYCLE"
    elif pi_diff < 100:
        return 75, "🔴 WARNING ZONE"
    else:
        return 92, "🔴 BUBBLE TERRITORY"

def score_stock_to_flow(s2f):
    """Score Stock-to-Flow (higher = more bullish due to scarcity)"""
    if s2f > 110:
        return 10, "🟢 EXTREME SCARCITY"
    elif s2f > 90:
        return 18, "🟢 VERY SCARCE"
    elif s2f > 70:
        return 30, "🟢 HIGH SCARCITY"
    elif s2f > 50:
        return 50, "🟡 MODERATE"
    else:
        return 70, "🟠 LESS SCARCE"

def calculate_v7_score(market_data, fear_greed_data, geo_risk):
    """
    Calculate v7.2 score using COMPOSITE INDICATORS with SYNERGY BONUSES
    
    COMPOSITE STRUCTURE:
    - VALUATION (30%): MVRV (60%) + RSI (40%)
    - TREND (20%): 50W MA (50%) + Cycle Position (50%)
    - SENTIMENT (17%): Fear & Greed (60%) + ETF (40%)
    - MOMENTUM (12%): MACD (50%) + Bollinger (50%)
    - GEOPOLITICAL (5%): standalone
    - PI CYCLE (3%): standalone
    - STOCK-TO-FLOW (3%): standalone
    - AI DISCRETION (10%): qualitative override buffer
    
    SYNERGY BONUSES (negative = LOWER score = MORE bullish):
    - VALUATION: MVRV < 1.0 AND RSI < 40 → -12
    - TREND: 50W MA < -20% AND Cycle 600-900 → -10
    - SENTIMENT: F&G < 25 AND ETF < -1500 → -12
    - MOMENTUM: MACD < -2000 AND BB < 0.2 → -10
    """
    if not market_data:
        return 50, {}, 0
    
    details = {}
    synergy_bonuses = {}
    total_synergy = 0
    
    current_price = market_data["current_price"]
    estimated_mvrv = market_data["estimated_mvrv"]
    rsi = market_data["rsi"]
    blocks_since = market_data["blocks_since_halving"]
    ma_50_week = market_data["ma_50_week"]
    ma_discount = (current_price / ma_50_week - 1) * 100 if ma_50_week > 0 else 0
    fg_value = fear_greed_data.get("value", 50)
    etf_data = market_data.get("etf_data")
    macd_histogram = market_data["macd_histogram"]
    bb_position = market_data["bb_position"]
    geo_score_val, geo_signal = score_geopolitical(geo_risk)
    pi_diff = market_data["pi_cycle_diff"]
    s2f = market_data["s2f_value"]
    
    # ===========================
    # COMPOSITE 1: VALUATION (30% total)
    # MVRV (60%) + RSI (40%)
    # ===========================
    mvrv_score, mvrv_signal = score_mvrv(estimated_mvrv)
    rsi_score, rsi_signal = score_rsi(rsi)
    
    valuation_raw = (mvrv_score * 0.6) + (rsi_score * 0.4)
    details["mvrv"] = {"value": estimated_mvrv, "score": mvrv_score, "signal": mvrv_signal, "weight": 18}  # 60% of 30%
    details["rsi"] = {"value": rsi, "score": rsi_score, "signal": rsi_signal, "weight": 12}  # 40% of 30%
    
    # VALUATION SYNERGY: MVRV < 1.0 AND RSI < 40 → -6 bonus (reduced from -12)
    valuation_synergy = 0
    if estimated_mvrv < 1.0 and rsi < 40:
        valuation_synergy = -6
        synergy_bonuses["valuation"] = -6
        total_synergy += 6
    details["valuation_synergy"] = valuation_synergy
    
    # ===========================
    # COMPOSITE 2: TREND (20% total)
    # 50W MA Discount (50%) + Cycle Position (50%)
    # ===========================
    ma_score, ma_signal = score_50w_ma_discount(ma_discount)
    cycle_score, cycle_signal = score_cycle_position(blocks_since)
    
    trend_raw = (ma_score * 0.5) + (cycle_score * 0.5)
    details["ma_discount"] = {"value": ma_discount, "score": ma_score, "signal": ma_signal, "weight": 10}  # 50% of 20%
    details["cycle"] = {"blocks": blocks_since, "score": cycle_score, "signal": cycle_signal, "weight": 10}  # 50% of 20%
    
    # TREND SYNERGY: 50W MA < -20% AND we're in BEAR ACCUMULATION phase (>104K blocks, <208K) → -8 bonus
    # v7.9a: Updated to match corrected peak timing (peaks at ~78K, bear starts ~104K)
    trend_synergy = 0
    if ma_discount < -20 and 104000 <= blocks_since <= 208000:
        trend_synergy = -8
        synergy_bonuses["trend"] = -8
        total_synergy += 8
    details["trend_synergy"] = trend_synergy
    
    # ===========================
    # COMPOSITE 3: SENTIMENT (17% total)
    # Fear & Greed (60%) + ETF (40%)
    # ===========================
    fg_score, fg_signal = score_fear_greed(fg_value)
    etf_score, etf_signal = score_etf_sentiment(etf_data)
    etf_value = etf_data.get("avg_daily_flow", 0) if etf_data else 0
    
    sentiment_raw = (fg_score * 0.6) + (etf_score * 0.4)
    details["fear_greed"] = {"value": fg_value, "score": fg_score, "signal": fg_signal, "weight": 10}  # 60% of 17%
    details["etf"] = {"value": etf_value, "score": etf_score, "signal": etf_signal, "weight": 7}  # 40% of 17%
    
    # SENTIMENT SYNERGY: F&G < 25 AND ETF outflows > 5000 (true capitulation) → -6 bonus (raised threshold from 1500)
    sentiment_synergy = 0
    if fg_value < 25 and etf_value < -5000:
        sentiment_synergy = -6
        synergy_bonuses["sentiment"] = -6
        total_synergy += 6
    details["sentiment_synergy"] = sentiment_synergy
    
    # ===========================
    # COMPOSITE 4: MOMENTUM (12% total)
    # MACD (50%) + Bollinger (50%)
    # ===========================
    macd_score, macd_signal = score_macd(macd_histogram)
    bb_score, bb_signal = score_bollinger(bb_position)
    
    momentum_raw = (macd_score * 0.5) + (bb_score * 0.5)
    details["macd"] = {"value": macd_histogram, "score": macd_score, "signal": macd_signal, "weight": 6}  # 50% of 12%
    details["bollinger"] = {"value": bb_position, "score": bb_score, "signal": bb_signal, "weight": 6}  # 50% of 12%
    
    # MOMENTUM SYNERGY: REMOVED (v7.2) - redundant with VALUATION synergy
    # Both measure oversold conditions - keeping only VALUATION to avoid double-counting
    momentum_synergy = 0
    # if macd_histogram < -2000 and bb_position < 0.2:
    #     momentum_synergy = -10
    #     synergy_bonuses["momentum"] = -10
    #     total_synergy += 10
    details["momentum_synergy"] = 0
    
    # ===========================
    # BULL MARKET SYNERGIES (v7.2) - INCREASE SCORE = MORE BEARISH
    # These fire when indicators show EXTREME BULL conditions
    # ===========================
    bull_total = 0
    
    # Bull VALUATION TOP: MVRV > 2.0 AND RSI > 70 → +6 (extreme bubble territory)
    if estimated_mvrv > 2.0 and rsi > 70:
        bull_total += 6
        synergy_bonuses["valuation_bull"] = +6
    
    # Bull TREND TOP: 50W MA > +20% AND Early bull (0-52K blocks) → +8 (extreme premium)
    if ma_discount > 20 and 0 <= blocks_since <= 52000:
        bull_total += 8
        synergy_bonuses["trend_bull"] = +8
    
    # Bull SENTIMENT TOP: F&G > 75 AND ETF inflows > 5000 → +6 (market euphoria)
    if fg_value > 75 and etf_value > 5000:
        bull_total += 6
        synergy_bonuses["sentiment_bull"] = +6
    
    details["bull_synergies"] = bull_total
    
    # ===========================
    # STANDALONE: GEOPOLITICAL (5%)
    # ===========================
    details["geopolitical"] = {"score": geo_score_val, "signal": geo_signal, "weight": 5}
    
    # ===========================
    # STANDALONE: PI CYCLE (3%)
    # ===========================
    pi_score, pi_signal = score_pi_cycle(pi_diff)
    details["pi_cycle"] = {"value": pi_diff, "score": pi_score, "signal": pi_signal, "weight": 3}
    
    # ===========================
    # STANDALONE: STOCK-TO-FLOW (3%)
    # ===========================
    s2f_score, s2f_signal = score_stock_to_flow(s2f)
    details["s2f"] = {"value": s2f, "score": s2f_score, "signal": s2f_signal, "weight": 3}
    
    # ===========================
    # CALCULATE BASE SCORE
    # ===========================
    # Sum weighted scores
    total_weight = 30 + 20 + 17 + 12 + 5 + 3 + 3  # = 90% (AI buffer is 10%)
    
    base_score = (
        (details["mvrv"]["score"] * details["mvrv"]["weight"]) +
        (details["rsi"]["score"] * details["rsi"]["weight"]) +
        (details["ma_discount"]["score"] * details["ma_discount"]["weight"]) +
        (details["cycle"]["score"] * details["cycle"]["weight"]) +
        (details["fear_greed"]["score"] * details["fear_greed"]["weight"]) +
        (details["etf"]["score"] * details["etf"]["weight"]) +
        (details["macd"]["score"] * details["macd"]["weight"]) +
        (details["bollinger"]["score"] * details["bollinger"]["weight"]) +
        (details["geopolitical"]["score"] * details["geopolitical"]["weight"]) +
        (details["pi_cycle"]["score"] * details["pi_cycle"]["weight"]) +
        (details["s2f"]["score"] * details["s2f"]["weight"])
    ) / total_weight
    
    # ===========================
    # APPLY SYNERGY BONUSES
    # Bear synergies (negative) = lower score = more bullish
    # Bull synergies (positive) = higher score = more bearish
    # ===========================
    score_after_synergy = base_score - total_synergy + bull_total
    
    # ===========================
    # AI DISCRETION BUFFER (10%)
    # For edge cases, qualitative overrides, regime detection
    # Can adjust score up or down by up to 5 points
    # ===========================
    ai_discretion = 0
    ai_discretion_reason = "No override"
    
    # Intra-cycle rally detection: bear phase (156K-208K blocks) but score suggests bull
    if 156000 <= blocks_since <= 208000 and score_after_synergy < 35:
        # Check if this is an intra-cycle rally (bear market bounce)
        # Rally conditions: BTC up > 20% from recent lows, RSI > 50
        if rsi > 50 or ma_discount > -15:
            # Likely an intra-cycle rally, not a new bull
            # Adjust score upward to reflect caution
            rally_adjustment = min(5, (score_after_synergy - 25))
            ai_discretion = rally_adjustment
            ai_discretion_reason = "INTRA-CYCLE RALLY detected - bear market bounce, not new bull"
    
    # Deep bear confirmation: score < 25 and all synergies firing
    if total_synergy >= 30 and score_after_synergy < 30:
        ai_discretion = -3
        ai_discretion_reason = "DEEP BEAR CONFIRMED - All composites aligning, maximum accumulation zone"
    
    final_score = max(0, min(100, score_after_synergy + ai_discretion))
    
    details["base_score"] = base_score
    details["synergy_bonuses"] = synergy_bonuses
    details["total_synergy"] = -total_synergy  # Store as positive for clarity
    details["ai_discretion"] = ai_discretion
    details["ai_discretion_reason"] = ai_discretion_reason
    details["final_score"] = final_score
    
    return final_score, details, total_synergy

def get_recommendation(score):
    """Get investment recommendation based on score (LOWER = BETTER)"""
    if score < 20:
        return "🟢 EXTREME BUY", "Historical major bottom - Maximum accumulation", "2-4 years"
    elif score < 30:
        return "🟢 DEEP BEAR", "Deep accumulation zone - High conviction", "1-3 years"
    elif score < 40:
        return "🟢 BUY", "Strong accumulation zone - Add to position", "6-18 months"
    elif score < 50:
        return "🟢 BUY", "Accumulation zone - Good value", "6-12 months"
    elif score < 60:
        return "🟡 ACCUMULATE", "Neutral - Slow accumulation on dips", "6-12 months"
    elif score < 70:
        return "🟠 HOLD", "Late cycle - Hold existing, no new buys", "3-6 months"
    elif score < 85:
        return "🔴 SELL", "Distribution phase - Take profits", "0-3 months"
    else:
        return "🔴 STRONG SELL", "Extreme overheated - Sell all", "0-3 months"

def get_probability(score):
    """Calculate historical win rate based on score"""
    if score < 20:
        return "85-95%", "Maximum opportunity zone - Best historical returns"
    elif score < 30:
        return "75-85%", "Strong accumulation - Very favorable risk/reward"
    elif score < 40:
        return "70-80%", "Good accumulation - Positive expected value"
    elif score < 50:
        return "60-70%", "Accumulation zone - Favorable risk/reward"
    elif score < 60:
        return "50-60%", "Neutral zone - Expected returns roughly market average"
    elif score < 70:
        return "35-50%", "Unfavorable - Sub-optimal entry"
    elif score < 85:
        return "20-35%", "Poor entry - Significant downside risk"
    else:
        return "10-20%", "Bearish zone - Major drawdown likely"

def get_profit_taking_guidance(score, btc_price, market_data, aave_debt=0, btc_position=0):
    """
    v7.4: INDICATOR-BASED profit-taking framework.
    Uses SCORE + BULL SYNERGIES + individual indicators (NOT price).
    
    MAX SELL: 25% of BTC position total
    
    Tiers (triggered by ANY condition at tier level):
    | Tier | Score > | Bull Synergies | MVRV > | RSI > | F&G > | Sell % | Cumulative |
    |------|---------|----------------|--------|-------|-------|--------|------------|
    | 1    | 55      | 1+             | 1.5    | 60    | 70    | 5%     | 5%         |
    | 2    | 65      | 2+             | 2.0    | 70    | 80    | 10%    | 15%        |
    | 3    | 75      | 3+ (all)       | 2.5    | 75    | 85    | 10%    | 25% max    |
    | 4    | 85      | MAX            | 3.0    | 80    | 90    | STOP   | 25% max    |
    
    Returns dict with guidance and suggested actions.
    """
    guidance = {
        "in_bull_run": False,
        "should_sell": False,
        "sell_percentage": 0,
        "sell_btc": 0,
        "sell_usd": 0,
        "cumulative_sold": 0,
        "cumulative_usd": 0,
        "tier": None,
        "action": "Accumulate - Not in bull run territory",
        "debt_repayment_possible": False,
        "recommendation": "Continue DCA at normal or elevated levels",
        "triggered_indicators": [],
        "bull_synergies_count": 0
    }
    
    # Only relevant if in potential bull territory (score > 45)
    if score < 45:
        return guidance
    
    # Get indicator values from market_data
    mvrv = market_data.get("estimated_mvrv", 0) if market_data else 0
    rsi = market_data.get("rsi", 0) if market_data else 0
    fg = market_data.get("fear_greed_value", 50) if market_data else 50
    bull_synergies = market_data.get("bull_synergies_count", 0) if market_data else 0
    ma_discount = market_data.get("ma_discount_pct", 0) if market_data else 0
    
    # Count how many bull synergy conditions are met
    bull_valuation = 1 if mvrv > 1.5 and rsi > 60 else 0
    bull_trend = 1 if ma_discount > 20 else 0
    bull_sentiment = 1 if fg > 70 else 0
    bull_total_conditions = bull_valuation + bull_trend + bull_sentiment
    
    guidance["bull_synergies_count"] = bull_total_conditions
    guidance["triggered_indicators"] = []
    
    if mvrv > 1.5 and rsi > 60:
        guidance["triggered_indicators"].append(f"MVRV {mvrv:.2f} > 1.5 + RSI {rsi:.1f} > 60")
    if ma_discount > 20:
        guidance["triggered_indicators"].append(f"50W MA premium {ma_discount:.1f}% > 20%")
    if fg > 70:
        guidance["triggered_indicators"].append(f"F&G {fg:.0f} > 70")
    
    # v7.4 Profit-taking tiers - INDICATOR-BASED
    tiers = [
        {
            "min_score": 55,
            "bull_synergies_min": 1,
            "mvrv_min": 1.5,
            "rsi_min": 60,
            "fg_min": 70,
            "sell_pct": 5,
            "cumulative_max": 5,
            "tier": 1,
            "action": "Trim 5% - Early profit-taking, build reserves"
        },
        {
            "min_score": 65,
            "bull_synergies_min": 2,
            "mvrv_min": 2.0,
            "rsi_min": 70,
            "fg_min": 80,
            "sell_pct": 10,
            "cumulative_max": 15,
            "tier": 2,
            "action": "Trim 10% - Moderate profits, clear partial debt"
        },
        {
            "min_score": 75,
            "bull_synergies_min": 3,
            "mvrv_min": 2.5,
            "rsi_min": 75,
            "fg_min": 85,
            "sell_pct": 10,
            "cumulative_max": 25,
            "tier": 3,
            "action": "Trim 10% - Clear remaining debt, hold rest"
        },
        {
            "min_score": 85,
            "bull_synergies_min": 3,
            "mvrv_min": 3.0,
            "rsi_min": 80,
            "fg_min": 90,
            "sell_pct": 0,
            "cumulative_max": 25,
            "tier": 4,
            "action": "STOP - Max 25% reached, hold remaining BTC"
        },
    ]
    
    # Find current tier - check conditions for each tier
    for tier_info in tiers:
        score_ok = score >= tier_info["min_score"]
        synergy_ok = bull_total_conditions >= tier_info["bull_synergies_min"]
        mvrv_ok = mvrv >= tier_info["mvrv_min"]
        rsi_ok = rsi >= tier_info["rsi_min"]
        fg_ok = fg >= tier_info["fg_min"]
        
        # Tier triggers if score AND at least one indicator condition met
        # OR if score AND synergy threshold met
        if score_ok:
            if synergy_ok or mvrv_ok or rsi_ok or fg_ok:
                guidance["in_bull_run"] = True
                guidance["tier"] = tier_info["tier"]
                guidance["action"] = tier_info["action"]
                
                # Only sell if under cumulative max
                if tier_info["sell_pct"] > 0:
                    cumulative_pct = tier_info["cumulative_max"]
                    if cumulative_pct <= 25:
                        guidance["should_sell"] = True
                        guidance["sell_percentage"] = tier_info["sell_pct"]
                        guidance["cumulative_sold"] = cumulative_pct
                break
    
    # Calculate actual amounts if position provided
    if btc_position > 0 and guidance["should_sell"]:
        guidance["sell_btc"] = btc_position * (guidance["sell_percentage"] / 100)
        guidance["sell_usd"] = guidance["sell_btc"] * btc_price
        guidance["cumulative_usd"] = btc_position * (guidance["cumulative_sold"] / 100) * btc_price
        
        # Can we clear debt with cumulative sales?
        if aave_debt > 0 and guidance["cumulative_usd"] >= aave_debt:
            guidance["debt_repayment_possible"] = True
            guidance["debt_after_sale"] = 0
            guidance["surplus_after_debt"] = guidance["cumulative_usd"] - aave_debt
        elif aave_debt > 0:
            guidance["debt_after_sale"] = aave_debt - guidance["cumulative_usd"]
    
    # Set recommendation based on tier
    if guidance["tier"] == 1:
        guidance["recommendation"] = "Take 5% profit - Build stablecoin reserves for future DCA"
    elif guidance["tier"] == 2:
        guidance["recommendation"] = "Take 10% profit - Partial debt repayment + stablecoins"
    elif guidance["tier"] == 3:
        guidance["recommendation"] = "Take 10% profit - Clear remaining debt, hold rest"
    elif guidance["tier"] == 4:
        guidance["recommendation"] = "Max 25% reached - Hold remaining BTC, don't sell more"
    else:
        guidance["recommendation"] = "Continue accumulation - Still in bear/deep discount zone"
    
    return guidance

# ======================
# MAIN DECISION ENGINE
# ======================

def run_analysis():
    """Run complete BTC decision analysis with v7.5 composites and Dune realized price"""
    print("=" * 70)
    print(f"BTC ACCUMULATION DECISION ENGINE v7.5")
    print(f"*** COMPOSITE INDICATORS + SYNERGY + DUNE REALIZED PRICE ***")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📊 Fetching market data...")
    
    market_data = get_market_status()
    fear_greed = get_fear_and_greed()
    geo_risk = get_geopolitical_risk()
    
    if not market_data:
        print("❌ Error: Could not fetch market data")
        return None
    
    # Calculate v7.2 score with composites and synergy
    print("\n🔍 Calculating v7.2 accumulation score with composites...")
    
    score, details, total_synergy = calculate_v7_score(market_data, fear_greed, geo_risk)
    recommendation, action, timeframe = get_recommendation(score)
    prob, prob_desc = get_probability(score)
    
    # Output results
    print("\n" + "=" * 70)
    print("📈 MARKET DATA")
    print("=" * 70)
    print(f"  Current Price:        ${market_data['current_price']:,.0f}")
    print(f"  50 Week MA:           ${market_data['ma_50_week']:,.0f} ({market_data['current_price']/market_data['ma_50_week']*100-100:.1f}%)")
    print(f"  RSI (20-WEEK):        {market_data['rsi']:.1f} *** WEEKLY - More smoothing, fewer false signals ***")
    print(f"  Estimated MVRV:       {market_data['estimated_mvrv']:.2f}")
    print(f"  Blocks Since Halving:  {market_data['blocks_since_halving']:,}")
    print(f"  Pi Cycle Diff:        {market_data['pi_cycle_diff']:.1f}%")
    print(f"  S2F Ratio:            {market_data['s2f_value']:.1f}")
    print(f"  MACD Histogram:       {market_data['macd_histogram']:.0f}")
    print(f"  Bollinger %B:         {market_data['bb_position']:.2f}")
    
    # ETF Data
    etf_data = market_data.get("etf_data")
    if etf_data and etf_data.get("data_source") != "None":
        source = etf_data.get("data_source", "Unknown")
        value = etf_data.get("avg_daily_flow", 0)
        if "BTC Dominance" in source:
            print(f"  ETF Sentiment:        {value:.1f}% BTC Dom ({source})")
        else:
            print(f"  ETF 7D Net Flow:      {value:,.0f} BTC ({source})")
    else:
        print(f"  ETF Sentiment:        Unavailable")
    
    print(f"  Fear & Greed:         {fear_greed.get('value', 50)} ({fear_greed.get('value_classification', 'Neutral')})")
    
    # Print composite breakdown
    print("\n" + "=" * 70)
    print("📊 v7.4 COMPOSITE SCORE BREAKDOWN")
    print("=" * 70)
    
    print(f"\n🎯 COMPOSITE 1: VALUATION (30%)")
    print(f"   MVRV:     {details['mvrv']['value']:.2f} → Score {details['mvrv']['score']:.0f} [{details['mvrv']['signal']}]")
    print(f"   RSI:      {details['rsi']['value']:.1f} → Score {details['rsi']['score']:.0f} [{details['rsi']['signal']}]")
    if details.get('valuation_synergy', 0) != 0:
        print(f"   ⚡ SYNERGY BONUS: {details['valuation_synergy']} (MVRV < 1.0 + RSI < 40) [v7.2 reduced]")
    
    print(f"\n🎯 COMPOSITE 2: TREND (20%)")
    print(f"   50W MA:   {details['ma_discount']['value']:.1f}% → Score {details['ma_discount']['score']:.0f} [{details['ma_discount']['signal']}]")
    print(f"   Cycle:    Block {details['cycle']['blocks']:,} → Score {details['cycle']['score']:.0f} [{details['cycle']['signal']}]")
    if details.get('trend_synergy', 0) != 0:
        print(f"   ⚡ SYNERGY BONUS: {details['trend_synergy']} (Deep discount + Bear phase) [v7.2 reduced]")
    
    print(f"\n🎯 COMPOSITE 3: SENTIMENT (17%)")
    print(f"   F&G:      {details['fear_greed']['value']:.0f} → Score {details['fear_greed']['score']:.0f} [{details['fear_greed']['signal']}]")
    print(f"   ETF:      {details['etf']['value']:.0f} BTC/day → Score {details['etf']['score']:.0f} [{details['etf']['signal']}]")
    if details.get('sentiment_synergy', 0) != 0:
        print(f"   ⚡ SYNERGY BONUS: {details['sentiment_synergy']} (Capitulation: F&G<25 + ETF outflows >5000) [v7.2 raised threshold]")
    
    print(f"\n🎯 COMPOSITE 4: MOMENTUM (12%)")
    print(f"   MACD:     {details['macd']['value']:.0f} → Score {details['macd']['score']:.0f} [{details['macd']['signal']}]")
    print(f"   Bollinger:{details['bollinger']['value']:.2f} → Score {details['bollinger']['score']:.0f} [{details['bollinger']['signal']}]")
    print(f"   ⚡ SYNERGY: REMOVED [v7.2 - was redundant with VALUATION synergy]")
    
    print(f"\n📊 STANDALONE INDICATORS")
    print(f"   Geopolitical: Score {details['geopolitical']['score']:.0f} [{details['geopolitical']['signal']}]")
    print(f"   Pi Cycle:     {details['pi_cycle']['value']:.1f}% → Score {details['pi_cycle']['score']:.0f} [{details['pi_cycle']['signal']}]")
    print(f"   Stock-to-Flow: {details['s2f']['value']:.1f} → Score {details['s2f']['score']:.0f} [{details['s2f']['signal']}]")
    
    # Bull Market Synergies (v7.2)
    if details.get('bull_synergies', 0) > 0:
        print(f"\n⚠️  BULL MARKET EXTREME SYNERGIES (v7.2)")
        if synergy_bonuses.get('valuation_bull'):
            print(f"   ⚡ VALUATION TOP: +6 (MVRV > 2.0 + RSI > 70)")
        if synergy_bonuses.get('trend_bull'):
            print(f"   ⚡ TREND TOP: +8 (50W MA > +20% + Early bull)")
        if synergy_bonuses.get('sentiment_bull'):
            print(f"   ⚡ SENTIMENT TOP: +6 (F&G > 75 + ETF inflows > 5000)")
    
    print(f"\n🤖 AI DISCRETION BUFFER (10%)")
    print(f"   Adjustment: {details.get('ai_discretion', 0):+.0f}")
    print(f"   Reason: {details.get('ai_discretion_reason', 'No override')}")
    
    print("\n" + "=" * 70)
    print("📊 SCORE CALCULATION SUMMARY")
    print("=" * 70)
    print(f"   Base Score:           {details.get('base_score', 0):.1f}")
    print(f"   Bear Synergies:       {int(details.get('total_synergy', 0))} (deep bear conditions)")
    if details.get('bull_synergies', 0) > 0:
        print(f"   Bull Synergies:       +{details.get('bull_synergies', 0):.0f} (extreme bubble)")
    print(f"   AI Discretion:        {details.get('ai_discretion', 0):+.0f}")
    print(f"   ─────────────────────────────────")
    print(f"   🎯 FINAL SCORE:        {details.get('final_score', 0):.1f}/100")
    print("=" * 70)
    
    print(f"\n  {recommendation}")
    print(f"  📋 Action: {action}")
    print(f"  📅 Suggested Timeframe: {timeframe}")
    print(f"\n📊 Historical Win Rate: {prob}")
    print(f"   {prob_desc}")
    
    # Determine cycle phase based on block height
    blocks = market_data['blocks_since_halving']
    if blocks < 52000:
        phase = "EARLY BULL (Blocks 0-52K)"
        strategy = "DCA 50% normal size, keep dry powder for corrections"
    elif blocks < 104000:
        phase = "MID BULL (Blocks 52K-104K)"
        strategy = "DCA 75% normal size, take some profits on 20%+ pumps"
    elif blocks < 156000:
        phase = "LATE BULL (Blocks 104K-156K)"
        strategy = "DCA 25% normal, take profits, build cash position"
    elif blocks < 208000:
        phase = "BEAR MARKET (Blocks 156K-208K)"
        strategy = "DCA 150% normal size, this is the accumulation zone"
    elif blocks < 260000:
        phase = "DEEP BEAR (Blocks 208K-260K)"
        strategy = "DCA 200% normal size, maximum accumulation mode"
    else:
        phase = "LATE BEAR (Blocks 260K+)"
        strategy = "DCA 200% normal size, near next halving"
    
    print(f"\n📅 CYCLE PHASE: {phase} (Block {blocks:,})")
    print(f"   Strategy: {strategy}")
    
    # v7.4: Check for profit-taking opportunity (INDICATOR-BASED)
    # Aave position defaults (can be overridden if position data available)
    aave_debt = 2504  # Current debt in USDC
    btc_position = 0.0876  # Current BTC collateral position
    
    # Get indicator values from details and market_data
    mvrv = details['mvrv']['value']
    rsi_val = details['rsi']['value']
    fg = details['fear_greed']['value']
    ma_disc = details['ma_discount']['value']
    
    # Calculate bull synergies count for profit-taking
    bull_valuation = 1 if mvrv > 1.5 and rsi_val > 60 else 0
    bull_trend = 1 if ma_disc > 20 else 0
    bull_sentiment = 1 if fg > 70 else 0
    bull_synergies_count = bull_valuation + bull_trend + bull_sentiment
    
    # Build market_data dict for profit-taking guidance
    profit_market_data = {
        "estimated_mvrv": mvrv,
        "rsi": rsi_val,
        "fear_greed_value": fg,
        "ma_discount_pct": ma_disc,
        "bull_synergies_count": bull_synergies_count
    }
    
    profit_guidance = get_profit_taking_guidance(score, market_data['current_price'], profit_market_data, aave_debt, btc_position)
    
    if profit_guidance["in_bull_run"]:
        print(f"\n⚠️  PROFIT-TAKING ALERT (v7.4 - INDICATOR-BASED)")
        print(f"   Tier: {profit_guidance['tier']} | Score: {score:.0f}/100")
        print(f"   📊 Bull Synergies Active: {profit_guidance['bull_synergies_count']}/3")
        for ind in profit_guidance.get("triggered_indicators", []):
            print(f"      • {ind}")
        print(f"   {profit_guidance['action']}")
        if profit_guidance["should_sell"]:
            print(f"   💰 Sell: {profit_guidance['sell_percentage']}% = {profit_guidance.get('sell_btc', 0):.5f} BTC (${profit_guidance.get('sell_usd', 0):,.0f})")
            print(f"   📊 Cumulative sold: {profit_guidance['cumulative_sold']}%")
            if profit_guidance["debt_repayment_possible"]:
                print(f"   ✅ Can CLEAR DEBT with cumulative sales!")
            elif profit_guidance.get("debt_after_sale", 0) > 0:
                print(f"   💸 Remaining debt after sale: ${profit_guidance.get('debt_after_sale', 0):,.0f}")
        print(f"   📋 {profit_guidance['recommendation']}")
    
    # Check for intra-cycle rally
    # Rally = bear market bounce, NOT a new bull
    # Detected when: we're in bear phase (600-750 days) BUT price has rallied significantly
    # RSI > 50 means momentum has turned bullish (bear market bounce)
    # MA discount > -15% (as percentage) means price has recovered toward the MA (typical of bounces)
    is_intra_cycle_rally = False
    rally_reason = ""
    ma_discount_pct = ((market_data['current_price'] / market_data['ma_50_week'] - 1) * 100) if market_data['ma_50_week'] > 0 else 0
    if 600 <= market_data['blocks_since_halving'] <= 750:
        # Only true rally if RSI recovered (>50) OR price near MA (> -15% discount)
        if market_data['rsi'] > 50 or ma_discount_pct > -15:
            is_intra_cycle_rally = True
            rally_reason = f"Bear market bounce - RSI {market_data['rsi']:.1f}, MA discount {ma_discount_pct:.1f}%"
    
    # Build alert object
    alert = {
        "timestamp": datetime.now().isoformat(),
        "score": round(score, 1),
        "recommendation": recommendation,
        "action": action,
        "timeframe": timeframe,
        "probability": prob,
        "price": market_data['current_price'],
        "realized_price": market_data.get('realized_price', 0),
        "realized_price_source": market_data.get('realized_price_source', 'unknown'),
        "regime": {
            "current": "INTRA_CYCLE_RALLY" if is_intra_cycle_rally else "BEAR_ACCUMULATION",
            "description": "🟡 INTRA-CYCLE RALLY - Bear market bounce. Don't confuse with new bull. Accumulation still OK but take profits on spikes." if is_intra_cycle_rally else "🟢 BEAR ACCUMULATION ZONE - Traditional buying opportunity. Price deeply discounted.",
            "dca_multiplier": 0.75 if is_intra_cycle_rally else 1.5,
            "borrow_allowed": False if is_intra_cycle_rally else True,
            "repay_urgency": "low" if is_intra_cycle_rally else "medium",
            "profit_taking": "Take 10-20% profit if BTC rallies > 20% from lows" if is_intra_cycle_rally else "Hold and accumulate - deep discount zone",
            "bull_signals": sum([1 for s in [details['mvrv'], details['rsi'], details['ma_discount'], details['cycle'], details['fear_greed'], details['macd']] if s['score'] < 35]),
            "bear_signals": sum([1 for s in [details['mvrv'], details['rsi'], details['ma_discount'], details['cycle']] if s['score'] > 55]),
            "is_intra_cycle_rally": is_intra_cycle_rally,
            "rally_reason": rally_reason
        },
        "indicators": {
            "mvrv": round(details['mvrv']['value'], 2),
            "rsi": round(details['rsi']['value'], 1),
            "cycle_blocks": details['cycle']['blocks'],
            "fear_greed": details['fear_greed']['value'],
            "discount_50w_ma": round(details['ma_discount']['value'], 1),
            "pi_cycle_diff": round(details['pi_cycle']['value'], 1),
            "s2f_value": round(details['s2f']['value'], 1),
            "etf_avg_daily_flow": round(details['etf']['value'], 0),
            "etf_net_flow_7d": round(details['etf']['value'] * 7, 0),
            "bollinger_position": round(details['bollinger']['value'], 2),
            "bollinger_bandwidth_pct": round(market_data.get('bb_bandwidth', 0), 1),
            "macd_histogram": round(details['macd']['value'], 0),
            "macd_hist_pct": round(details['macd']['value'] / market_data['current_price'] * 100, 2) if market_data['current_price'] > 0 else 0
        },
        "synergy_bonuses": details.get('synergy_bonuses', {}),
        "ai_discretion": {
            "adjustment": details.get('ai_discretion', 0),
            "reason": details.get('ai_discretion_reason', 'No override')
        },
        "cycle_phase": phase,
        "strategy": strategy,
        "profit_taking_v74": {
            "in_bull_run": profit_guidance["in_bull_run"],
            "tier": profit_guidance["tier"],
            "action": profit_guidance["action"],
            "should_sell": profit_guidance["should_sell"],
            "sell_percentage": profit_guidance["sell_percentage"],
            "sell_btc": round(profit_guidance.get("sell_btc", 0), 6),
            "sell_usd": round(profit_guidance.get("sell_usd", 0), 2),
            "cumulative_sold_pct": profit_guidance["cumulative_sold"],
            "cumulative_usd": round(profit_guidance.get("cumulative_usd", 0), 2),
            "debt_repayment_possible": profit_guidance["debt_repayment_possible"],
            "debt_after_sale": round(profit_guidance.get("debt_after_sale", 0), 2),
            "recommendation": profit_guidance["recommendation"],
            "triggered_indicators": profit_guidance.get("triggered_indicators", []),
            "bull_synergies_count": profit_guidance["bull_synergies_count"]
        }
    }
    
    return alert

def save_alert(alert, filepath="/tmp/btc_decision_alert.json"):
    """Save alert to file for monitoring"""
    try:
        with open(filepath, 'w') as f:
            json.dump(alert, f, indent=2)
    except Exception as e:
        print(f"Error saving alert: {e}")

def get_score_interpretation(score):
    """Convert numeric score to human-readable interpretation."""
    if score <= 20:
        return "🟢 Extreme Buy Zone - Historical cycle bottom conditions"
    elif score <= 35:
        return "🟢 Strong Buy - Favorable conditions for accumulation"
    elif score <= 50:
        return "🟡 Buy - Generally positive conditions, DCA appropriate"
    elif score <= 65:
        return "🟡 Neutral - Mixed signals, maintain current strategy"
    elif score <= 80:
        return "🟠 Sell - Overvalued conditions emerging"
    else:
        return "🔴 Strong Sell - Take profits, reduce exposure"

# DCA table aligned with strategy skill v8 (20-level, €1,100/month base budget)
DCA_TABLE = [
    (0, 5, 2.00, 550),    # €1,100/month
    (6, 10, 1.85, 509),
    (11, 15, 1.70, 468),
    (16, 20, 1.55, 426),
    (21, 25, 1.40, 385),
    (26, 30, 1.25, 344),
    (31, 35, 1.10, 303),
    (36, 40, 0.95, 261),
    (41, 45, 0.80, 220),
    (46, 50, 0.70, 193),
    (51, 55, 0.50, 138),
    (56, 60, 0.25, 69),
    (61, 65, 0.50, 138),
    (66, 70, 0.25, 69),
    (71, 100, 0.00, 0),
]

def get_dca_amounts(score):
    """Get DCA weekly/monthly amounts based on score using the 20-level strategy table.
    Returns: (weekly_eur, monthly_eur, multiplier, status)
    """
    # Float scores (e.g. 25.8) must map to integer buckets; floor before lookup
    score = int(score)
    for lo, hi, mult, weekly in DCA_TABLE:
        if lo <= score <= hi:
            monthly = round(weekly * 4.33)
            status = "STOP" if mult == 0 else "DCA"
            return weekly, monthly, mult, status
    # Default fallback
    return 138, 597, 0.50, "DCA"

def get_dca_recommendation(score, price=77840):
    """Legacy: Get DCA recommendation string based on score."""
    weekly, monthly, mult, status = get_dca_amounts(score)
    if status == "STOP":
        return "Pause DCA - Consider profit-taking"
    return f"€{monthly:,}/month (€{weekly:,}/week @ {int(mult*100)}% intensity)"

def save_report(alert, filepath="/tmp/btc_general_report.json"):
    """Save full report JSON for DApp /btc-report/summary endpoint"""
    try:
        indicators = alert.get("indicators", {})
        score = alert.get("score", 0)
        regime = alert.get("regime", {})
        
        # Calculate MVRV Z-Score (simplified)
        mvrv = indicators.get("mvrv", 1.0)
        mvrv_z = round((mvrv - 1.0) / 0.5, 2) if mvrv else 0
        
        # Determine action and detail
        action = alert.get("action", "")
        action_detail = f"Historical win rate: 60-70%. Suggested timeframe: {alert.get('timeframe', '3-6 months')}"
        
        # Get cycle position in days (approx from blocks)
        cycle_blocks = indicators.get("cycle_blocks", 0)
        days_since_halving = cycle_blocks / 144 if cycle_blocks else 0  # ~144 blocks/day
        
        # Use aligned DCA amounts from strategy table
        weekly_dca, monthly_dca, dca_mult, dca_status = get_dca_amounts(score)
        
        # Use recommendation for score_interpretation to ensure consistency
        score_interp = alert.get("recommendation", get_score_interpretation(score))
        
        report = {
            "generated": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "score_interpretation": score_interp,
            "score_detail": f"Based on MVRV {mvrv}, RSI {indicators.get('rsi', 0)}, Fear/Greed {indicators.get('fear_greed', 0)} and 8 other indicators",
            "dca_recommendation": get_dca_recommendation(score, alert.get("price", 77840)),
            "regime": regime.get("current", "UNKNOWN"),
            "regime_title": regime.get("description", "").split(" - ")[0] if regime.get("description") else "Market Regime",
            "regime_description": regime.get("description", "Market conditions unclear"),
            "action": action,
            "action_detail": action_detail,
            "recommendation": alert.get("recommendation", ""),
            "price": alert.get("price", 0),
            "summary": {
                "score": score,
                "recommendation": alert.get("recommendation", ""),
                "price": alert.get("price", 0),
                "dca_amount_weekly": weekly_dca,
                "dca_amount_monthly": monthly_dca,
                "dca_multiplier": dca_mult,
                "dca_status": dca_status,
                "strategy": alert.get("strategy", ""),
                "mvrv": indicators.get("mvrv", 0),
                "rsi": indicators.get("rsi", 0),
                "fear_greed": indicators.get("fear_greed", 0),
                "etf_net_flow_7d": indicators.get("etf_net_flow_7d", 0),
                "pi_cycle_diff": indicators.get("pi_cycle_diff", 0),
                "s2f_value": indicators.get("s2f_value", 0),
                "discount_50w_ma": indicators.get("discount_50w_ma", 0),
                "bollinger_position": indicators.get("bollinger_position", 0),
                "macd_histogram": indicators.get("macd_histogram", 0),
                "cycle_blocks": indicators.get("cycle_blocks", 0),
                "mvrv_z": mvrv_z,
                "cycle_phase": alert.get("cycle_phase", ""),
            }
        }
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"💾 Report saved to {filepath}")
        print(f"   Score: {score}/100 | Regime: {regime.get('current', 'UNKNOWN')}")
        print(f"   Indicators: MVRV={mvrv}, RSI={indicators.get('rsi', 0)}, Fear/Greed={indicators.get('fear_greed', 0)}")
    except Exception as e:
        print(f"Error saving report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run analysis
    alert = run_analysis()
    
    if alert:
        save_alert(alert)
        save_report(alert)
        
        print("\n" + "=" * 70)
        print("💾 Alert saved to /tmp/btc_decision_alert.json")
        print("💾 Report saved to /tmp/btc_general_report.json")
        print("=" * 70)
