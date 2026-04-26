#!/usr/bin/env python3
"""
BTC General Report Service - Colombia Staking
==============================================
Generates a detailed BTC market report for COLS stakers.
Reads signals from existing btc_decision_engine.py output.
Exposes report via HTTP for DApp consumption.

This is a SEPARATE service from the personal daily strategy.
It uses the cached signals from the existing automation.
"""

import json
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Data paths
BTC_SIGNALS_FILE = "/tmp/btc_decision_alert.json"
CACHE_FILE = "/tmp/btc_general_report.json"
PORT = 3001  # Different port from kepler-proxy (3000)

def load_btc_signals():
    """Load BTC signals from existing decision engine output."""
    try:
        with open(BTC_SIGNALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Could not load signals: {e}"}

def get_regime_description(regime):
    """Get detailed description of current market regime."""
    descriptions = {
        "BEAR_ACCUMULATION": {
            "title": "🐻 BEAR MARKET ACCUMULATION ZONE",
            "description": "This is traditionally the best time to accumulate Bitcoin. Historical data shows that buying during bear markets has produced the best long-term returns. The market is in fear, but conditions are ideal for patient investors.",
            "action": "✅ ACCUMULATE",
            "action_detail": "This is a generational buying opportunity. Maintain or increase your DCA purchases."
        },
        "INTRA_CYCLE_RALLY": {
            "title": "⚠️ INTRA-CYCLE RALLY (NOT A NEW BULL)",
            "description": "This is a relief rally WITHIN a bear market, not the start of a new bull market. BTC may pump 20-40% but will likely make new lows. Do NOT increase leverage during this phase.",
            "action": "⚠️ ACCUMULATE CAUTIOUSLY",
            "action_detail": "Continue systematic DCA but do NOT take on new debt. Be prepared for the rally to fade."
        },
        "EARLY_BULL": {
            "title": "🟢 EARLY BULL MARKET",
            "description": "The bull run is just beginning. Historical pattern shows this phase can last 6-18 months before reaching overheated territory. Conditions remain favorable for DCA.",
            "action": "✅ ACCUMULATE",
            "action_detail": "Continue systematic DCA. Early bull markets historically deliver 3-10x returns from this level."
        },
        "BULL_CORRECTION": {
            "title": "🟡 BULL MARKET CORRECTION",
            "description": "Normal healthy correction within a bull market. These are buying opportunities before the next leg up. BTC often drops 30-50% during these corrections before resuming the uptrend.",
            "action": "✅ BUY THE DIP",
            "action_detail": "Consider increasing DCA temporarily. Corrections are healthy and expected."
        },
        "MID_BULL": {
            "title": "🟠 MID BULL MARKET",
            "description": "We're in the middle of a bull run. Still room to accumulate but with more caution. This phase can last 12-24 months before reaching bubble territory.",
            "action": "🟡 DCA MODERATELY",
            "action_detail": "Reduce DCA to 50-75% of normal levels. Start thinking about taking some profits."
        },
        "LATE_BULL_BUBBLE": {
            "title": "🔴 LATE BULL / EARLY BUBBLE",
            "description": "Market is overheating. We are entering the dangerous zone where corrections can be severe (50-80%). This is NOT the time to be aggressive. Start taking profits.",
            "action": "🔴 REDUCE/STOP DCA",
            "action_detail": "Stop or severely reduce DCA. Take profits systematically. Do NOT borrow to buy more."
        },
        "MAXIMUM_BUBBLE": {
            "title": "☠️ MAXIMUM BUBBLE TERRITORY",
            "description": "EXTREME CAUTION. This level has historically marked major Bitcoin TOPS. The rally may continue for weeks but the eventual crash will be severe. Cash out is the priority.",
            "action": "☠️ TAKE PROFITS NOW",
            "action_detail": "Sell 25-50% of your position. Do NOT buy. The crash from here has historically been 80-90%."
        },
        "UNKNOWN": {
            "title": "❓ UNKNOWN REGIME",
            "description": "The algorithm cannot determine the current market regime with confidence. Wait for clearer signals before making major allocation changes.",
            "action": "⏸️ HOLD",
            "action_detail": "Maintain current position. Do not make major changes until regime is clearer."
        }
    }
    return descriptions.get(regime, descriptions["UNKNOWN"])

def get_score_interpretation(score):
    """Interpret the 0-100 accumulation score."""
    if score <= 10:
        return {
            "level": "🟢🟢🟢 EXTREME FEAR",
            "description": "Maximum conviction buying opportunity. This level historically marks generational Bitcoin bottoms. The crowd is in panic mode, but history shows this is exactly when the biggest gains are made.",
            "dca_recommendation": "MAXIMUM DCA (200%)"
        }
    elif score <= 20:
        return {
            "level": "🟢🟢 STRONG FEAR",
            "description": "Excellent accumulation zone. Fear dominates but conditions are ideal for long-term investors. This is the second-best entry point in any market cycle.",
            "dca_recommendation": "STRONG DCA (155-185%)"
        }
    elif score <= 35:
        return {
            "level": "🟢 FEAR",
            "description": "Good accumulation territory. Still early in the bear-to-bull transition. Sentiment is cautious but conditions favor long-term holders.",
            "dca_recommendation": "ELEVATED DCA (110-140%)"
        }
    elif score <= 50:
        return {
            "level": "🟡 NEUTRAL",
            "description": "Neutral zone. Neither extreme fear nor greed. BTC is fairly valued relative to holder behavior. This is normal for post-correction phases.",
            "dca_recommendation": "NORMAL DCA (70-100%)"
        }
    elif score <= 65:
        return {
            "level": "🟠 EARLY GREED",
            "description": "Market is getting expensive. Future returns from this level are historically more modest. Consider reducing new positions.",
            "dca_recommendation": "REDUCED DCA (25-50%)"
        }
    elif score <= 75:
        return {
            "level": "🔴 GREED",
            "description": "BTC is in premium territory. We are entering the danger zone. Corrections of 30-50% are likely from here. Start taking profits.",
            "dca_recommendation": "STOP DCA (0%)"
        }
    else:
        return {
            "level": "☠️ EXTREME GREED",
            "description": "Maximum caution required. This level has historically marked Bitcoin TOPS. The crash from here has historically been 80-95%. Cash out is the priority.",
            "dca_recommendation": "TAKE PROFITS (Sell BTC)"
        }

def get_indicator_description(indicator_name, value, data):
    """Get detailed description of each indicator."""
    descriptions = {
        "MVRV": {
            "name": "Market Value to Realized Value (MVRV)",
            "description": "Compares Bitcoin's current market cap to what holders actually paid. When MVRV < 1.0, BTC trades below what holders paid on average = historically a bottom signal.",
            "ranges": {
                "bullish": "< 1.0 = Deep value (generational buying)",
                "neutral": "1.0-2.0 = Fair value range",
                "bearish": "> 2.5 = Premium (bubble territory)"
            }
        },
        "RSI": {
            "name": "Relative Strength Index (Weekly)",
            "description": "Measures momentum. Below 40 = oversold (buying opportunity), Above 70 = overbought (danger zone).",
            "ranges": {
                "bullish": "< 40 = Oversold (accumulate)",
                "neutral": "40-65 = Normal range",
                "bearish": "> 70 = Overbought (reduce exposure)"
            }
        },
        "FearGreed": {
            "name": "Fear & Greed Index",
            "description": "Measures crowd sentiment. Extreme fear = buying opportunity, Extreme greed = top signal.",
            "ranges": {
                "bullish": "< 30 = Fear (accumulate)",
                "neutral": "30-70 = Neutral",
                "bearish": "> 75 = Greed (take profits)"
            }
        },
        "MA50W": {
            "name": "50-Week Moving Average Discount",
            "description": "How far BTC is below its 50-week average price. Bigger discount = more undervalued.",
            "ranges": {
                "bullish": "< -20% = Deep discount (accumulate)",
                "neutral": "-20% to +10% = Near average",
                "bearish": "> +30% = Premium to MA"
            }
        },
        "PiCycle": {
            "name": "Pi Cycle Indicator",
            "description": "Uses 111-day and 350-day moving averages. When the 111DMA crosses below 350DMA = bear market signal. Currently shows how far we are from cycle top/bottom.",
            "ranges": {
                "bullish": "< 0 = Bear market confirmed",
                "neutral": "0-100 = Normal range",
                "bearish": "> 100 = Near cycle peak"
            }
        },
        "S2F": {
            "name": "Stock-to-Flow Model",
            "description": "Measures scarcity. Higher S2F = more scarce = higher predicted price. This model uses halving cycles.",
            "ranges": {
                "bullish": "> 100 = Post-halving scarcity",
                "neutral": "50-100 = Normal",
                "bearish": "< 50 = Pre-halving abundance"
            }
        },
        "ETFFlows": {
            "name": "Bitcoin ETF 7-Day Net Flow",
            "description": "Tracks institutional money flow through Bitcoin ETFs. Positive = institutions buying (bullish), Negative = institutions selling.",
            "ranges": {
                "bullish": "> $500M inflow = Strong institutional support",
                "neutral": "-$500M to +$500M = Mixed",
                "bearish": "< -$500M outflow = Institutional selling"
            }
        },
        "CycleDay": {
            "name": "Days Since Halving",
            "description": "Tracks position in the 4-year cycle. Post-halving years 1-2 = historically the best performing.",
            "ranges": {
                "bullish": "Year 1-2 (Days 0-730) = Accumulation phase",
                "neutral": "Year 3 (730-1095) = Bull continuation",
                "bearish": "Year 4 (1095+) = Late cycle / bear"
            }
        }
    }
    return descriptions.get(indicator_name, {"name": indicator_name, "description": "No data", "ranges": {}})

def generate_report():
    """Generate the general BTC report."""
    signals = load_btc_signals()
    
    if "error" in signals:
        return {"error": signals["error"]}
    
    # Extract key data
    score = signals.get("score", 50)
    recommendation = signals.get("recommendation", "NEUTRAL")
    price = signals.get("price", 0)
    realized_price = signals.get("realized_price", 0)
    realized_source = signals.get("realized_price_source", "unknown")
    # Map cycle_phase to regime key
    cycle_phase = signals.get("cycle_phase", "")
    phase_key = cycle_phase.split(" (")[0] if cycle_phase else ""
    phase_to_regime = {
        "BEAR MARKET": "BEAR_ACCUMULATION",
        "EARLY BULL": "INTRA_CYCLE_RALLY",
        "MID BULL": "MID_BULL",
        "LATE BULL": "LATE_BULL_BUBBLE",
        "DEEP BEAR": "BEAR_ACCUMULATION"
    }
    regime = phase_to_regime.get(phase_key, "UNKNOWN")
    regime_data = {"current": regime, "phase": cycle_phase}
    regime_data = signals.get("regime", {})
    indicators = signals.get("indicators", {})
    
    # Get interpretations
    score_interp = get_score_interpretation(score)
    regime_interp = get_regime_description(regime)
    
    # Calculate if BTC is above/below realized price
    if price > 0 and realized_price > 0:
        vs_realized_pct = ((price - realized_price) / realized_price) * 100
        vs_realized_label = "ABOVE" if vs_realized_pct > 0 else "BELOW"
        vs_realized_abs = abs(vs_realized_pct)
    else:
        vs_realized_pct = 0
        vs_realized_label = "UNKNOWN"
        vs_realized_abs = 0
    
    # Build indicators list with interpretations
    indicators_list = []
    
    # MVRV
    mvrv = indicators.get("mvrv", 0)
    if mvrv < 1.0:
        mvrv_signal = "🟢 BULLISH"
    elif mvrv < 2.0:
        mvrv_signal = "🟡 NEUTRAL"
    else:
        mvrv_signal = "🔴 BEARISH"
    indicators_list.append({
        "name": "MVRV Ratio",
        "value": f"{mvrv:.2f}",
        "signal": mvrv_signal,
        "detail": f"Market is {abs(((mvrv - 1) * 100)):.1f}% {'above' if mvrv > 1 else 'below'} realized value"
    })
    
    # RSI
    rsi = indicators.get("rsi", 50)
    if rsi < 40:
        rsi_signal = "🟢 OVERSOLD"
    elif rsi < 70:
        rsi_signal = "🟡 NEUTRAL"
    else:
        rsi_signal = "🔴 OVERBOUGHT"
    indicators_list.append({
        "name": "Weekly RSI",
        "value": f"{rsi:.1f}",
        "signal": rsi_signal,
        "detail": f"{'Historically oversold - buying opportunity' if rsi < 40 else 'Overbought - caution warranted' if rsi > 70 else 'Within normal range'}"
    })
    
    # Fear & Greed
    fg = indicators.get("fear_greed", 50)
    if fg < 30:
        fg_signal = "🟢 FEAR"
    elif fg < 75:
        fg_signal = "🟡 NEUTRAL"
    else:
        fg_signal = "🔴 GREED"
    indicators_list.append({
        "name": "Fear & Greed",
        "value": f"{fg}/100",
        "signal": fg_signal,
        "detail": f"Crowd sentiment: {'Extreme fear - accumulation zone' if fg < 30 else 'Extreme greed - top signal' if fg > 75 else 'Neutral'}"
    })
    
    # 50W MA Discount
    ma_disc = indicators.get("discount_50w_ma", 0)
    ma_disc_abs = abs(ma_disc)
    if ma_disc < -20:
        ma_signal = "🟢 DEEP DISCOUNT"
    elif ma_disc < 10:
        ma_signal = "🟡 NEAR AVG"
    else:
        ma_signal = "🔴 PREMIUM"
    indicators_list.append({
        "name": "50-Week MA",
        "value": f"-{ma_disc_abs:.1f}%" if ma_disc < 0 else f"+{ma_disc:.1f}%",
        "signal": ma_signal,
        "detail": f"BTC is trading {ma_disc_abs:.1f}% {'below' if ma_disc < 0 else 'above'} its 50-week average"
    })
    
    # ETF Flows
    etf_flow = indicators.get("etf_net_flow_7d", 0)
    if etf_flow > 500:
        etf_signal = "🟢 STRONG INFLOW"
    elif etf_flow > -500:
        etf_signal = "🟡 MIXED"
    else:
        etf_signal = "🔴 OUTFLOW"
    flow_abs = abs(etf_flow)
    indicators_list.append({
        "name": "ETF 7-Day Flow",
        "value": f"${flow_abs:,.0f}M",
        "signal": etf_signal,
        "detail": f"{'Institutional buying pressure' if etf_flow > 0 else 'Institutional selling pressure' if etf_flow < 0 else 'No significant ETF activity'}"
    })
    
    # Pi Cycle
    pi_diff = indicators.get("pi_cycle_diff", 0)
    if pi_diff < 0:
        pi_signal = "🟢 BEAR MARKET"
    elif pi_diff < 100:
        pi_signal = "🟡 NORMAL"
    else:
        pi_signal = "🔴 NEAR TOP"
    indicators_list.append({
        "name": "Pi Cycle",
        "value": f"{pi_diff:.1f}",
        "signal": pi_signal,
        "detail": f"{'Below 350DMA - bear confirmed' if pi_diff < 0 else 'Within normal range' if pi_diff < 100 else 'Near cycle peak zone'}"
    })
    
    # Cycle Day
    cycle_day = indicators.get("cycle_blocks", 0)
    if cycle_day < 52000:
        cycle_signal = "🟢 YEAR 1-2"
    elif cycle_day < 104000:
        cycle_signal = "🟡 MID CYCLE"
    else:
        cycle_signal = "🔴 LATE CYCLE"
    indicators_list.append({
        "name": "Cycle Position",
        "value": f"Day {cycle_day:,}",
        "signal": cycle_signal,
        "detail": f"Week {(cycle_day / 7):.0f} of current 4-year cycle"
    })
    
    # S2F
    s2f = indicators.get("s2f_value", 50)
    if s2f > 100:
        s2f_signal = "🟢 HIGH SCARCITY"
    elif s2f > 50:
        s2f_signal = "🟡 NORMAL"
    else:
        s2f_signal = "🔴 LOW SCARCITY"
    indicators_list.append({
        "name": "Stock-to-Flow",
        "value": f"{s2f:.1f}",
        "signal": s2f_signal,
        "detail": f"Scarcity factor post-halving: {'High (post-2024 halving)' if s2f > 100 else 'Increasing toward next halving'}"
    })
    
    # Bollinger Position
    bb_pos = indicators.get("bollinger_position", 0.5)
    if bb_pos < 0.2:
        bb_signal = "🟢 NEAR BOTTOM"
    elif bb_pos > 0.8:
        bb_signal = "🔴 NEAR TOP"
    else:
        bb_signal = "🟡 MID RANGE"
    indicators_list.append({
        "name": "Bollinger Position",
        "value": f"{bb_pos*100:.0f}%",
        "signal": bb_signal,
        "detail": f"Price position within Bollinger Bands: {'Near lower band (support)' if bb_pos < 0.2 else 'Near upper band (resistance)' if bb_pos > 0.8 else 'Mid-range'}"
    })
    
    # MACD
    macd_hist = indicators.get("macd_histogram", 0)
    if macd_hist > 0:
        macd_signal = "🟢 BULLISH MOMENTUM"
    else:
        macd_signal = "🔴 BEARISH MOMENTUM"
    indicators_list.append({
        "name": "MACD Histogram",
        "value": f"{macd_hist:,.0f}",
        "signal": macd_signal,
        "detail": f"{'Histogram positive - momentum favoring buyers' if macd_hist > 0 else 'Histogram negative - momentum favoring sellers'}"
    })
    
    # Dune Z-Score
    z_score = indicators.get("dune_z_score", 0)
    if z_score < -1:
        z_signal = "🟢 BELOW FAIR VALUE"
    elif z_score < 1:
        z_signal = "🟡 NEAR FAIR VALUE"
    else:
        z_signal = "🔴 ABOVE FAIR VALUE"
    indicators_list.append({
        "name": "MVRV Z-Score",
        "value": f"{z_score:.2f}",
        "signal": z_signal,
        "detail": f"Statistical deviation from fair value: {'Significantly undervalued' if z_score < -1 else 'Within normal range' if z_score < 1 else 'Significantly overvalued'}"
    })
    
    # Count bullish/bearish signals
    bullish_count = sum(1 for ind in indicators_list if "🟢" in ind["signal"])
    bearish_count = sum(1 for ind in indicators_list if "🔴" in ind["signal"])
    neutral_count = sum(1 for ind in indicators_list if "🟡" in ind["signal"])
    
    # Build regime-specific guidance
    regime_guidance = {
        "dca_multiplier": regime_data.get("dca_multiplier", 1.0),
        "borrow_allowed": regime_data.get("borrow_allowed", False),
        "repay_urgency": regime_data.get("repay_urgency", "low"),
        "profit_taking": regime_data.get("profit_taking", "none"),
        "bull_signals": regime_data.get("bull_signals", 0),
        "bear_signals": regime_data.get("bear_signals", 0),
    }
    
    # DCA table based on score
    dca_table = []
    for s in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]:
        if s <= 5:
            dca_pct = 200
        elif s <= 10:
            dca_pct = 185
        elif s <= 15:
            dca_pct = 170
        elif s <= 20:
            dca_pct = 155
        elif s <= 25:
            dca_pct = 140
        elif s <= 30:
            dca_pct = 125
        elif s <= 35:
            dca_pct = 110
        elif s <= 40:
            dca_pct = 95
        elif s <= 45:
            dca_pct = 80
        elif s <= 50:
            dca_pct = 70
        elif s <= 55:
            dca_pct = 50
        elif s <= 60:
            dca_pct = 25
        elif s <= 65:
            dca_pct = 50
        elif s <= 70:
            dca_pct = 25
        elif s <= 75:
            dca_pct = 0
        else:
            dca_pct = 0
        dca_eur = 200 * (dca_pct / 100)
        dca_table.append({"score": s, "dca_pct": dca_pct, "eur": dca_eur})
    
    # Build final report
    report = {
        "generated_at": datetime.now().isoformat(),
        "report_version": "1.0",
        "data_source": "Colombia Staking BTC Strategy Engine",
        "source_signals_timestamp": signals.get("timestamp", "unknown"),
        
        "summary": {
            "score": score,
            "score_interpretation": score_interp["level"],
            "score_detail": score_interp["description"],
            "dca_recommendation": score_interp["dca_recommendation"],
            "regime": regime,
            "regime_title": regime_interp["title"],
            "regime_description": regime_interp["description"],
            "action": regime_interp["action"],
            "action_detail": regime_interp["action_detail"],
            "recommendation": recommendation,
        },
        
        "market_data": {
            "price": price,
            "price_formatted": f"${price:,.0f}" if price else "Unknown",
            "realized_price": realized_price,
            "realized_price_source": realized_source,
            "vs_realized_pct": vs_realized_pct,
            "vs_realized_label": vs_realized_label,
            "vs_realized_detail": f"BTC is trading {vs_realized_abs:.1f}% {vs_realized_label} realized price of ${realized_price:,.0f}"
        },
        
        "indicators": indicators_list,
        
        "signal_counts": {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count,
            "total": len(indicators_list)
        },
        
        "regime_guidance": regime_guidance,
        
        "dca_table": dca_table,
        
        "documentation": {
            "title": "Understanding the 11 Indicators",
            "description": "Each indicator provides a different perspective on Bitcoin's valuation and market position. Together they create a comprehensive picture.",
            "indicators": [
                {
                    "name": "MVRV Ratio",
                    "full_name": "Market Value to Realized Value",
                    "why": "Compares what the market is paying vs what holders actually paid. When MVRV < 1.0, the market is undervaluing BTC relative to historical holder behavior.",
                    "how_to_read": "Below 1.0 = buy zone. Above 2.5 = bubble zone"
                },
                {
                    "name": "RSI (Weekly)",
                    "full_name": "Relative Strength Index",
                    "why": "Measures momentum. Bitcoin's weekly RSI has been remarkably accurate at calling bottoms and tops.",
                    "how_to_read": "Below 40 = oversold. Above 70 = overbought"
                },
                {
                    "name": "Fear & Greed Index",
                    "full_name": "Crowd Sentiment Index",
                    "why": "Captures aggregate crowd behavior. Markets are driven by fear and greed. Extreme fear creates bottoms, extreme greed creates tops.",
                    "how_to_read": "Below 30 = fear (buy). Above 75 = greed (sell)"
                },
                {
                    "name": "50-Week MA Discount",
                    "full_name": "50-Week Moving Average Discount",
                    "why": "Shows how far BTC has fallen from its average price over the past year. Bigger discounts = better entry points.",
                    "how_to_read": "Below -20% = deep discount. Above +30% = premium"
                },
                {
                    "name": "ETF Flows",
                    "full_name": "Bitcoin ETF 7-Day Net Flow",
                    "why": "ETF flows show institutional money movement. Large inflows = smart money accumulating. Large outflows = institutions selling.",
                    "how_to_read": "Positive = institutions buying. Negative = institutions selling"
                },
                {
                    "name": "Pi Cycle",
                    "full_name": "Pi Cycle Indicator",
                    "why": "Uses long-term moving averages to identify cycle peaks and bottoms. When the fast MA crosses below slow MA = bear confirmed.",
                    "how_to_read": "Below 0 = bear. Above 100 = near cycle peak"
                },
                {
                    "name": "Cycle Position",
                    "full_name": "Days Since Halving",
                    "why": "Bitcoin follows 4-year cycles tied to halvings. Year 1-2 post-halving are historically the best performing.",
                    "how_to_read": "Day 0-730 = accumulation phase. Day 730-1095 = bull continuation. Day 1095+ = late cycle"
                },
                {
                    "name": "Stock-to-Flow",
                    "full_name": "BTC Stock-to-Flow Ratio",
                    "why": "Measures scarcity by comparing existing supply to new supply rate. Halvings increase scarcity dramatically.",
                    "how_to_read": "Higher = more scarce. Post-halving values > 100 show extreme scarcity"
                },
                {
                    "name": "Bollinger Position",
                    "full_name": "Bollinger Band Position",
                    "why": "Shows where price sits within the Bollinger Band range. Near lower band = support, near upper band = resistance.",
                    "how_to_read": "Below 20% = near support. Above 80% = near resistance"
                },
                {
                    "name": "MACD Histogram",
                    "full_name": "Moving Average Convergence Divergence",
                    "why": "Shows trend momentum. Positive histogram = buying pressure. Negative = selling pressure.",
                    "how_to_read": "Positive = bullish momentum. Negative = bearish momentum"
                },
                {
                    "name": "MVRV Z-Score",
                    "full_name": "MVRV Statistical Z-Score",
                    "why": "Statistical measure of how far MVRV deviates from normal. Accounts for Bitcoin's growth over time.",
                    "how_to_read": "Below -1 = undervalued. Above +7 = overvalued"
                }
            ]
        }
    }
    
    return report

def save_report(report):
    """Save report to cache file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(report, f, indent=2)

class ReportHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the BTC report."""
    
    def do_GET(self):
        # Normalize path (strip leading/trailing slashes, handle cloudflare stripping)
        path = self.path.rstrip('/')
        if path.startswith('/btc-report'):
            path = path.replace('/btc-report', '') or '/'
        
        if path in ['/', '', '/report', '/btc-report']:
            # Serve the full report
            try:
                with open(CACHE_FILE, 'r') as f:
                    report = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(report, indent=2).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif path in ['/summary', '/btc-report/summary']:
            # Serve just the summary (smaller payload for quick checks)
            # Auto-regenerate if signals file is newer than cache
            try:
                signals_mtime = os.path.getmtime(BTC_SIGNALS_FILE)
                cache_mtime = os.path.getmtime(CACHE_FILE)
                if signals_mtime > cache_mtime:
                    report = generate_report()
                    save_report(report)
                    print(f"[Auto-refresh] Score {report['summary']['score']}")
            except Exception as e:
                pass  # Fall through to serve cached version
            try:
                with open(CACHE_FILE, 'r') as f:
                    report = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(report.get("summary", {}), indent=2).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif path in ['/health', '/btc-report/health']:
            # Health check
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "btc-general-report"}).encode())
        else:
            # Unknown path - redirect to report
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            try:
                with open(CACHE_FILE, 'r') as f:
                    report = json.load(f)
                self.wfile.write(json.dumps(report, indent=2).encode())
            except:
                self.wfile.write(json.dumps({"error": "Report not available"}).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging

def run_server():
    """Run the HTTP server."""
    server = HTTPServer(('0.0.0.0', PORT), ReportHandler)
    print(f"BTC General Report Server running on port {PORT}")
    server.serve_forever()

def main():
    """Generate report and optionally start server."""
    import sys
    
    # Generate report
    print("Generating BTC General Report...")
    report = generate_report()
    
    if "error" in report:
        print(f"Error generating report: {report['error']}")
        return
    
    # Save to cache
    save_report(report)
    print(f"Report saved to {CACHE_FILE}")
    print(f"Summary: Score {report['summary']['score']} - {report['summary']['score_interpretation']}")
    print(f"Action: {report['summary']['action']}")
    print(f"Indicators: {report['signal_counts']['bullish']} bullish, {report['signal_counts']['neutral']} neutral, {report['signal_counts']['bearish']} bearish")
    
    # If run with 'serve' argument, start HTTP server
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        print("Starting HTTP server...")
        run_server()

if __name__ == "__main__":
    main()
