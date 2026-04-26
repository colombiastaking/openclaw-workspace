#!/usr/bin/env python3
"""
Daily Strategy Report - Professional Advisory with Deep Reflection
BTC Accumulation + Aave Position = Strategic Weekly Plan

v7.5: AI decides DCA/borrow/repay amounts + LTV 60% max
v7.2: Fixed INTRA_CYCLE_RALLY regime handling + v7.0 composite indicators
v7.1: Updated with Dune Analytics real on-chain realized price
v7.0: Strategic posture drives weekly strategy - deep reflection is the brain
"""

import json
import subprocess
import os
import requests
import re
from datetime import datetime
import openai

# Config - Load from environment variables (DO NOT commit secrets!)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1144365829")

# Professional Advisory Parameters
# Weekly DCA = 2% of Total Aave Position (Collateral + Borrowed)
# Capped at €1000/month max (Sebas's budget)
DCA_PERCENT_OF_POSITION = 0.02
MAX_MONTHLY_DCA_EUR = 1000

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def get_btc_signal():
    try:
        with open('/tmp/btc_decision_alert.json', 'r') as f:
            data = json.load(f)
        
        indicators = data.get('indicators', {})
        bull_market = data.get('bull_market', {})
        regime = data.get('regime', {})
        
        return {
            'score': data.get('score', 50),
            'recommendation': data.get('recommendation', 'NEUTRAL'),
            'mvrv': indicators.get('mvrv', 0),
            'realized_price': data.get('realized_price', 0),
            'realized_price_source': data.get('realized_price_source', 'ma_365_proxy'),
            'rsi': indicators.get('rsi', 0),
            'cycle_days': indicators.get('cycle_days', 0),
            'ma_discount': indicators.get('discount_50w_ma', 0),
            'price': data.get('price', 0),
            'cycle_phase': data.get('cycle_phase', ''),
            'fear_greed': indicators.get('fear_greed', 50),
            'pi_cycle': indicators.get('pi_cycle_diff', 0),
            's2f': indicators.get('s2f_value', 50),
            'etf_flow': indicators.get('etf_net_flow_7d', 0),
            'bull_stage': bull_market.get('stage', 0),
            'bull_action': bull_market.get('action', 'ACCUMULATION ZONE'),
            'bull_btc_sell_pct': bull_market.get('btc_to_sell_pct', 0),
            'bull_debt_pay_pct': bull_market.get('debt_to_pay_pct', 0),
            'bull_description': bull_market.get('description', 'All clear - Continue accumulation'),
            'intra_cycle_rally': indicators.get('intra_cycle_rally', False),
            # Regime data
            'regime_current': regime.get('current', 'UNKNOWN'),
            'regime_description': regime.get('description', ''),
            'dca_multiplier': regime.get('dca_multiplier', 1.0),
            'borrow_allowed': regime.get('borrow_allowed', True),
            'repay_urgency': regime.get('repay_urgency', 'low'),
            'profit_taking': regime.get('profit_taking', 'none'),
            'bull_signals': regime.get('bull_signals', 0),
            'bear_signals': regime.get('bear_signals', 0)
        }
    except:
        return {'score': 50, 'recommendation': 'NEUTRAL', 'bull_stage': 0, 'regime_current': 'UNKNOWN'}

def get_aave_position():
    output = run_command("cd /home/raspberry/.openclaw/workspace/aave-monitor && python3 btc_monitor.py")
    
    hf = 1.5
    collateral_btc = 0
    collateral_usd = 0
    debt_usd = 0
    liq_price = 0
    buffer_pct = 0
    btc_price = 69437
    
    for line in output.split('\n'):
        if 'Current HF:' in line or 'Current HF' in line:
            try:
                match = re.search(r'(\d+\.\d+)', line)
                if match:
                    hf = float(match.group(1))
            except:
                pass
        
        if 'Collateral:' in line and 'BTC' in line:
            try:
                collateral_btc = float(line.split('BTC')[0].split(':')[1].strip().split()[0])
            except:
                pass
        
        if 'Debt:' in line:
            try:
                parts = line.split('$')
                if len(parts) > 1:
                    debt_usd = float(parts[-1].replace(',','').strip())
            except:
                pass
        
        if 'HF 1.0' in line and 'DANGER' in line:
            try:
                liq_price = float(line.split('$')[-1].replace(',','').strip())
            except:
                pass
        
        if 'BTC Price:' in line:
            try:
                btc_price = float(line.split('$')[1].replace(',','').strip())
            except:
                pass
    
    collateral_usd = collateral_btc * btc_price
    
    if btc_price > 0 and liq_price > 0:
        buffer_pct = ((btc_price - liq_price) / btc_price) * 100
    
    ltv = (debt_usd / collateral_usd * 100) if collateral_usd > 0 else 0
    max_borrow_at_50 = (collateral_usd * 0.5) - debt_usd
    
    return {
        'health_factor': hf,
        'collateral_btc': collateral_btc,
        'collateral_usd': collateral_usd,
        'debt_usd': debt_usd,
        'liq_price': liq_price,
        'buffer_pct': buffer_pct,
        'ltv': ltv,
        'btc_price': btc_price,
        'max_borrow_at_50': max_borrow_at_50 if max_borrow_at_50 > 0 else 0
    }

def generate_deep_reflection(btc, aave, strategy):
    """
    Generate deep analytical reflection based on current market conditions
    This is the "professional advisor" thinking - not just numbers
    """
    score = btc.get('score', 50)
    mvrv = btc.get('mvrv', 1)
    rsi = btc.get('rsi', 50)
    ma_disc = btc.get('ma_discount', 0)
    cycle_days = btc.get('cycle_days', 0)
    fear_greed = btc.get('fear_greed', 50)
    pi_cycle = btc.get('pi_cycle', 0)
    bull_stage = btc.get('bull_stage', 0)
    bull_action = btc.get('bull_action', 'ACCUMULATION ZONE')
    bull_btc_pct = btc.get('bull_btc_sell_pct', 0)
    bull_debt_pct = btc.get('bull_debt_pay_pct', 0)
    intra_cycle_rally = btc.get('intra_cycle_rally', False)
    
    hf = aave.get('health_factor', 1.5)
    ltv = aave.get('ltv', 0)
    buffer = aave.get('buffer_pct', 0)
    collateral = aave.get('collateral_usd', 0)
    btc_price = aave.get('btc_price', 0)
    
    # Deep analysis
    reflection = []
    
    # 1. Market Cycle Analysis
    if score <= 30:
        reflection.append("📍 **MARKET CYCLE**: We're in a deep accumulation zone. The last 3 times the score was this low (2018, 2022 bear markets), BTC rallied 3-5x within 2-3 years. This is historically the highest-conviction buying environment.")
    elif score <= 45:
        reflection.append("📍 **MARKET CYCLE**: Good accumulation territory. Not as extreme as the deep bear zones, but still presenting strong value for long-term investors.")
    else:
        reflection.append("📍 **MARKET CYCLE**: We're in neutral/expensive territory. This isn't the time for aggressive DCA - patience may be rewarded with better entry points.")
    
    # 2. Valuation Analysis
    if mvrv < 0.8:
        reflection.append("📊 **VALUATION**: MVRV at {:.2f} - BTC is significantly below what holders paid on average. This historically marks major bottoms.".format(mvrv))
    elif mvrv > 1.5:
        reflection.append("📊 **VALUATION**: MVRV at {:.2f} - We're in premium territory. Future returns likely to be modest from here.".format(mvrv))
    
    # 3. Technical Analysis
    if rsi < 35:
        reflection.append("📈 **TECHNICAL**: RSI at {} on weekly - oversold. Momentum is turning negative which typically marks capitulation and new accumulation starts.".format(rsi))
    elif rsi > 65:
        reflection.append("📈 **TECHNICAL**: RSI at {} - overbought. This has historically preceded corrections.".format(rsi))
    
    # 4. Cycle Position
    if 600 <= cycle_days <= 750:
        reflection.append("⏰ **CYCLE TIMING**: Day {} post-halving - we're in the traditional bear market accumulation window. Historically, this is when institutions accumulate quietly.".format(cycle_days))
    elif cycle_days < 180:
        reflection.append("⏰ **CYCLE TIMING**: Early cycle - typically not the best time for heavy accumulation as you're paying a premium.")
    
    # 5. Aave Position Strategy
    if hf >= 1.8 and ltv < 60:
        reflection.append("💰 **YOUR POSITION**: HF {:.2f} and LTV {:.1f}% - strong health. You have optionality: either maintain for long-term or strategically leverage during this accumulation zone.".format(hf, ltv))
    elif hf < 1.3:
        reflection.append("💰 **YOUR POSITION**: HF {:.2f} is concerning. Priority this week is debt reduction, not DCA. Your buffer is too thin for this cycle.".format(hf))
    else:
        reflection.append("💰 **YOUR POSITION**: HF {:.2f} is healthy but monitor closely. You're positioned well for this market phase.".format(hf))
    
    # 6. Risk Assessment
    if buffer > 30:
        reflection.append("🛡️ **RISK**: Buffer of {:.1f}% above liquidation - comfortable safety margin. You're insulated from normal volatility.".format(buffer))
    elif buffer < 15:
        reflection.append("🛡️ **RISK**: Buffer of {:.1f}% is thin. Any significant BTC drop puts you at risk. Consider reducing debt.".format(buffer))
    
    # 7. Intra-Cycle Rally Warning
    intra_cycle = btc.get('intra_cycle_rally', False)
    if intra_cycle:
        reflection.append("⚠️ **INTRA-CYCLE RALLY WARNING**: MACD shows positive momentum BUT RSI is oversold AND price is >20% below 50W MA. This is a relief rally WITHIN the bear market, NOT a new bull market. Do NOT increase leverage. Continue systematic DCA.")
    
    # 8. Bull Market Profit-Taking Analysis
    if bull_stage > 0:
        if bull_stage == 1:
            reflection.append("🐂 **BULL MARKET**: Early bubble detected - Score {} + MVRV {}. Stop DCA and monitor for profit-taking triggers.".format(score, mvrv))
        elif bull_stage == 2:
            reflection.append("🐂 **BULL MARKET**: BUBBLE ZONE - Score {} + MVRV {}. Consider selling {}% of BTC, using {}% to pay debt.".format(score, mvrv, bull_btc_pct, bull_debt_pct))
        elif bull_stage == 3:
            reflection.append("🐂 **BULL MARKET**: HOT BUBBLE - Score {} + MVRV {}. Serious profit-taking: sell {}% of BTC, use {}% to aggressively pay debt.".format(score, mvrv, bull_btc_pct, bull_debt_pct))
        elif bull_stage == 4:
            reflection.append("🐂 **BULL MARKET**: EXTREME BUBBLE - Score {} + MVRV {}. MAXIMUM PROFIT-TAKING: sell {}% of BTC, pay off ALL debt.".format(score, mvrv, bull_btc_pct))
    else:
        reflection.append("🐂 **BULL MARKET**: All clear - Continue accumulation strategy. No profit-taking signals active.")
    
    # 9. Position Progress Tracking
    btc_holdings = collateral / btc_price if btc_price > 0 else 0
    dca_eur = strategy.get('dca_amount_eur', 0)
    # Goal: Car ~0.35-0.5 BTC, Projects ~0.7-1 BTC, Real Estate ~1-2 BTC
    car_target = 0.4  # BTC
    projects_target = 0.85  # BTC
    real_estate_target = 1.5  # BTC
    
    reflection.append("📊 **PROGRESS**: You hold {:.4f} BTC (${:,.0f})".format(btc_holdings, collateral))
    if dca_eur > 0:
        weekly_sats = (dca_eur / btc_price * 100000000) if btc_price > 0 else 0
        if btc_holdings < car_target:
            weeks_to_car = ((car_target - btc_holdings) * 100000000 / weekly_sats) if weekly_sats > 0 else float('inf')
            reflection.append("   → Car goal ({:.1f} BTC): {:.0f} weeks at current DCA".format(car_target, weeks_to_car))
        elif btc_holdings < projects_target:
            weeks_to_projects = ((projects_target - btc_holdings) * 100000000 / weekly_sats) if weekly_sats > 0 else float('inf')
            reflection.append("   → Car goal ACHIEVED! 🎉 Projects target ({:.1f} BTC): {:.0f} weeks to go".format(projects_target, weeks_to_projects))
    elif btc_holdings >= projects_target:
        reflection.append("   → Projects goal ACHIEVED! 🎉 Real estate ({:.1f} BTC) next".format(real_estate_target))
    
    # 10. The Big Picture
    if score <= 30 and hf >= 1.5:
        reflection.append("🎯 **STRATEGIC VIEW**: This is a generational buying opportunity. You're in the perfect position: healthy Aave health + deep BTC discount. The professionals are loading up right now.")
    elif score > 50 and hf < 1.3:
        reflection.append("🎯 **STRATEGIC VIEW**: Not ideal - expensive BTC + stressed position. Focus on deleveraging while BTC is at a premium.")
    
    return reflection

# ==========================================
# AI DECISION FUNCTION - Let AI decide € amounts
# ==========================================

def ai_decide_amounts(score, regime, hf, ltv, buffer, debt, collateral, btc_price, 
                       mvrv, rsi, fear_greed, days_since, max_borrow_at_60):
    """
    Ask AI to decide DCA, borrow, and repay amounts based on full context.
    Replaces hardcoded multipliers with AI judgment.
    """
    import openai
    
    prompt = f"""You are a BTC investment strategy advisor. Decide the weekly € amounts for DCA, borrow, and repay based on:

MARKET DATA:
- BTC Score: {score}/100 (0=extreme fear/deep bear, 100=extreme greed/bull)
- Regime: {regime}
- MVRV: {mvrv:.2f} (<1 = undervalued, >2 = overvalued)
- RSI: {rsi:.1f} (<40 oversold, >70 overbought)
- Fear & Greed: {fear_greed} (0-100)
- Days post-halving: {days_since}
- BTC Price: ${btc_price:,.0f}

AAVE POSITION:
- Health Factor: {hf:.2f} (>2.0 healthy, <1.0 liquidation)
- LTV: {ltv:.1f}% (max 60%)
- Buffer: {buffer:.1f}%
- Debt: ${debt:,.0f} USDC
- Collateral: ${collateral:,.0f} ({collateral/btc_price:.6f} BTC)
- Max borrowable (at 60% LTV): ${max_borrow_at_60:,.0f}

USER CONTEXT:
- Budget: €1,000/month max (€250/week base)
- Risk: Conservative, HF target >2.0, LTV max 60%
- Goals: Car €20K, Projects €30-50K, Real Estate €50-100K
- Time Horizon: 5+ years

DECISION RULES:
- DCA: €0-375 range based on score and HF
- Borrow: Only if HF >1.5, LTV <60%, buffer >25%, accumulation posture
- Repay: Based on HF (<1.3 urgent, 1.3-1.5 moderate, >1.5 optional)
- Max monthly toward Aave: €500

Respond ONLY with JSON:
{{"dca_eur": NUMBER, "borrow_eur": NUMBER, "repay_eur": NUMBER, "reasoning": "2 sentences"}}
"""
    
    try:
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            return None  # No API key, use strategic posture logic
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        result = response.choices[0].message.content.strip()
        import json
        return json.loads(result)
    except Exception as e:
        return None  # AI failed, use strategic posture logic

def calculate_professional_strategy(btc, aave):
    """
    Calculate strategy using the same AI-style reasoning as deep reflection.
    The deep analysis drives the final recommendations - not mechanical rules.
    """
    score = btc.get('score', 50)
    mvrv = btc.get('mvrv', 1)
    rsi = btc.get('rsi', 50)
    ma_disc = btc.get('ma_discount', 0)
    cycle_days = btc.get('cycle_days', 0)
    fear_greed = btc.get('fear_greed', 50)
    
    hf = aave.get('health_factor', 1.5)
    ltv = aave.get('ltv', 0)
    buffer = aave.get('buffer_pct', 0)
    debt = aave.get('debt_usd', 0)
    collateral = aave.get('collateral_usd', 0)
    max_borrow = aave.get('max_borrow_at_50', 0)
    btc_price = aave.get('btc_price', 0)
    
    bull_stage = btc.get('bull_stage', 0)
    bull_action = btc.get('bull_action', 'ACCUMULATION ZONE')
    bull_btc_pct = btc.get('bull_btc_sell_pct', 0)
    bull_debt_pct = btc.get('bull_debt_pay_pct', 0)
    
    total_position = collateral + debt
    base_dca_eur = 250  # Weekly budget
    
    # ==========================================
    # STEP 1: Determine overall strategic posture
    # This is where the "advisor judgment" happens
    # ==========================================
    
    strategic_posture = "NEUTRAL"
    posture_reason = ""
    
    # BULL MARKET OVERRIDES EVERYTHING
    if bull_stage >= 4:
        strategic_posture = "MAXIMUM_PROFIT-TAKING"
        posture_reason = f"☠️ EXTREME BUBBLE - Score {score}, MVRV {mvrv}. Take maximum profits now."
    elif bull_stage == 3:
        strategic_posture = "SERIOUS_PROFIT-TAKING"
        posture_reason = f"🚨 HOT BUBBLE - Score {score}, MVRV {mvrv}. Serious deleveraging time."
    elif bull_stage == 2:
        strategic_posture = "PROFIT-TAKING"
        posture_reason = f"🔴 BUBBLE ZONE - Score {score}, MVRV {mvrv}. Start taking profits."
    elif bull_stage == 1:
        strategic_posture = "STOP_ACCUMULATION"
        posture_reason = f"🟠 EARLY BUBBLE - Score {score}, MVRV {mvrv}. Stop DCA, monitor closely."
    
    # DEEP BEAR / GENERATIONAL OPPORTUNITY
    elif score <= 25 and hf >= 1.5:
        strategic_posture = "MAXIMUM_ACCUMULATION"
        posture_reason = "🟢 GENERATIONAL OPPORTUNITY - Deep bear + healthy position. Maximum DCA."
    elif score <= 35 and hf >= 1.5:
        strategic_posture = "STRONG_ACCUMULATION"
        posture_reason = "🟢 Strong accumulation zone. High conviction buy."
    
    # HEALTH FACTOR CONCERNS OVERRIDE DCA
    elif hf < 1.3:
        strategic_posture = "DELEVERAGE_URGENT"
        posture_reason = f"🔴 DANGER - HF {hf:.2f} is critically low. Deleverage first."
    elif hf < 1.5:
        strategic_posture = "DELEVERAGE"
        posture_reason = f"⚠️ HF {hf:.2f} is thin. Prioritize debt reduction."
    
    # EXPENSIVE BTC + STRESSED POSITION
    elif score > 50 and hf < 1.3:
        strategic_posture = "DELEVERAGE"
        posture_reason = "Not ideal: expensive BTC + stressed position. Focus on deleveraging."
    
    # INTRA-CYCLE RALLY (Bear market bounce - NOT new bull)
    elif btc.get('regime_current') == 'INTRA_CYCLE_RALLY':
        if hf >= 1.8 and ltv < 60:
            strategic_posture = "INTRA_CYCLE_RALLY_NORMAL"
            posture_reason = "🟡 INTRA-CYCLE RALLY - Bear bounce. Accumulation OK but don't increase leverage."
        else:
            strategic_posture = "INTRA_CYCLE_RALLY_CAUTION"
            posture_reason = "⚠️ Rally but HF/LTV needs monitoring. Stay conservative."
    
    # NORMAL NEUTRAL
    elif score <= 50:
        strategic_posture = "ACCUMULATION"
        posture_reason = "Accumulation zone - add to position."
    else:
        strategic_posture = "NEUTRAL"
        posture_reason = "Neutral zone - hold, wait for better entry."
    
    # ==========================================
    # STEP 2: Apply strategic posture to DCA decision
    # ==========================================
    
    if strategic_posture in ["MAXIMUM_PROFIT-TAKING", "SERIOUS_PROFIT-TAKING", "PROFIT-TAKING", "STOP_ACCUMULATION"]:
        # In bull market territory - no DCA
        dca_action = "❌ STOP DCA"
        dca_amount_eur = 0
        dca_btc = 0
        dca_sats = 0
        dca_reason = f"Bull market stage {bull_stage}: {bull_action}"
        
    elif strategic_posture == "MAXIMUM_ACCUMULATION":
        # Deep bear - maximum DCA (150%)
        dca_action = "🟢 MAXIMUM DCA (150%)"
        dca_amount_eur = base_dca_eur * 1.5
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = posture_reason
        
    elif strategic_posture == "STRONG_ACCUMULATION":
        # Strong buy zone - 125%
        dca_action = "🟢 STRONG DCA (125%)"
        dca_amount_eur = base_dca_eur * 1.25
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = posture_reason
        
    elif strategic_posture == "DELEVERAGE_URGENT":
        # HF < 1.3 - no DCA, pay debt
        dca_action = "❌ NO DCA - DELEVERAGE"
        dca_amount_eur = 0
        dca_btc = 0
        dca_sats = 0
        dca_reason = "HF too low - debt reduction is priority"
        
    elif strategic_posture == "DELEVERAGE":
        # HF < 1.5 - reduce DCA, focus on repay
        dca_action = "⚠️ REDUCE DCA (50%)"
        dca_amount_eur = base_dca_eur * 0.5
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = "HF needs attention - split between repay and small DCA"
    
    elif strategic_posture in ["INTRA_CYCLE_RALLY_NORMAL", "INTRA_CYCLE_RALLY_CAUTION"]:
        # Bear market bounce - DCA OK but be conservative
        dca_action = "🟡 MODERATE DCA (75%)"
        dca_amount_eur = base_dca_eur * 0.75
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = "Bear market bounce - don't overcommit, keep dry powder"
        
    elif strategic_posture == "ACCUMULATION":
        # Normal accumulation - 100%
        dca_action = "🟢 NORMAL DCA (100%)"
        dca_amount_eur = base_dca_eur
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = posture_reason
        
    else:
        # Neutral - 75%
        dca_action = "🟡 REDUCED DCA (75%)"
        dca_amount_eur = base_dca_eur * 0.75
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000
        dca_reason = posture_reason
    
    # ==========================================
    # STEP 3: Borrow decision (based on posture + conditions)
    # ==========================================
    
    if strategic_posture in ["MAXIMUM_PROFIT-TAKING", "SERIOUS_PROFIT-TAKING", "PROFIT-TAKING", "DELEVERAGE_URGENT", "DELEVERAGE"]:
        borrow_action = "❌ NO BORROW - Deleverage mode"
        borrow_amount_eur = 0
        borrow_reason = "Position management takes priority"
    elif hf < 1.5:
        borrow_action = "❌ NO BORROW - HF too low"
        borrow_amount_eur = 0
        borrow_reason = "Build HF buffer first"
    elif ltv > 60:
        borrow_action = "❌ NO BORROW - LTV too high"
        borrow_amount_eur = 0
        borrow_reason = f"LTV at {ltv:.1f}% - reduce first"
    elif buffer < 25:
        borrow_action = "⚠️ CAUTION - Buffer thin"
        borrow_amount_eur = 0
        borrow_reason = f"Buffer only {buffer:.1f}% - build safety first"
    elif strategic_posture in ["MAXIMUM_ACCUMULATION", "STRONG_ACCUMULATION"] and max_borrow > 500:
        borrow_action = f"✅ YES - €{min(max_borrow, 500):,.0f} available"
        borrow_amount_eur = min(max_borrow, 500)
        borrow_reason = "Strong accumulation zone - leverage opportunity"
    else:
        borrow_action = "❌ NOT OPTIMAL"
        borrow_amount_eur = 0
        borrow_reason = "Wait for better conditions"
    
    # ==========================================
    # STEP 4: Repay decision (based on HF)
    # ==========================================
    
    if strategic_posture in ["MAXIMUM_PROFIT-TAKING", "SERIOUS_PROFIT-TAKING"]:
        # In bubble - use profits to pay debt
        repay_action = f"✅ YES - Use profits to pay debt"
        repay_amount_eur = min(bull_btc_pct * btc_price * 0.01 * bull_debt_pct / 100, debt)
        repay_reason = f"Sell {bull_btc_pct}% BTC → {bull_debt_pct}% to debt"
    elif hf >= 2.0:
        repay_action = "FOCUS ON DCA - position healthy"
        repay_amount_eur = 0
        repay_reason = "HF above 2.0 - maintain position"
    elif hf >= 1.6:
        repay_action = f"OPTIONAL - €{min(150, debt * 0.05):,.0f}"
        repay_amount_eur = min(150, debt * 0.05)
        repay_reason = "Modest HF buffer - optional repay"
    elif hf >= 1.3:
        repay_action = f"RECOMMENDED - €{min(300, debt * 0.10):,.0f}"
        repay_amount_eur = min(300, debt * 0.10)
        repay_reason = "HF needs improvement - prioritize repay"
    else:
        repay_action = f"URGENT - €{min(500, debt * 0.20):,.0f} ASAP"
        repay_amount_eur = min(500, debt * 0.20)
        repay_reason = "Critical - HF dangerously low"
    
    # ==========================================
    # STEP 5: BTC for debt (de-risk decision)
    # ==========================================
    
    if strategic_posture in ["MAXIMUM_PROFIT-TAKING", "SERIOUS_PROFIT-TAKING", "PROFIT-TAKING"]:
        btc_deleverage = f"✅ YES - Sell {bull_btc_pct}% BTC to reduce debt"
        btc_deleverage_reason = f"Bull market stage {bull_stage}: {bull_action}"
    elif ltv > 60:
        btc_deleverage = "⚠️ YES - Consider using BTC to reduce debt"
        btc_deleverage_reason = f"LTV at {ltv:.1f}% is high"
    elif hf < 1.3:
        btc_deleverage = "⚠️ YES - BTC deleverage recommended"
        btc_deleverage_reason = "HF critically low"
    else:
        btc_deleverage = "❌ NO - Keep BTC for long-term"
        btc_deleverage_reason = "Position is healthy"
    
    # ==========================================
    # AI DECISION ENGINE - Let AI decide € amounts
    # Replaces hardcoded multipliers with AI judgment
    # ==========================================
    
    # Get max borrow at 60% LTV
    max_borrow_at_60 = (collateral * 0.60) - debt if collateral > 0 else 0
    
    # AI Decision - Only override if AI returns valid decision
    # Otherwise keep strategic posture amounts (already calculated above)
    ai_decision = ai_decide_amounts(
        score=score,
        regime=btc.get('regime_current', 'UNKNOWN'),
        hf=hf,
        ltv=ltv,
        buffer=buffer,
        debt=debt,
        collateral=collateral,
        btc_price=btc_price,
        mvrv=btc.get('mvrv', 0),
        rsi=btc.get('rsi', 50),
        fear_greed=btc.get('fear_greed', 50),
        days_since=btc.get('days_since_halving', 0),
        max_borrow_at_60=max_borrow_at_60
    )
    
    if ai_decision:
        # Override amounts with AI decision
        dca_amount_eur = ai_decision.get('dca_eur', dca_amount_eur)
        dca_btc = dca_amount_eur / btc_price if btc_price > 0 else 0
        dca_sats = dca_btc * 100000000 if dca_btc > 0 else 0
        dca_action = f"🤖 AI DCA: €{dca_amount_eur:.0f}"
        dca_reason = ai_decision.get('reasoning', 'AI decision')
        
        borrow_amount_eur = ai_decision.get('borrow_eur', 0)
        if borrow_amount_eur > 0:
            borrow_action = f"✅ YES - €{borrow_amount_eur:.0f}"
            borrow_reason = ai_decision.get('reasoning', 'AI decision')
        else:
            borrow_action = f"❌ NO BORROW"
            borrow_reason = ai_decision.get('reasoning', 'AI decision')
        
        repay_amount_eur = ai_decision.get('repay_eur', 0)
        if repay_amount_eur > 0:
            repay_action = f"✅ YES - €{repay_amount_eur:.0f}"
            repay_reason = ai_decision.get('reasoning', 'AI decision')
        else:
            repay_action = f"❌ NO REPAY"
            repay_reason = ai_decision.get('reasoning', 'AI decision')
    else:
        # Keep strategic posture amounts (already calculated above)
        dca_action = f"{dca_action} (Strategic Posture)"
        dca_reason = f"{dca_reason}"
    
    return {
        'strategic_posture': strategic_posture,
        'posture_reason': posture_reason,
        
        'dca_action': dca_action,
        'dca_amount_eur': dca_amount_eur,
        'dca_btc': dca_btc,
        'dca_sats': dca_sats,
        'dca_reason': dca_reason,
        
        'borrow_action': borrow_action,
        'borrow_amount_eur': borrow_amount_eur,
        'borrow_reason': borrow_reason,
        
        'repay_action': repay_action,
        'repay_amount_eur': repay_amount_eur,
        'repay_reason': repay_reason,
        
        'btc_deleverage': btc_deleverage,
        'btc_deleverage_reason': btc_deleverage_reason,
        
        'bull_stage': bull_stage,
        'bull_action': bull_action,
        'bull_btc_pct': bull_btc_pct,
        'bull_debt_pct': bull_debt_pct,
        
        'current_ltv': ltv,
        'current_hf': hf,
        'total_position': total_position
    }

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=data, timeout=10)

def main():
    # Fetch data
    run_command("cd /home/raspberry/.openclaw/workspace/btc-monitor && python3 btc_decision_engine.py > /dev/null 2>&1")
    btc = get_btc_signal()
    aave = get_aave_position()
    strategy = calculate_professional_strategy(btc, aave)
    reflection = generate_deep_reflection(btc, aave, strategy)
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Build comprehensive report
    score = btc.get('score', 50)
    rec = btc.get('recommendation', 'NEUTRAL')
    mvrv = btc.get('mvrv', 0)
    rsi = btc.get('rsi', 0)
    cycle = btc.get('cycle_days', 0)
    ma_disc = abs(btc.get('ma_discount', 0))
    
    hf = aave.get('health_factor', 0)
    collat = aave.get('collateral_usd', 0)
    debt = aave.get('debt_usd', 0)
    buffer = aave.get('buffer_pct', 0)
    liq = aave.get('liq_price', 0)
    ltv = aave.get('ltv', 0)
    
    # Bull market signals
    bull_stage = btc.get('bull_stage', 0)
    bull_action = btc.get('bull_action', 'ACCUMULATION ZONE')
    bull_btc_pct = btc.get('bull_btc_sell_pct', 0)
    bull_debt_pct = btc.get('bull_debt_pay_pct', 0)
    bull_desc = btc.get('bull_description', 'All clear - Continue accumulation')
    
    # Build the message with deep reflection
    message = f"""📊 **{current_date} - WEEKLY STRATEGY**
═══════════════════════════════════════

🎯 *ACCUMULATION SCORE: {score}/100* ({rec})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *MARKET SNAPSHOT*
   BTC: ${btc.get('price', 0):,.0f}
   MVRV: {mvrv} (Realized: ${btc.get('realized_price', 0):,.0f} [{btc.get('realized_price_source', 'unknown')}])
   RSI: {rsi} | 50W MA: -{ma_disc}%
   Cycle: Day {cycle} | Fear&Greed: {btc.get('fear_greed', 50)}

💰 *YOUR POSITION*
   Collateral: ${collat:,.0f} | Debt: ${debt:,.0f}
   HF: {hf} | LTV: {ltv:.1f}% | Buffer: {buffer:.1f}%
   Total Aave: ${strategy['total_position']:,.0f}

🐂 *BULL MARKET SIGNALS*
   Stage: {bull_stage}/4
   Action: {bull_action}
   {bull_desc}"""

    if bull_stage > 0:
        message += f"\n   💡 Sell {bull_btc_pct}% BTC → {bull_debt_pct}% to debt"
    
    message += """

═══════════════════════════════════════
🧠 *DEEP REFLECTION*
══════════════════════════════════════="""

    # Add deep reflections line by line
    for ref in reflection:
        message += f"\n{ref}"

    message += f"""

═══════════════════════════════════════
🔄 *MARKET REGIME* (AUTO-DETECTED)
═══════════════════════════════════════
📍 {btc.get('regime_current', 'UNKNOWN').replace('_', ' ')}
   {btc.get('regime_description', '')[:80]}

📊 Signals: 🟢 {btc.get('bull_signals', 0)} Bull | 🔴 {btc.get('bear_signals', 0)} Bear

💰 DCA Multiplier: {btc.get('dca_multiplier', 1.0)}x
💳 Borrow: {'✅ Yes' if btc.get('borrow_allowed', True) else '❌ No'}
📉 Repay: {btc.get('repay_urgency', 'low').upper()}
💵 Profit Taking: {btc.get('profit_taking', 'none')}

═══════════════════════════════════════
📋 *THIS WEEK'S STRATEGY*
═══════════════════════════════════════

🎯 *STRATEGIC POSTURE*: {strategy['strategic_posture'].replace('_', ' ')}
   → {strategy['posture_reason']}

💵 *DCA*: {strategy['dca_action']}
   → €{strategy['dca_amount_eur']:,.0f}/week ({strategy['dca_btc']:.4f} BTC)
   → {strategy['dca_reason']}

🏦 *BORROW*: {strategy['borrow_action']}
   → {strategy['borrow_reason']}

💳 *REPAY*: {strategy['repay_action']}
   → €{strategy['repay_amount_eur']:,.0f} this week
   → {strategy['repay_reason']}

₿ *DE-RISK*: {strategy['btc_deleverage']}
   → {strategy['btc_deleverage_reason']}

═══════════════════════════════════════

Next deep reflection: Tomorrow 🎀"""

    send_telegram(message)
    print("✅ Deep strategy report sent!")
    
    # Save locally first
    report_date = datetime.now().strftime('%Y-%m-%d')
    with open(f"/home/raspberry/.openclaw/workspace/btc-strategy/reports/daily/{report_date}.md", 'w') as f:
        f.write(message)
    
    # Auto-commit and push to GitHub for backup
    try:
        import subprocess
        repo_path = "/home/raspberry/.openclaw/workspace/btc-strategy"
        
        # Git add, commit, push
        subprocess.run(["git", "-C", repo_path, "add", "."], capture_output=True)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", f"Daily report - {report_date}"], capture_output=True)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], capture_output=True, timeout=30)
        print("✅ GitHub backup complete!")
    except Exception as e:
        print(f"⚠️ GitHub backup failed: {e}")

if __name__ == "__main__":
    main()

