---
name: btc-strategy
description: |
  BTC accumulation and Aave position management strategy for long-term holders.
  Use when: (1) providing weekly investment strategy, (2) analyzing BTC market cycles,
  (3) making DCA/borrow/repay decisions, (4) evaluating Aave health factor and LTV,
  (5) reviewing BTC accumulation score, or (6) discussing Bitcoin investment decisions.
  This skill provides the 11-indicator scoring model and AI-powered decision framework
  for Colombia Staking BTC strategy. Includes daily AI-powered strategy automation.
---

# BTC Investment Strategy

---

## 👤 User Profile: Sébastien (Colombia Staking)

### Personal Financial Context

| Attribute | Value |
|-----------|-------|
| **Income** | €1,800/month (freelance, variable) |
| **Expenses** | €800/month |
| **Available for BTC** | ~€1,100/month (base budget) |
| **Risk Tolerance** | Conservative (due to freelance variability) |
| **Time Horizon** | 5+ years |
| **Strategy Goal** | Use BTC as collateral for loans, NOT to sell |

### Financial Goals (5-Year Timeline)

| Goal | Estimated Cost | Timeline | BTC Needed (@ $70K) |
|------|----------------|----------|---------------------|
| Car | €15,000-25,000 | 1-2 years | ~0.35-0.5 BTC |
| Small Projects | €30,000-50,000 | 2-3 years | ~0.7-1 BTC |
| Real Estate | €50,000-100,000 | 3-5 years | ~1-2 BTC |

### DCA Budget Limits

- **Max Monthly DCA: €1,100 (never exceed)
- **Weekly DCA: €275/week (or 2% of Aave position, whichever is lower)
- **Strategy**: Scale DCA with position, but cap at budget

---

## 🎯 Core Philosophy

**"We are long-term Bitcoin holders, not daily traders."**

The strategy is designed for accumulation during bear markets and cycle lows. Focus on:
- Systematic DCA during deep accumulation zones
- Strategic leverage during optimal conditions
- Risk management via Health Factor and LTV
- Position sizing based on total portfolio
- **Personal constraint**: Never exceed €1,100/month DCA budget

### DCA Scaling Rules (20-Level Table)

**Base:** €275/week = €1,100/month at 100% intensity

| Score | DCA | Weekly € | Notes |
|-------|-----|----------|-------|
| 0-5 | 200% | €550 | 🟢 Maximum accumulation |
| 6-10 | 185% | €509 | 🟢 Maximum accumulation |
| 11-15 | 170% | €468 | 🟢 Strong accumulation |
| 16-20 | 155% | €426 | 🟢 Strong accumulation |
| 21-25 | 140% | €385 | 🟢 Accumulation |
| 26-30 | 125% | €344 | 🟢 Normal accumulation |
| 31-35 | 110% | €303 | 🟢 Accumulation |
| 36-40 | 95% | €261 | 🟡 Light accumulation |
| 41-45 | 80% | €220 | 🟡 Light accumulation |
| 46-50 | 70% | €193 | 🟡 Reduced |
| 51-55 | 50% | €138 | 🟠 Minimal |
| 56-60 | 25% | €69 | 🟠 Minimal |
| 61-65 | 50% | €138 | 🟠 Early bull (before profit-taking) |
| 66-70 | 25% | €69 | 🟠 + Smoothed profit-taking |
| 71-75 | STOP | €0 | 🔴 Profit-taking mode |
| 76-100 | STOP | €0 | 🔴 Distribution |

---

## 11-Indicator Scoring Model (v7.9a — Granular Thresholds)

All indicators now use **10-step granular thresholds** (v7.9a, April 2026). This reduces false signals when indicators sit near boundaries and reflects the modern ETF-era market structure.

### Composite Structure

| Composite | Indicators | Weight | Bear Synergy | Bull Synergy |
|-----------|------------|--------|--------------|--------------|
| **Valuation** | MVRV + RSI | 30% | MVRV < 1.0 + RSI < 40 → -6 | MVRV > 2.0 + RSI > 70 → +6 |
| **Trend** | 50W MA + Cycle Position | 20% | MA < -20% + Bear (104K-208K blocks) → -8 | MA > +20% + Early bull (0-52K blocks) → +8 |
| **Sentiment** | Fear & Greed + ETF | 17% | F&G < 25 + ETF outflows > 5000 → -6 | F&G > 75 + ETF inflows > 5000 → +6 |
| **Momentum** | MACD + Bollinger | 12% | *(merged into Valuation)* | *(merged into Valuation)* |
| **Standalone** | Geopolitical | 5% | - | - |
| **Standalone** | Pi Cycle | 3% | - | - |
| **Standalone** | Stock-to-Flow | 3% | - | - |
| **Buffer** | AI discretion | 10% | For edge cases | For edge cases |

### Key v7.9a Improvements

| Indicator | Old Steps | New Steps | Biggest Fix |
|-----------|-----------|-----------|-------------|
| **MVRV** | 7 | **10** | 1.0-1.5 lumped into "normal" → now split into early/mid/late bull |
| **RSI** | 6 | **10** | 50 threshold was too blunt → true neutral now 48-52 |
| **MACD** | 7 | **10** | 5000 threshold too sensitive → added 10000 tier |
| **ETF Flow** | 7 | **10** | Pre-2024 thresholds → modern ETF era calibrated |
| **Pi Cycle** | 6 | **10** | Positive diff now correctly scored as bullish |
| **50W MA** | 7 | **10** | Added generational crash tier (< -50%) |
| **Cycle Position** | 6 | **9** | **HISTORICALLY CORRECTED** — peaks at ~78K blocks, not 104K+ |

### Why Granular?

**Old problem:** MACD at 5,752 scored 85 ("EXTREME MOMENTUM") while RSI was 40.5 ("BUY ZONE"). These should NOT diverge that much. The new 10-step system scores MACD 5,752 at 78 instead of 85 — still high but not distorted.

**ETF era reality:** -526 BTC/day used to score 65 ("OUTFLOWS"). In the post-2024 ETF era, that's mild. New system scores it 52 ("NEUTRAL/MILD").

**Cycle correction:** Old model said 107K blocks = "LATE CYCLE" (45). Historical peaks happen at ~70-80K blocks. New system: 107K blocks = "POST-PEAK CORRECTION" (28) — matches 2017/2021/2025 reality.

### Symmetric Scoring

The v7.9a system is **symmetric** - scores range from 10 (extreme bear) to 90 (extreme bull):

| Score Range | Interpretation | DCA Action |
|-------------|----------------|------------|
| **10-25** | 🟢 EXTREME BUY | €385-550/week (150-200% - maximum accumulation) |
| **25-35** | 🟢 BUY | €303-344/week (110-125%) |
| **35-45** | 🟡 ACCUMULATION | €220-261/week (80-95% - normal) |
| **45-55** | 🟡 NEUTRAL | €138-193/week (50-70%) |
| **55-65** | 🟠 EXPENSIVE | €69-138/week (25-50%) |
| **65-75** | 🟠 CAUTION | €0/week (pause DCA) |
| **> 75** | 🔴 SELL/DISTRIBUTE | €0 + consider taking profit |

### Synergy Rationale

**Why Momentum synergy was removed (v7.1):**
- MACD and Bollinger both measure momentum → double-counting
- VALUATION synergy already captures oversold conditions via RSI

**Why synergies are balanced (v7.2):**
- Bear synergies (negative) = LOWER score = MORE bullish = deeper accumulation
- Bull synergies (positive) = HIGHER score = MORE bearish = distribution zone
- Max synergy range: **-20 to +20** (symmetric)

---

## Score Zones (v7.9 - 20-Level Table)

| Score | Zone | Weekly EUR | Regime |
|-------|------|------------|--------|
| **0-25** | 🟢 BUY | €385-550 | Maximum accumulation |
| **26-35** | 🟢 BUY | €303-344 | Strong accumulation |
| **36-45** | 🟡 ACCUMULATE | €220-261 | Light accumulation |
| **46-50** | 🟡 NEUTRAL | €193 | Reduced |
| **51-60** | 🟠 EXPENSIVE | €69-138 | Minimal DCA |
| **61-70** | 🟠 EARLY BULL | €69-138 | + Smoothed profit-taking |
| **71-75** | 🔴 CAUTION | €0 | Full profit-taking |
| **> 75** | 🔴 SELL | €0 | Distribution phase |

**HF Override:** HF < 1.3 → STOP all DCA. HF < 1.5 → 50% reduction.

**Profit-Taking (Score ≥ 65):** Smoothed across full bull run
- Formula: `(score - 65) / 30 × 25` = target cumulative %
- Weekly incremental = this week's cumulative - last week's cumulative
- Result: 25% spread over ~30 weeks instead of ~3 weeks
- Example at score 77: ~1.67%/week ($217/week on €1,100 base)

---

## Aave Position Rules

### Health Factor Thresholds
- **HF > 2.0**: Healthy - can consider borrowing
- **HF 1.5-2.0**: Moderate - monitor closely
- **HF < 1.5**: Warning - reduce debt
- **HF < 1.3**: Danger - prioritize deleveraging

### LTV Limits (Sebas - Adjusted March 2026)
- **LTV < 45%**: Safe - Room for more leverage
- **LTV 45-55%**: Warning zone - Monitor closely
- **LTV 55-60%**: Aggressive - Near max, be cautious
- **LTV > 60%**: Reduce exposure (Sebas max)

### Decision Matrix (Sebas - Updated)

| HF | LTV | Score | Decision |
|----|-----|-------|----------|
| > 2.0 | < 45% | < 35 | ✅ Borrow for project |
| > 2.0 | < 50% | < 40 | ✅ Optional borrow |
| > 1.5 | < 60% | any | ⚪ Neutral - monitor |
| < 1.5 | > 50% | any | ❌ No new debt |
| < 1.3 | any | any | ❌ Deleverage ASAP |

**Note:** Updated to 60% LTV max (from 40%) for more flexibility. Still conservative due to freelance income variability.

---

## Daily AI-Powered Strategy (Automation)

**Cron Job:** BTC AI Daily Strategy
- Runs: Every day at 8:00 AM (Bogotá time)
- Session: Telegram direct (delivers to Sebas)
- Process: Run scripts → AI analyzes → Strategy delivered

### Ledger Holdings Tracking (xpub Scan)

**Wallet:** Ledger Nano S/X via BIP84 xpub  
**Xpub:** `xpub6CjqJTKYKEYHJxJWePZ44hAM5EDrJ58sJLDWgNGcbRd2VKmHo8UPRJQbtBeaMZpA1BpByPXdge5wxcVtbJMKAnEhNtGWcC584EJc8Ba7gWS`

**How it works:**
- Ledger auto-generates new receiving addresses for each transaction (privacy)
- Balance is spread across multiple addresses, not just one
- Single-address checks show **0 BTC** even when funds exist at other indices

**Solution:** `/home/raspberry/.openclaw/workspace/scripts/scan_xpub.py`
- Scans BIP84 receiving chain (`m/84'/0'/0'/0/i`) + change chain (`m/84'/0'/0'/1/i`)
- Gap limit 20, max index 200
- Auto-updates `btc-position.json`

**Current holdings (Apr 29, 2026):**
- Receiving indices 27-31: 0.09154928 BTC
- Change index 19: 0.05247096 BTC
- **Total: 0.14402024 BTC**

**Integration:** Daily report runs xpub scan before reading balance.

---

### Daily Report Format (v8.0 — Simplified)

```
📊 BTC Daily — April 29, 2026

🎯 Score: 31.4/100 — 🟢 BUY

📈 Market
• BTC: $75,916 | MVRV: 1.29
• RSI: 40.6 | 50W MA: -21.2%
• Fear & Greed: 50

💰 Position
• Ledger: 0.1440 BTC ($10,935)
• Aave: $0 collateral | $0 debt
• Total: 0.1440 BTC ($10,935)

📋 Strategy
• DCA: €385/week — Deep value zone
• Borrow: No — Deep value zone
• Repay: No — Deep value zone

⚠️ Watch: Deep value zone
```

**What was removed (v7.x → v8.0):**
- Deep reflection section
- Market regime breakdown
- Bull market signals
- Risk check section
- Model confidence section

**What was added:**
- Auto xpub scan for Ledger balance accuracy
- Concise bullet-point format

---

## Weekly Strategy Output (Manual/On-Demand)

When generating a full weekly strategy (on-demand, not daily automation), include:

1. **Market Snapshot**: Score, price, key indicators (MVRV, RSI, 50W MA)
2. **Position Status**: HF, LTV, liquidation buffer, total position (in EUR)
3. **🧠 Deep Reflection**: AI analysis of:
   - Current cycle position and historical context
   - Valuation assessment (MVRV interpretation)
   - Technical outlook (RSI, trend)
   - Risk assessment and buffer analysis
   - Strategic big-picture view
4. **Clear Decisions** (in EUR for Sebas):
   - DCA amount (€ and BTC/sats)
   - Borrow Y/N with amount
   - Repay Y/N with amount
   - Use BTC for debt Y/N
5. **Progress Toward Goals**: Track BTC accumulation vs car/projects targets (only when relevant)

---

## References

- [STRATEGY.md](references/STRATEGY.md) - Deep reasoning and decision framework
- [INDICATORS.md](references/INDICATORS.md) - Detailed indicator definitions
- [btc_decision_engine.py](scripts/btc_decision_engine.py) - Core scoring engine
- [daily_strategy_report.py](scripts/daily_strategy_report.py) - Weekly report generator

---

## Strategy Evolution

**Quarterly Review Process:**

Every 3 months, analyze:
1. Did the score accurately predict the cycle?
2. Which indicators gave false signals?
3. Did our Aave decisions work out?
4. What would we do differently?

**Evolution Triggers:**
- New major indicator emerges (e.g., ETF flows post-2024)
- Significant market structure change
- Clear pattern in our decisions that failed
- User requests adjustment

**How to Evolve:**
1. Document the issue in STRATEGY.md
2. Propose weight/indicator changes
3. Test against historical data
4. Update version number
5. Push to GitHub with commit message

**Current Version:** v8.0: Simplified daily report format + auto xpub scanning for Ledger balance accuracy (April 2026)
- v5.0: Weekly candles (long-term focus)
- v5.1: Research-based weights
- v5.2: Professional advisory format
- v5.3: Aave position integration
- v5.4: Bull market tiered exit strategy
- v5.5: ETF trend scoring
- v5.6: MACD/Pi Cycle bear market overrides
- v5.7: ETF btcetfdata.com integration
- v5.8: ETF persistent cache with trend tracking
- v5.9: Automatic market regime detection (7 phases)
- v6.0: Dynamic Geopolitical indicator using VIX + DXY (live market data)
- v6.1: AI-powered daily strategy automation with context-aware analysis
- v6.2: TRUE 50W MA (from weekly closes) + removed 200W blend
- v7.0: COMPOSITE INDICATORS with SYNERGY BONUSES - 4 new composites
- v7.1: Balanced synergies (-44 max → -20 max), removed momentum double-counting
- v7.2: BULL MARKET SYNERGIES added for symmetric scoring (+20 max)
- v7.3: INDICATOR-BASED PROFIT-TAKING (v7.3 was internal/dev, not released)
- v7.8: 20-level DCA/profit-taking table via dca_lookup.py - smooth transitions
- v7.9: Smoothed profit-taking + €1,100/month budget (April 2026)
- v7.9a: Granular 10-step scoring + historically-corrected cycle timing
- **v8.0: Simplified daily report + auto xpub Ledger scanning**

---

*Skill owner: Colombia Staking*
*Advisor: Alice (AI Assistant)*
