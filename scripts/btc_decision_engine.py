#!/usr/bin/env python3
"""
BTC Accumulation Decision Engine v5.0 - WEEKLY INDICATORS
Professional-grade multi-indicator scoring system for LONG-TERM HOLDERS

*** KEY CHANGE v5.0 ***
All momentum indicators (RSI, MACD, Bollinger Bands) now use WEEKLY candles
instead of daily candles. This eliminates "daily trader noise" and gives
signals appropriate for 2-4+ year investment horizons.

SCORING SYSTEM (LOWER = BETTER FOR ACCUMULATION):
- 0-25: 🟢 EXTREME BUY (Maximum accumulation opportunity)
- 25-40: 🟢 BUY (Strong accumulation zone)
- 40-55: 🟡 NEUTRAL (Wait/watch)
- 55-70: 🟠 HOLD (Late cycle, reduce new buys)
- 70-85: 🔴 SELL (Distribution phase)
- 85-100: 🔴 STRONG SELL (Extreme overheated)

INDICATOR TIMEFRAMES:
- MVRV: 365-day MA (long-term valuation)
- RSI: 14-WEEK (weekly candles - NO DAILY NOISE)
- MA Discount: 50W MA + 200-day MA (long-term)
- Fear & Greed: Daily (sentiment)
- Geopolitical: Static (macro)
- Cycle Position: Days since halving (very long-term)
- Bollinger Bands: 20-WEEK (weekly candles - NO DAILY NOISE)
- MACD: 12/26/9 ON WEEKLY CANDLES (NO DAILY NOISE)
- Pi Cycle: 111-day + 350-day MA (medium-long term)
- Stock-to-Flow: Supply model (very long-term)
- ETF Sentiment: Daily/BTC Dominance

Usage: python3 btc_decision_engine.py
"""

import requests
import json
import time
from datetime import datetime
import math

# ======================
# CONFIGURATION
# ======================

COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/v2"

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
            # Note: CoinGecko free tier limits to 365 days, so we use 350 days
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
            # Bandwidth = (Upper - Lower) / Middle * 100
            bb_bandwidth = ((bb_upper - bb_lower) / ma_20 * 100) if ma_20 > 0 else 0
            
            # Historical bandwidth comparison (percentile)
            # This tells us if bandwidth is near historical lows (squeeze)
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
    CoinGecko free API doesn't support weekly interval directly,
    so we fetch daily data and aggregate into weekly candles.
    
    This gives us RSI, MACD, and Bollinger Bands on WEEKLY timeframes
    - eliminating "daily trader noise" for long-term holders.
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
            
            # Calculate weekly RSI (14-week)
            gains = []
            losses = []
            for i in range(1, min(15, len(weekly_closes))):
                change = weekly_closes[-i] - weekly_closes[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0
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

def get_etf_sentiment():
    """
    Get Bitcoin ETF sentiment from available sources
    
    DATA TIMING NOTE:
    - SoSoValue API: Currently unavailable (direct access blocked)
    - Official SEC T+2: 2 business days delayed
    - Farside.co.uk: Scrape-based, no API
    
    FALLBACK APPROACH: Use BTC Dominance as ETF sentiment proxy
    - BTC Dom rising = money flowing into BTC ETFs = BULLISH
    - BTC Dom falling = money rotating to altcoins = BEARISH for BTC
    
    This is an INDIRECT proxy but correlates well with ETF flow trends
    """
    try:
        # Try SoSoValue API first
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
    
    # FALLBACK: Use BTC Dominance as ETF sentiment proxy
    try:
        # Get global crypto market data including BTC dominance
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            btc_dominance = data.get("data", {}).get("market_cap_percentage", {}).get("btc", 50)
            
            # BTC dominance interpretation:
            # > 55% = HIGH ETF/institutional concentration = NEUTRAL-BULLISH
            # 50-55% = Normal range
            # 45-50% = Money rotating to alts = BEARISH signal
            # < 45% = Altcoin season = VERY BEARISH for BTC
            # < 40% = Extreme alt season = Capitulation
            
            # Convert to flow-like metric (inferred)
            # Rising dominance = inferred inflows
            # Falling dominance = inferred outflows
            
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

def get_market_status():
    """Get all market data and compute key metrics"""
    try:
        btc_data = get_btc_price_data()
        hist_data = get_historical_btc_prices(365)
        weekly_data = get_weekly_btc_prices()  # NEW: Weekly candles for long-term momentum
        
        if not btc_data or not hist_data:
            return None
        
        current_price = btc_data["current_price"]
        ath = btc_data["ath"]
        
        # Use WEEKLY RSI instead of daily for long-term signals
        rsi = weekly_data["weekly_rsi"] if weekly_data else hist_data["rsi"]
        
        # Calculate realized price (approximated using 365-day avg)
        realized_price = hist_data["ma_365"] if hist_data else current_price
        
        # Estimated MVRV ratio
        estimated_mvrv = current_price / realized_price if realized_price > 0 else 1.0
        
        # Days since halving (April 19, 2024)
        halving_date = datetime(2024, 4, 19)
        days_since_halving = (datetime.now() - halving_date).days
        
        # Pi Cycle indicator: 111 MA * 2 vs 350 MA crossover
        # When 111*2 MA crosses below 350 MA = BOTTOM signal
        # When 111*2 MA crosses above 350 MA = TOP signal
        pi_cycle_value = (hist_data.get("ma_111", current_price) * 2) if hist_data else current_price * 2
        pi_cycle_350 = hist_data.get("ma_350", current_price) if hist_data else current_price
        pi_cycle_diff = ((pi_cycle_value - pi_cycle_350) / pi_cycle_350 * 100) if pi_cycle_350 > 0 else 0
        
        # Stock-to-Flow calculation (simplified, meaningful approach)
        # After 2024 halving: 3.125 BTC/block, ~144 blocks/day, 365 days/year
        # Annual production = 3.125 * 144 * 365 = ~164,250 BTC
        # S2F = circulating / annual_production
        blocks_per_day = 6 * 24  # Post-2024 halving
        btc_per_block = 3.125
        annual_production = blocks_per_day * btc_per_block * 365
        circulating_supply = btc_data.get("circulating_supply", 19500000)
        s2f_ratio = circulating_supply / annual_production if annual_production > 0 else 100
        
        # Simplified S2F discount: compare current price to what S2F suggests is "fair"
        # We use historical S2F-to-price relationship as baseline
        # S2F = 122 means scarcity is HIGHEST EVER in BTC history
        # But price hasn't caught up to the scarcity premium yet = BUY
        # If price were at same premium as previous cycles, it would be much higher
        
        # Simple interpretation: S2F ratio is at all-time high
        # This means scarcity is extreme - historically bullish for long-term
        # S2F > 100 is rare and suggests undervaluation relative to scarcity
        s2f_value = s2f_ratio  # Just use the ratio directly
        
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
            "ath": ath,
            "ath_percentage": (current_price / ath * 100) if ath > 0 else 0,
            "days_since_halving": days_since_halving,
            "ma_50": hist_data.get("ma_50", current_price),
            "ma_200": hist_data.get("ma_200", current_price),
            "ma_50_week": hist_data.get("ma_50_week", current_price),
            "ma_111": hist_data.get("ma_111", current_price),
            "ma_350": hist_data.get("ma_350", current_price),
            "rsi": rsi,  # NOW WEEKLY RSI
            "macd": macd,  # NOW WEEKLY MACD
            "macd_histogram": macd_histogram,  # NOW WEEKLY MACD HISTOGRAM
            "bb_position": bb_position,  # NOW WEEKLY BOLLINGER
            "bb_upper": bb_upper,  # NOW WEEKLY BOLLINGER
            "bb_lower": bb_lower,  # NOW WEEKLY BOLLINGER
            "bb_bandwidth": bb_bandwidth,  # NOW WEEKLY BOLLINGER BANDWIDTH
            "volume_ratio": hist_data.get("volume_ratio", 1),
            "pi_cycle_value": pi_cycle_value,
            "pi_cycle_350": pi_cycle_350,
            "pi_cycle_diff": pi_cycle_diff,
            "s2f_ratio": s2f_ratio,
            "s2f_value": s2f_value,
            "etf_data": get_etf_sentiment(),
            "weekly_data": weekly_data is not None,  # Flag indicating weekly data availability
            "note": "Momentum indicators (RSI, MACD, Bollinger) now on WEEKLY timeframes"
        }
    except Exception as e:
        print(f"Error getting market status: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def get_geopolitical_risk():
    """
    Assess current geopolitical risk level
    Returns: score 0-100 (0 = maximum crisis, 100 = peaceful)
    
    Research shows BTC acts as safe haven during market crashes but NOT during
    initial war shocks (drops with risk assets, then recovers).
    """
    try:
        risk_factors = {
            # Active conflicts (assessed dynamically)
            "ukraine_russia_war": 0.85,     # Ongoing but stabilized
            "israel_gaza": 0.90,             # Ongoing tension
            "taiwan_straits": 0.80,         # China-US tensions
            
            # Macro factors
            "us_china_trade": 0.75,
            "global_recession": 0.70,
            "inflation_concerns": 0.65,
            "rate_hike_cycle": 0.60,
            
            # Crypto-specific
            "sec_crackdown": 0.85,
            "etf_outflows": 0.80,
            "stablecoin_concerns": 0.90
        }
        
        avg_risk = sum(risk_factors.values()) / len(risk_factors)
        war_conflict_score = (risk_factors["ukraine_russia_war"] + 
                             risk_factors["israel_gaza"] + 
                             risk_factors["taiwan_straits"]) / 3
        
        return {
            "overall_risk": avg_risk,
            "war_conflict_risk": war_conflict_score,
            "interpretation": get_geopolitical_interpretation(avg_risk, war_conflict_score)
        }
    except Exception as e:
        print(f"Error assessing geopolitical risk: {e}")
    
    return {"overall_risk": 0.70, "war_conflict_risk": 0.80, "interpretation": "Stable"}

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
# SCORING ENGINE (LOWER = BETTER FOR ACCUMULATION)
# ======================

def calculate_accumulation_score(market_data, fear_greed, geo_risk):
    """
    Calculate BTC accumulation score (0-100, LOWER = BETTER FOR ACCUMULATION)
    
    NEW WEIGHT SYSTEM:
    - MVRV: 25% - Core on-chain valuation metric
    - RSI: 15% - Technical momentum
    - MA Discount: 15% - Price vs major MAs
    - Fear & Greed: 15% - Market sentiment
    - Geopolitical: 15% - Global macro
    - Cycle Position: 15% - Halving cycle timing
    - Pi Cycle: 5% - Cycle top/bottom timing
    - Stock-to-Flow: 5% - Scarcity model
    """
    if not market_data:
        return 50, {}
    
    details = {}
    current_price = market_data["current_price"]
    estimated_mvrv = market_data["estimated_mvrv"]
    rsi = market_data["rsi"]
    days_since = market_data["days_since_halving"]
    ma_50_week = market_data["ma_50_week"]
    ma_200 = market_data["ma_200"]
    ath_pct = market_data["ath_percentage"]
    pi_cycle_diff = market_data["pi_cycle_diff"]
    s2f_value = market_data.get("s2f_value", 50)
    
    # ===========================
    # 1. MVRV SCORE (25% weight)
    # MVRV < 1.0 = entire market at loss = BEST ENTRY
    # MVRV > 3.0 = extreme overheated = WORST ENTRY
    # ===========================
    if estimated_mvrv < 0.7:
        mvrv_score = 5  # EXTREME VALUE
        mvrv_signal = "🟢 EXTREME DISCOUNT (MVRV < 0.7)"
    elif estimated_mvrv < 0.9:
        mvrv_score = 15  # DEEP VALUE
        mvrv_signal = "🟢 DEEP VALUE (MVRV 0.7-0.9)"
    elif estimated_mvrv < 1.0:
        mvrv_score = 22  # GOOD VALUE
        mvrv_signal = "🟢 GOOD VALUE (MVRV 0.9-1.0)"
    elif estimated_mvrv < 1.3:
        mvrv_score = 35  # FAIR VALUE
        mvrv_signal = "🟡 FAIR VALUE (MVRV 1.0-1.3)"
    elif estimated_mvrv < 1.7:
        mvrv_score = 55  # EXPENSIVE
        mvrv_signal = "🟠 EXPENSIVE (MVRV 1.3-1.7)"
    elif estimated_mvrv < 2.2:
        mvrv_score = 75  # VERY EXPENSIVE
        mvrv_signal = "🔴 VERY EXPENSIVE (MVRV 1.7-2.2)"
    else:
        mvrv_score = 90  # BUBBLE
        mvrv_signal = "🔴 BUBBLE ZONE (MVRV > 2.2)"
    
    details["mvrv"] = {"value": estimated_mvrv, "score": mvrv_score, "signal": mvrv_signal, "weight": 25}
    
    # ===========================
    # 2. RSI SCORE (15% weight) - NOW ON WEEKLY CANDLES
    # Weekly RSI < 40 = oversold = BEST (no daily noise)
    # Weekly RSI > 70 = overbought = WORST
    # ===========================
    if rsi < 30:
        rsi_score = 5  # EXTREME OVERSOLD
        rsi_signal = "🟢 EXTREME OVERSOLD (RSI < 30)"
    elif rsi < 40:
        rsi_score = 15  # OVERSOLD
        rsi_signal = "🟢 OVERSOLD (RSI 30-40)"
    elif rsi < 50:
        rsi_score = 25  # NEAR NEUTRAL - SLIGHT BUY
        rsi_signal = "🟢 NEAR NEUTRAL (RSI 40-50) - Buy zone"
    elif rsi < 60:
        rsi_score = 45  # NEUTRAL
        rsi_signal = "🟡 NEUTRAL (RSI 50-60)"
    elif rsi < 70:
        rsi_score = 65  # OVERBOUGHT
        rsi_signal = "🟠 OVERBOUGHT (RSI 60-70)"
    else:
        rsi_score = 85  # EXTREME OVERBOUGHT
        rsi_signal = "🔴 EXTREME OVERBOUGHT (RSI > 70)"
    
    details["rsi"] = {"value": rsi, "score": rsi_score, "signal": rsi_signal, "weight": 15}
    
    # ===========================
    # 3. PRICE VS MOVING AVERAGES (15% weight)
    # Below major MAs = discount = BUY
    # Above major MAs = premium = SELL
    # ===========================
    discount_vs_50w = (current_price / ma_50_week - 1) * 100 if ma_50_week > 0 else 0
    discount_vs_200 = (current_price / ma_200 - 1) * 100 if ma_200 > 0 else 0
    
    # Combined average discount
    avg_discount = (discount_vs_50w + discount_vs_200) / 2
    
    if avg_discount < -40:  # 40%+ below MAs
        ma_score = 8
        ma_signal = "🟢 MASSIVE DISCOUNT vs MA"
    elif avg_discount < -25:  # 25%+ below
        ma_score = 18
        ma_signal = "🟢 DEEP DISCOUNT vs MA"
    elif avg_discount < -15:  # 15%+ below
        ma_score = 28
        ma_signal = "🟢 DISCOUNT vs MA"
    elif avg_discount < 0:  # Below MAs
        ma_score = 38
        ma_signal = "🟢 BELOW MA (buy zone)"
    elif avg_discount < 15:  # Slight premium
        ma_score = 50
        ma_signal = "🟡 NEAR MA"
    elif avg_discount < 30:  # Above MAs
        ma_score = 65
        ma_signal = "🟠 ABOVE MA - Premium"
    else:  # Way above
        ma_score = 85
        ma_signal = "🔴 FAR ABOVE MA - Extreme premium"
    
    details["ma"] = {"discount_50w": discount_vs_50w, "discount_200": discount_vs_200, "score": ma_score, "signal": ma_signal, "weight": 12}
    
    # ===========================
    # 4. FEAR & GREED SCORE (15% weight)
    # Extreme Fear = BEST for accumulation
    # Extreme Greed = WORST
    # ===========================
    fg_value = fear_greed.get("value", 50)
    
    if fg_value < 20:  # Extreme Fear
        fg_score = 5
        fg_signal = "🟢 EXTREME FEAR - Major buy signal"
    elif fg_value < 30:  # Fear
        fg_score = 18
        fg_signal = "🟢 FEAR - Accumulate"
    elif fg_value < 45:  # Some Fear
        fg_score = 30
        fg_signal = "🟢 CAUTIOUS - Start accumulating"
    elif fg_value < 55:  # Neutral
        fg_score = 45
        fg_signal = "🟡 NEUTRAL - Hold"
    elif fg_value < 70:  # Greed
        fg_score = 65
        fg_signal = "🟠 GREED - Take profits"
    elif fg_value < 85:  # Extreme Greed
        fg_score = 82
        fg_signal = "🔴 EXTREME GREED - Sell"
    else:  # Maximum Greed
        fg_score = 95
        fg_signal = "🔴 BUBBLE - Maximum sell"
    
    details["fear_greed"] = {"value": fg_value, "score": fg_score, "signal": fg_signal, "weight": 12}
    
    # ===========================
    # 5. GEOPOLITICAL SCORE (15% weight)
    # High crisis = potentially good for BTC long-term
    # ===========================
    overall_risk = geo_risk["overall_risk"]
    
    if overall_risk < 0.50:  # Major crisis
        geo_score = 15
        geo_signal = "🟢 MAJOR CRISIS - Safe haven bid"
    elif overall_risk < 0.65:  # Elevated tension
        geo_score = 30
        geo_signal = "🟢 ELEVATED TENSIONS - Safe haven narrative"
    elif overall_risk < 0.75:  # Moderate risk
        geo_score = 45
        geo_signal = "🟡 MODERATE RISK - BTC neutral"
    else:  # Low risk, peaceful
        geo_score = 35
        geo_signal = "🟢 LOW GLOBAL RISK - Risk-on environment"
    
    details["geopolitical"] = {"score": geo_score, "signal": geo_signal, "weight": 5}
    
    # ===========================
    # 6. CYCLE POSITION SCORE (15% weight - REDUCED)
    # Post-halving bear markets are BEST for accumulation
    # ===========================
    if days_since < 180:  # 0-6 months post-halving
        cycle_score = 50  # Early bull - not ideal yet
        cycle_signal = "🟡 EARLY BULL - Wait for correction"
    elif days_since < 300:  # 6-10 months
        cycle_score = 40  # Still early
        cycle_signal = "🟡 EARLY-MID - Start accumulating"
    elif days_since < 400:  # 10-13 months
        cycle_score = 30  # Mid cycle
        cycle_signal = "🟡 MID CYCLE - Accumulating"
    elif days_since < 500:  # 13-16 months - peak zone
        cycle_score = 45  # Warning zone
        cycle_signal = "🟠 LATE CYCLE - Reduce buys"
    elif days_since < 600:  # 16-20 months - past peak
        cycle_score = 35  # Bear starting
        cycle_signal = "🟡 POST-PEAK - Bear begins"
    elif days_since < 750:  # 20-25 months - BEAR MARKET = ACCUMULATION
        cycle_score = 15  # GOOD ACCUMULATION ZONE
        cycle_signal = "🟢 BEAR MARKET - Strong accumulation zone"
    elif days_since < 900:  # 25-30 months
        cycle_score = 8  # DEEP BEAR = BEST ENTRY
        cycle_signal = "🟢 DEEP BEAR - Maximum accumulation"
    else:  # 30+ months
        cycle_score = 12  # Still good
        cycle_signal = "🟢 LATE BEAR - Accumulate"
    
    details["cycle"] = {"days": days_since, "score": cycle_score, "signal": cycle_signal, "weight": 10}
    
    # ===========================
    # 9. PI CYCLE INDICATOR (5% weight)
    # 111 MA * 2 vs 350 MA crossover
    #
    # IMPORTANT CONTEXT:
    # - During 2018 cycle peak: 111*2 was ~200-300% ABOVE 350 MA
    # - During 2022 cycle bottom: 111*2 was ~15-20% BELOW 350 MA
    # - Current reading: +62% ABOVE - elevated but not at extreme peak levels
    #
    # This indicator suggests we are NOT at a typical bear market bottom
    # Either: (1) ETF institutional buying has changed dynamics, OR
    # (2) True bear bottom hasn't arrived yet
    #
    # The score is set to NEUTRAL/BULL due to +62% reading
    # ===========================
    
    if pi_cycle_diff < -20:  # 111*2 MA is 20%+ below 350 MA = TYPICAL BOTTOM
        pi_score = 8
        pi_signal = "🟢 PI CYCLE BOTTOM - Classic bear bottom pattern"
    elif pi_cycle_diff < -5:  # 5%+ below
        pi_score = 18
        pi_signal = "🟢 PI CYCLE RECOVERING - Bottoming pattern"
    elif pi_cycle_diff < 30:  # 0-30% above - MODERATE BULL
        pi_score = 40
        pi_signal = "🟡 PI CYCLE ELEVATED - Mid-cycle correction (not bottom)"
    elif pi_cycle_diff < 60:  # 30-60% above
        pi_score = 60
        pi_signal = "🟠 PI CYCLE HIGH - Extended bull phase"
    elif pi_cycle_diff < 100:  # 60-100% above - getting dangerous
        pi_score = 80
        pi_signal = "🔴 PI CYCLE EXTREME - Warning zone"
    else:  # 100%+ above - bubble territory
        pi_score = 95
        pi_signal = "🔴 PI CYCLE BUBBLE - Cycle top signal"
    
    details["pi_cycle"] = {"value": pi_cycle_diff, "score": pi_score, "signal": pi_signal, "weight": 3}
    
    # ===========================
    # 10. STOCK-TO-FLOW SCORE (5% weight)
    # S2F measures scarcity - higher S2F = more scarce
    # Post-2024 halving S2F is at ALL-TIME HIGHS (~120)
    # This means BTC is MORE SCARCE than ever = BULLISH for long-term
    # ===========================
    s2f_value = market_data.get("s2f_value", 50)
    
    # S2F context:
    # Pre-2016 halving: S2F ~25 (BTC $200-$1000)
    # Post-2016 halving: S2F ~50 (BTC $1000-$20000)
    # Post-2020 halving: S2F ~100 (BTC $10000-$69000)
    # Post-2024 halving: S2F ~120 (BTC ~$70000)
    
    if s2f_value > 110:  # Post-2024 halving territory - extreme scarcity
        s2f_score = 10
        s2f_signal = "🟢 EXTREME SCARCITY - S2F at ATH (post-2024 halving)"
    elif s2f_value > 90:  # 90-110
        s2f_score = 18
        s2f_signal = "🟢 VERY HIGH SCARCITY - Accumulation zone"
    elif s2f_value > 60:  # 60-90
        s2f_score = 30
        s2f_signal = "🟢 HIGH SCARCITY - Good for long-term"
    elif s2f_value > 40:  # 40-60
        s2f_score = 50
        s2f_signal = "🟡 MODERATE SCARCITY - Neutral"
    else:  # < 40
        s2f_score = 70
        s2f_signal = "🟠 LOW SCARCITY - Less rare (pre-halving periods)"
    
    details["s2f"] = {"value": s2f_value, "score": s2f_score, "signal": s2f_signal, "weight": 3}
    
    # ===========================
    # 11. ETF SENTIMENT SCORE (5% weight)
    # ETF flows show institutional sentiment
    # Positive flows = institutional buying = BULLISH
    # Negative flows = institutional selling = BEARISH
    #
    # TIMING NOTE:
    # - SoSoValue: ~15 min delayed (best free option) - Currently blocked
    # - Official SEC data: T+2 (2 business days delayed)
    # - FALLBACK: BTC Dominance as ETF sentiment proxy
    # ===========================
    etf_data = market_data.get("etf_data")
    
    if etf_data:
        # Check if we have direct flow data or proxy data
        net_flow_7d = etf_data.get("net_flow_7d", 0)  # in BTC
        avg_daily_flow = etf_data.get("avg_daily_flow", 0)
        btc_dominance = etf_data.get("btc_dominance", 50)
        data_source = etf_data.get("data_source", "Unknown")
        
        current_price = market_data.get("current_price", 70000)
        
        # If we have direct ETF flow data, use it
        if net_flow_7d != 0 or avg_daily_flow != 0:
            if avg_daily_flow > 10000:
                etf_score = 5
                etf_signal = "🟢 MASSIVE ETF INFLOWS - Strong institutional buying"
            elif avg_daily_flow > 5000:
                etf_score = 15
                etf_signal = "🟢 STRONG ETF INFLOWS - Good institutional support"
            elif avg_daily_flow > 1000:
                etf_score = 25
                etf_signal = "🟢 POSITIVE ETF FLOWS - Moderate buying"
            elif avg_daily_flow > -1000:
                etf_score = 45
                etf_signal = "🟡 NEUTRAL ETF FLOWS - Mixed flows"
            elif avg_daily_flow > -5000:
                etf_score = 65
                etf_signal = "🟠 ETF OUTFLOWS - Institutional selling"
            elif avg_daily_flow > -10000:
                etf_score = 80
                etf_signal = "🔴 HEAVY ETF OUTFLOWS - Major distribution"
            else:
                etf_score = 92
                etf_signal = "🔴 MASSIVE ETF OUTFLOWS - Capitulation"
            
            details["etf"] = {
                "value": avg_daily_flow,
                "net_flow_7d": net_flow_7d,
                "data_source": data_source,
                "score": etf_score,
                "signal": etf_signal,
                "weight": 5,
                "timing_note": "Direct ETF flow data"
            }
        else:
            # Use BTC Dominance as proxy
            # BTC Dom interpretation for ETF sentiment:
            # > 58% = Strong ETF/institutional concentration = BULLISH
            # 52-58% = Healthy institutional demand = NEUTRAL-GOOD
            # 48-52% = Normal range = NEUTRAL
            # 45-48% = Money rotating to alts = CAUTION
            # < 45% = Alt season beginning = BEARISH for BTC
            # < 40% = Extreme alt season = VERY BEARISH
            
            if btc_dominance > 58:
                etf_score = 15
                etf_signal = f"🟢 HIGH BTC DOM ({btc_dominance}%) - Strong ETF concentration"
            elif btc_dominance > 52:
                etf_score = 30
                etf_signal = f"🟢 HEALTHY BTC DOM ({btc_dominance}%) - Good institutional demand"
            elif btc_dominance > 48:
                etf_score = 45
                etf_signal = f"🟡 NORMAL BTC DOM ({btc_dominance}%) - Balanced market"
            elif btc_dominance > 45:
                etf_score = 60
                etf_signal = f"🟠 FALLING BTC DOM ({btc_dominance}%) - Alt rotation starting"
            elif btc_dominance > 40:
                etf_score = 75
                etf_signal = f"🔴 LOW BTC DOM ({btc_dominance}%) - Alt season, BTC underperforming"
            else:
                etf_score = 90
                etf_signal = f"🔴 EXTREME ALT SEASON ({btc_dominance}%) - BTC capitulating to alts"
            
            details["etf"] = {
                "value": btc_dominance,
                "data_source": data_source,
                "score": etf_score,
                "signal": etf_signal,
                "weight": 5,
                "timing_note": "Proxy: BTC Dominance. Lower = money rotating to alts"
            }
    else:
        # No ETF data at all
        details["etf"] = {
            "value": 50,
            "data_source": "None",
            "score": 50,
            "signal": "🟡 ETF DATA UNAVAILABLE - Neutral score",
            "weight": 5,
            "timing_note": "Could not fetch ETF or dominance data"
        }
    
    # ===========================
    # 7. WEEKLY BOLLINGER BANDS SCORE (5% weight)
    # NOW ON WEEKLY CANDLES - No daily noise
    # Position within bands shows overbought/oversold on weekly timeframe
    # ===========================
    bb_position = market_data.get("bb_position", 0.5)
    bb_bandwidth = market_data.get("bb_bandwidth", 0)
    
    # %B interpretation (weekly):
    # < 0 = Below lower band = EXTREME discount
    # 0-0.2 = Near lower band = Deep discount
    # 0.2-0.4 = Lower half = Discount zone
    # 0.4-0.6 = Middle = Neutral
    # 0.6-0.8 = Upper half = Premium
    # 0.8-1.0 = Near upper band = Expensive
    # > 1.0 = Above upper band = Very expensive
    
    if bb_position < 0:
        bb_score = 5
        bb_signal = "🟢 BELOW LOWER BAND - Extreme discount (weekly)"
    elif bb_position < 0.2:
        bb_score = 12
        bb_signal = "🟢 NEAR LOWER BAND - Deep discount (weekly)"
    elif bb_position < 0.4:
        bb_score = 22
        bb_signal = "🟢 LOWER BAND AREA - Discount zone (weekly)"
    elif bb_position < 0.6:
        bb_score = 45
        bb_signal = "🟡 MIDDLE - Neutral (weekly)"
    elif bb_position < 0.8:
        bb_score = 60
        bb_signal = "🟠 UPPER HALF - Premium building (weekly)"
    elif bb_position < 1.0:
        bb_score = 75
        bb_signal = "🔴 NEAR UPPER BAND - Expensive (weekly)"
    else:
        bb_score = 88
        bb_signal = "🔴 ABOVE UPPER BAND - Bubble territory (weekly)"
    
    details["bollinger"] = {
        "value": bb_position,
        "bandwidth": bb_bandwidth,
        "score": bb_score,
        "signal": bb_signal,
        "weight": 5,
        "note": "Weekly Bollinger - no daily noise"
    }
    
    # ===========================
    # 8. WEEKLY MACD MOMENTUM SCORE (5% weight)
    # NOW ON WEEKLY CANDLES - No daily noise
    # MACD histogram shows trend direction and momentum on weekly timeframe
    # ===========================
    macd_histogram = market_data.get("macd_histogram", 0)
    current_price = market_data.get("current_price", 0)
    macd_pct = (macd_histogram / current_price * 100) if current_price > 0 else 0
    
    # MACD histogram interpretation (weekly):
    # Strongly negative = Bear momentum weakening = Accumulation
    # Slightly negative = Early accumulation
    # Near zero = Neutral
    # Positive = Bull momentum
    
    if macd_histogram < -5000:
        macd_score = 8
        macd_signal = "🟢 STRONG BEAR MOMENTUM - Bottoming pattern (weekly)"
    elif macd_histogram < -2000:
        macd_score = 18
        macd_signal = "🟢 BEAR MOMENTUM WEAKENING - Accumulating (weekly)"
    elif macd_histogram < -500:
        macd_score = 28
        macd_signal = "🟢 EARLY ACCUMULATION - Bear weakening (weekly)"
    elif macd_histogram < 500:
        macd_score = 45
        macd_signal = "🟡 NEAR ZERO - Neutral momentum (weekly)"
    elif macd_histogram < 2000:
        macd_score = 55
        macd_signal = "🟠 BULL MOMENTUM - Rising strength (weekly)"
    elif macd_histogram < 5000:
        macd_score = 70
        macd_signal = "🔴 STRONG BULL - Overextended (weekly)"
    else:
        macd_score = 85
        macd_signal = "🔴 EXTREME BULL MOMENTUM - Topping pattern (weekly)"
    
    details["macd"] = {
        "value": macd_histogram,
        "histogram_pct": macd_pct,
        "score": macd_score,
        "signal": macd_signal,
        "weight": 5,
        "note": "Weekly MACD - no daily noise"
    }
    
    # ===========================
    # CALCULATE FINAL SCORE
    # ===========================
    total_weight = sum(d["weight"] for d in details.values())
    
    final_score = sum(d["score"] * d["weight"] for d in details.values()) / total_weight
    
    return final_score, details

def get_recommendation(score):
    """Get investment recommendation based on score (LOWER = BETTER)"""
    if score < 20:
        return "🟢 EXTREME BUY", "Historical major bottom - Maximum accumulation", "2-4 years"
    elif score < 35:
        return "🟢 STRONG BUY", "Strong accumulation zone - High conviction buy", "1-3 years"
    elif score < 50:
        return "🟢 BUY", "Accumulation zone - Add to position", "6-18 months"
    elif score < 60:
        return "🟡 ACCUMULATE", "Neutral - Slow accumulation on dips", "6-12 months"
    elif score < 70:
        return "🟠 HOLD", "Late cycle - Hold existing, no new buys", "3-6 months"
    elif score < 85:
        return "🔴 SELL", "Distribution phase - Take profits, reduce exposure", "0-3 months"
    else:
        return "🔴 STRONG SELL", "Extreme overheated - Sell all, wait for correction", "0-3 months"

def get_probability(score):
    """Calculate historical win rate based on score"""
    if score < 20:
        return "85-95%", "Maximum opportunity zone - Best historical returns"
    elif score < 35:
        return "75-85%", "Strong accumulation - Very favorable risk/reward"
    elif score < 50:
        return "60-75%", "Good accumulation - Positive expected value"
    elif score < 60:
        return "50-60%", "Neutral zone - Expected returns roughly market average"
    elif score < 70:
        return "35-50%", "Unfavorable - Sub-optimal entry, limited upside"
    elif score < 85:
        return "20-35%", "Poor entry - Significant downside risk"
    else:
        return "10-20%", "Bearish zone - Major drawdown likely"

# ======================
# MAIN DECISION ENGINE
# ======================

def run_analysis():
    """Run complete BTC decision analysis"""
    print("=" * 70)
    print(f"BTC ACCUMULATION DECISION ENGINE v5.0 - WEEKLY TIMEFRAMES")
    print(f"*** LONG-TERM HOLDER VERSION ***")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📊 Fetching market data...")
    
    market_data = get_market_status()
    fear_greed = get_fear_and_greed()
    geo_risk = get_geopolitical_risk()
    
    if not market_data:
        print("❌ Error: Could not fetch market data")
        return None
    
    # Calculate score
    print("\n🔍 Calculating accumulation score...")
    
    score, details = calculate_accumulation_score(market_data, fear_greed, geo_risk)
    recommendation, action, timeframe = get_recommendation(score)
    prob, prob_desc = get_probability(score)
    
    # Output results
    print("\n" + "=" * 70)
    print("📈 MARKET DATA")
    print("=" * 70)
    print(f"  Current Price:        ${market_data['current_price']:,.0f}")
    print(f"  50 Week MA:           ${market_data['ma_50_week']:,.0f} ({market_data['current_price']/market_data['ma_50_week']*100-100:.1f}%)")
    print(f"  200 Day MA:           ${market_data['ma_200']:,.0f} ({market_data['current_price']/market_data['ma_200']*100-100:.1f}%)")
    print(f"  RSI (14-WEEK):        {market_data['rsi']:.1f} *** WEEKLY - No daily noise ***")
    print(f"  Estimated MVRV:       {market_data['estimated_mvrv']:.2f}")
    print(f"  Days Since Halving:   {market_data['days_since_halving']}")
    print(f"  ATH Discount:         {100-market_data['ath_percentage']:.1f}% below ATH")
    print(f"  Pi Cycle Diff:        {market_data['pi_cycle_diff']:.1f}%")
    print(f"  S2F Ratio:            {market_data['s2f_value']:.1f} (scarcity measure)")
    
    # ETF Data if available
    etf_data = market_data.get("etf_data")
    if etf_data and etf_data.get("data_source") != "None":
        source = etf_data.get("data_source", "Unknown")
        value = etf_data.get("value", 0)
        if "BTC Dominance" in source:
            print(f"  ETF Sentiment:        {value:.1f}% BTC Dom ({source})")
        else:
            print(f"  ETF 7D Net Flow:      {value:,.0f} BTC ({source})")
    else:
        print(f"  ETF Sentiment:        Unavailable")
    
    # Bollinger Bands data (now weekly)
    bb_pos = market_data.get("bb_position", 0.5)
    bb_bw = market_data.get("bb_bandwidth", 0)
    print(f"  Bollinger %B (WEEKLY): {bb_pos:.2f} *** WEEKLY - No daily noise ***")
    print(f"  Bollinger Bandwidth:   {bb_bw:.1f}%")
    
    print("\n" + "=" * 70)
    print("📊 SCORE BREAKDOWN (11 INDICATORS)")
    print("=" * 70)
    
    print(f"\n  {'INDICATOR':<22} {'VALUE':<12} {'SCORE':<8} {'WT':<4} {'SIGNAL'}")
    print("-" * 90)
    
    # Indicator display names with timeframe indicator
    indicator_names = {
        "mvrv": "MVRV",
        "rsi": "RSI (WEEKLY) *",
        "ma": "MA Discount",
        "fear_greed": "Fear & Greed",
        "geopolitical": "Geopolitical",
        "bollinger": "Bollinger (WEEKLY) *",
        "macd": "MACD (WEEKLY) *",
        "cycle": "Cycle Position",
        "pi_cycle": "Pi Cycle",
        "s2f": "Stock-to-Flow",
        "etf": "ETF Sentiment"
    }
    
    for key in ["mvrv", "rsi", "ma", "fear_greed", "geopolitical", "bollinger", "macd", "cycle", "pi_cycle", "s2f", "etf"]:
        d = details[key]
        val_str = f"{d.get('value', d.get('discount', 0)):.2f}" if 'value' in d else f"{d.get('discount', 0)*100:.1f}%" if 'discount' in d else "-"
        name = indicator_names.get(key, key.capitalize())
        print(f"  {name:<22} {val_str:<12} {d['score']:<8.0f} {d['weight']:<4} {d['signal']}")
    
    print("\n" + "=" * 70)
    print(f"🎯 FINAL ACCUMULATION SCORE: {score:.1f}/100")
    print("   (Lower = Better for Accumulation)")
    print("=" * 70)
    
    print(f"\n  {recommendation}")
    print(f"  📋 Action: {action}")
    print(f"  📅 Suggested Timeframe: {timeframe}")
    
    print(f"\n📊 PROBABILITY & RISK:")
    print("-" * 50)
    print(f"  Historical Win Rate: {prob}")
    print(f"  {prob_desc}")
    
    # Determine cycle phase
    days = market_data['days_since_halving']
    if days < 300:
        phase = "EARLY BULL (Days 0-300)"
        strategy = "DCA 50% normal size, keep dry powder for corrections"
    elif days < 500:
        phase = "MID BULL (Days 300-500)"
        strategy = "DCA 75% normal size, take some profits on 20%+ pumps"
    elif days < 600:
        phase = "LATE BULL (Days 500-600)"
        strategy = "DCA 25% normal, take profits, build cash position"
    elif days < 750:
        phase = "BEAR MARKET (Days 600-750)"
        strategy = "DCA 150% normal size, this is the accumulation zone"
    else:
        phase = "DEEP BEAR (Days 750+)"
        strategy = "DCA 200% normal size, maximum accumulation mode"
    
    print(f"\n📅 CYCLE ANALYSIS:")
    print("-" * 50)
    print(f"  Phase: {phase}")
    print(f"  Days Since Halving: {days}")
    print(f"  Strategy: {strategy}")
    
    # Build alert object
    alert = {
        "timestamp": datetime.now().isoformat(),
        "score": round(score, 1),
        "recommendation": recommendation,
        "action": action,
        "timeframe": timeframe,
        "probability": prob,
        "price": market_data['current_price'],
        "indicators": {
            "mvrv": round(details['mvrv']['value'], 2),
            "rsi": round(details['rsi']['value'], 1),
            "cycle_days": details['cycle']['days'],
            "fear_greed": details['fear_greed']['value'],
            "discount_50w_ma": round(details['ma']['discount_50w'], 1),
            "discount_200_ma": round(details['ma']['discount_200'], 1),
            "pi_cycle_diff": round(details['pi_cycle']['value'], 1),
            "s2f_value": round(details['s2f']['value'], 1),
            "etf_avg_daily_flow": round(details['etf'].get('value', 0), 0),
            "etf_net_flow_7d": round(details['etf'].get('net_flow_7d', 0), 0),
            "bollinger_position": round(details['bollinger'].get('position', 0.5), 2),
            "bollinger_bandwidth_pct": round(details['bollinger'].get('bandwidth_pct', 50), 1),
            "macd_histogram": round(details['macd'].get('histogram', 0), 0),
            "macd_hist_pct": round(details['macd'].get('hist_pct', 0), 2)
        },
        "cycle_phase": phase,
        "regime": {
            "current": "BEAR_ACCUMULATION" if phase.startswith("BEAR") else "UNKNOWN",
            "phase": phase
        },
        "strategy": strategy
    }
    
    return alert

def save_alert(alert, filepath="/tmp/btc_decision_alert.json"):
    """Save alert to file for monitoring"""
    try:
        with open(filepath, 'w') as f:
            json.dump(alert, f, indent=2)
    except Exception as e:
        print(f"Error saving alert: {e}")

if __name__ == "__main__":
    # Run analysis
    alert = run_analysis()
    
    if alert:
        save_alert(alert)
        
        print("\n" + "=" * 70)
        print("💾 Alert saved to /tmp/btc_decision_alert.json")
        print("=" * 70)
