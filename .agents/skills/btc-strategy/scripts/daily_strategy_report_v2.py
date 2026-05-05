#!/usr/bin/env python3
"""
Daily Strategy Report - Simplified v2
BTC Accumulation + Aave Position
"""

import json
import subprocess
import os
import requests
import re
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1144365829")

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def get_btc_signal():
    try:
        with open('/tmp/btc_general_report.json', 'r') as f:
            data = json.load(f)
            # Flatten summary into top level for compatibility
            summary = data.get('summary', {})
            result = {
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
            return result
    except Exception as e:
        print(f"Error reading btc_general_report.json: {e}")
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
    """Get Ledger BTC from xpub scan."""
    # Run xpub scan first
    run_command("/usr/bin/python3 /home/raspberry/.openclaw/workspace/scripts/scan_xpub.py")
    
    # Read from btc-position.json
    try:
        with open('/home/raspberry/.openclaw/workspace/btc-position.json', 'r') as f:
            pos = json.load(f)
            return pos.get("btc_holding", 0)
    except:
        return 0

def get_aave_position():
    output = run_command("cd /home/raspberry/.openclaw/workspace/aave-monitor && python3 btc_monitor.py")
    hf = 1.5; collateral_btc = 0; collateral_usd = 0; debt_usd = 0
    liq_price = 0; buffer_pct = 0; btc_price = 75000
    
    for line in output.split('\n'):
        if 'Current HF:' in line:
            try: hf = float(re.search(r'(\d+\.\d+)', line).group(1))
            except: pass
        if 'Collateral:' in line and 'BTC' in line:
            try: collateral_btc = float(line.split('BTC')[0].split(':')[1].strip().split()[0])
            except: pass
        if 'Debt:' in line:
            try: debt_usd = float(line.split('$')[-1].replace(',','').strip())
            except: pass
        if 'HF 1.0' in line and 'DANGER' in line:
            try: liq_price = float(line.split('$')[-1].replace(',','').strip())
            except: pass
        if 'BTC Price:' in line:
            try: btc_price = float(line.split('$')[1].replace(',','').strip())
            except: pass
    
    collateral_usd = collateral_btc * btc_price
    if btc_price > 0 and liq_price > 0: buffer_pct = ((btc_price - liq_price) / btc_price) * 100
    ltv = (debt_usd / collateral_usd * 100) if collateral_usd > 0 else 0
    
    ledger_btc = get_ledger_btc()
    
    return {
        'health_factor': hf, 'collateral_btc': collateral_btc,
        'collateral_usd': collateral_usd, 'debt_usd': debt_usd,
        'buffer_pct': buffer_pct, 'btc_price': btc_price, 'ltv': ltv,
        'ledger_btc': ledger_btc, 'total_btc': collateral_btc + ledger_btc,
        'total_usd': collateral_usd + (ledger_btc * btc_price)
    }

def calculate_strategy(score, aave):
    dca = 0; borrow = 0; repay = 0
    posture = "NEUTRAL"; reason = "Score neutral"
    
    if score <= 25:
        dca = 385; posture = "ACCUMULATE"; reason = "Deep value zone"
    elif score <= 35:
        dca = 303; posture = "ACCUMULATE"; reason = "Good value"
    elif score <= 45:
        dca = 220; posture = "LIGHT ACCUMULATION"; reason = "Fair value"
    elif score <= 55:
        dca = 138; posture = "REDUCED"; reason = "Neutral"
    else:
        dca = 0; posture = "STOP"; reason = "Expensive territory"
    
    if aave['health_factor'] < 1.3:
        repay = 500; posture = "DELEVERAGE"; reason = "HF critical"
    elif aave['health_factor'] < 1.5:
        repay = 250
    
    return {
        'dca_amount_eur': dca, 'dca_btc': dca / aave['btc_price'] if aave['btc_price'] > 0 else 0,
        'borrow_amount_eur': borrow, 'repay_amount_eur': repay,
        'strategic_posture': posture, 'posture_reason': reason
    }

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=data, timeout=10)

def main():
    run_command("cd /home/raspberry/.openclaw/workspace/.agents/skills/btc-strategy/scripts && python3 btc_decision_engine.py > /dev/null 2>&1")
    btc = get_btc_signal()
    aave = get_aave_position()
    strategy = calculate_strategy(btc.get('score', 50), aave)
    
    current_date = datetime.now().strftime("%B %d, %Y")
    score = btc.get('score', 50)
    rec = btc.get('recommendation', 'NEUTRAL')
    
    message = f"""📊 BTC Daily — {current_date}

🎯 Score: {score}/100 — {rec}

📈 Market
• BTC: ${btc.get('price', 0):,.0f} | MVRV: {btc.get('mvrv', 0):.2f}
• RSI: {btc.get('rsi', 0):.1f} | 50W MA: {btc.get('ma_discount', 0):+.1f}%
• Fear & Greed: {btc.get('fear_greed', 50)} | ETF 7d: {btc.get('etf_net_flow_7d', 0):+,.0f} BTC

💰 Position
• Ledger: {aave.get('ledger_btc', 0):.4f} BTC (${aave.get('ledger_btc', 0) * btc.get('price', 0):,.0f})
• Aave: ${aave.get('collateral_usd', 0):,.0f} collateral | ${aave.get('debt_usd', 0):,.0f} debt
• Total: {aave.get('total_btc', 0):.4f} BTC (${aave.get('total_usd', 0):,.0f})

📋 Strategy
• DCA: €{strategy['dca_amount_eur']:,.0f}/week — {strategy['posture_reason']}
• Borrow: {'Yes' if strategy['borrow_amount_eur'] > 0 else 'No'} — {strategy['posture_reason']}
• Repay: {'€' + str(strategy['repay_amount_eur']) if strategy['repay_amount_eur'] > 0 else 'No'} — {strategy['posture_reason']}

⚠️ Watch: {strategy['posture_reason']}"""
    
    send_telegram(message)
    print("✅ Report sent!")
    
    # Save locally
    report_date = datetime.now().strftime('%Y-%m-%d')
    os.makedirs('/home/raspberry/.openclaw/workspace/btc-strategy/reports/daily', exist_ok=True)
    with open(f"/home/raspberry/.openclaw/workspace/btc-strategy/reports/daily/{report_date}.md", 'w') as f:
        f.write(message)
    
    # GitHub backup
    try:
        repo_path = '/home/raspberry/.openclaw/workspace/btc-strategy'
        subprocess.run(["git", "-C", repo_path, "add", "."], capture_output=True)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", f"Daily report - {report_date}"], capture_output=True)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], capture_output=True, timeout=30)
        print("✅ GitHub backup complete!")
    except Exception as e:
        print(f"⚠️ GitHub backup: {e}")

if __name__ == "__main__":
    main()
