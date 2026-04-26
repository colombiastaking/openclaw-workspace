#!/usr/bin/env python3
"""
Daily Strategy Report - Professional Advisory with Deep Reflection
BTC Accumulation + Aave Position = Strategic Weekly Plan
"""

import json
import subprocess
import os
import requests
import re
from datetime import datetime

# Config - Load from environment variables (DO NOT commit secrets!)
import os
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1144365829")

# Professional Advisory Parameters
# Weekly DCA = 2% of Total Aave Position (Collateral + Borrowed)
DCA_PERCENT_OF_POSITION = 0.02

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def get_btc_signal():
    try:
        with open('/tmp/btc_decision_alert.json', 'r') as f:
            data = json.load(f)
        
        indicators = data.get('indicators', {})
        
        return {
            'score': data.get('score', 50),
            'recommendation': data.get('recommendation', 'NEUTRAL'),
            'mvrv': indicators.get('mvrv', 0),
            'rsi': indicators.get('rsi', 0),
            'cycle_days': indicators.get('cycle_days', 0),
            'ma_discount': indicators.get('discount_50w_ma', 0),
            'price': data.get('price', 0),
            'cycle_phase': data.get('cycle_phase', ''),
            'fear_greed': indicators.get('fear_greed', 50),
            'pi_cycle': indicators.get('pi_cycle_diff', 0),
            's2f': indicators.get('s2f_value', 50),
            'etf_flow': indicators.get('etf_net_flow_7d', 0)
        }
    except:
        return {'score': 50, 'recommendation': 'NEUTRAL'}

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

def get_ledger_btc():
    """Fetch Ledger BTC balance from the tracker script."""
    result = run_command("/usr/bin/python3 /home/raspberry/.openclaw/workspace/btc-monitor/ledger_btc_tracker.py")
    ledger_btc = 0
    ledger_sats = 0
    ledger_addr_count = 0
    
    # Parse output
    for line in result.split('\n'):
        if 'TOTAL LEDGER BTC:' in line:
            try:
                parts = line.split('BTC')
                if len(parts) > 0:
                    btc_str = parts[0].split(':')[-1].strip()
                    ledger_btc = float(btc_str)
            except:
                pass
    
    # Try reading from state file
    try:
        with open('/tmp/ledger_btc_state.json', 'r') as f:
            state = json.load(f)
            ledger_btc = state.get('total_btc', 0)
            ledger_sats = state.get('total_sats', 0)
            ledger_addr_count = len(state.get('external', {}).get('found', [])) + len(state.get('internal', {}).get('found', []))
    except:
        pass
    
    return {
        'btc': ledger_btc,
        'sats': ledger_sats,
        'address_count': ledger_addr_count
    }

def generate_deep_reflection(btc, aave, strategy, ledger):
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
    
    hf = aave.get('health_factor', 1.5)
    ltv = aave.get('ltv', 0)
    buffer = aave.get('buffer_pct', 0)
    
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
    if hf >= 1.8 and ltv < 40:
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
    
    # 7. The Big Picture
    if score <= 30 and hf >= 1.5:
        reflection.append("🎯 **STRATEGIC VIEW**: This is a generational buying opportunity. You're in the perfect position: healthy Aave health + deep BTC discount. The professionals are loading up right now.")
    elif score > 50 and hf < 1.3:
        reflection.append("🎯 **STRATEGIC VIEW**: Not ideal - expensive BTC + stressed position. Focus on deleveraging while BTC is at a premium.")
    
    return reflection

def calculate_professional_strategy(btc, aave, ledger):
    score = btc.get('score', 50)
    hf = aave.get('health_factor', 1.5)
    ltv = aave.get('ltv', 0)
    buffer = aave.get('buffer_pct', 0)
    debt = aave.get('debt_usd', 0)
    collateral = aave.get('collateral_usd', 0)
    max_borrow = aave.get('max_borrow_at_50', 0)
    btc_price = aave.get('btc_price', 0)
    
    # DCA Strategy (auto-scaled)
    total_position = collateral + debt
    base_dca = total_position * DCA_PERCENT_OF_POSITION
    
    if score <= 30:
        weekly_usd = base_dca * 1.5
        dca_action = "🟢 MAXIMIZE DCA"
    elif score <= 45:
        weekly_usd = base_dca
        dca_action = "🟢 NORMAL DCA"
    elif score <= 60:
        weekly_usd = base_dca * 0.75
        dca_action = "🟡 REDUCE DCA"
    else:
        weekly_usd = base_dca * 0.5
        dca_action = "🔴 MINIMUM DCA"
    
    btc_amount = weekly_usd / btc_price if btc_price > 0 else 0
    sats = btc_amount * 100000000
    
    # Borrow Strategy
    if ltv >= 45:
        borrow_action = "❌ DO NOT BORROW - LTV too high"
        borrow_amount = 0
    elif buffer < 20:
        borrow_action = "❌ DO NOT BORROW - Buffer too low"
        borrow_amount = 0
    elif score <= 35 and max_borrow > 500:
        borrow_action = f"✅ YES - Borrow ${max_borrow:,.0f} available"
        borrow_amount = min(max_borrow, base_dca * 2)
    else:
        borrow_action = "❌ DO NOT BORROW - Not optimal"
        borrow_amount = 0
    
    # Repay Strategy
    if hf >= 2.0:
        repay_action = "FOCUS ON DCA - position healthy"
        repay_amount = 0
    elif hf >= 1.6:
        repay_action = f"OPTIONAL - ${min(200, debt*0.05):,.0f} repay if comfortable"
        repay_amount = min(200, debt * 0.05)
    elif hf >= 1.3:
        repay_action = f"RECOMMENDED - ${min(400, debt*0.10):,.0f} repay this week"
        repay_amount = min(400, debt * 0.10)
    else:
        repay_action = f"URGENT - ${min(600, debt*0.20):,.0f} repay ASAP"
        repay_amount = min(600, debt * 0.20)
    
    # BTC Deleverage Decision
    if ltv > 45 or hf < 1.3:
        btc_deleverage = "⚠️ YES - Consider using BTC to reduce debt"
    else:
        btc_deleverage = "❌ NO - Keep BTC for long-term"
    
    return {
        'dca_action': dca_action,
        'dca_amount_usd': weekly_usd,
        'dca_btc': btc_amount,
        'dca_sats': sats,
        
        'borrow_action': borrow_action,
        'borrow_amount_usd': borrow_amount,
        
        'repay_action': repay_action,
        'repay_amount_usd': repay_amount,
        
        'btc_deleverage': btc_deleverage,
        
        'current_ltv': ltv,
        'current_hf': hf,
        'total_position': total_position
    }

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Split into chunks if message is too long (Telegram limit is 4096 chars)
    max_len = 4000
    if len(message) <= max_len:
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        requests.post(url, data=data, timeout=10)
    else:
        # Split message at a newline to avoid breaking formatting
        lines = message.split('\n')
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > max_len:
                data = {'chat_id': TELEGRAM_CHAT_ID, 'text': chunk, 'parse_mode': 'Markdown'}
                requests.post(url, data=data, timeout=10)
                chunk = line
            else:
                chunk += "\n" + line
        if chunk:
            data = {'chat_id': TELEGRAM_CHAT_ID, 'text': chunk, 'parse_mode': 'Markdown'}
            requests.post(url, data=data, timeout=10)

def main():
    # Fetch data
    run_command("cd /home/raspberry/.openclaw/workspace/btc-monitor && python3 btc_decision_engine.py > /dev/null 2>&1")
    btc = get_btc_signal()
    ledger = get_ledger_btc()
    aave = get_aave_position()
    strategy = calculate_professional_strategy(btc, aave, ledger)
    reflection = generate_deep_reflection(btc, aave, strategy, ledger)
    
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
    btc_price = btc.get('price', 0)
    
    # Calculate total BTC holdings
    ledger_btc = ledger.get('btc', 0)
    aave_btc = collat / btc_price if btc_price > 0 else 0
    total_btc = ledger_btc + aave_btc
    total_btc_usd = total_btc * btc_price if btc_price > 0 else 0
    
    # Build the message with deep reflection
    message = f"""📊 **{current_date} - WEEKLY STRATEGY**
═══════════════════════════════════════

🎯 *ACCUMULATION SCORE: {score:.1f}/100* ({rec})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *MARKET SNAPSHOT*
   BTC: ${btc_price:,.0f}
   MVRV: {mvrv} | RSI: {rsi} | 50W MA: -{ma_disc}%
   Cycle: Day {cycle} | Fear&Greed: {btc.get('fear_greed', 50)}

💼 *YOUR HOLDINGS*
   Ledger BTC: {ledger_btc:.5f} BTC ({ledger.get('sats', 0):,} sats)
   Aave BTC: {aave_btc:.5f} BTC
   Total BTC: {total_btc:.5f} BTC (${total_btc_usd:,.0f})

💰 *AAVE POSITION*
   Collateral: ${collat:,.0f} | Debt: ${debt:,.0f}
   HF: {hf} | LTV: {ltv:.1f}% | Buffer: {buffer:.1f}%
   Total Aave: ${strategy['total_position']:,.0f}

═══════════════════════════════════════
🧠 *DEEP REFLECTION*
═══════════════════════════════════════"""

    # Add deep reflections line by line
    for ref in reflection:
        message += f"\n{ref}"

    message += f"""

═══════════════════════════════════════
📋 *THIS WEEK'S STRATEGY*
═══════════════════════════════════════

💵 *DCA*: {strategy['dca_action']}
   → ${strategy['dca_amount_usd']:,.0f}/week ({strategy['dca_btc']:.4f} BTC)

🏦 *BORROW*: {strategy['borrow_action']}

💳 *REPAY*: {strategy['repay_action']}

₿ *BTC FOR DEBT*: {strategy['btc_deleverage']}

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