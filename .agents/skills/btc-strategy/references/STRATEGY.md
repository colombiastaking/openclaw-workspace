# BTC Investment Strategy - Deep Reasoning

## Philosophy

**"We are long-term Bitcoin holders, not daily traders."**

This strategy is designed for accumulation during bear markets and cycle lows. We don't try to time tops or trade frequently. We DCA systematically and leverage responsibly during deep accumulation zones.

---

## Core Principles

### 1. Accumulation Score < 30 = Maximum DCA
When the score drops below 30, we're in a "deep bear" zone - historically the best time to accumulate. This aligns with:
- MVRV < 1.0 (undervalued)
- RSI < 40 (oversold)
- Price below 50W MA (discount)
- Post-halving bear market (600-750 days)

### 2. Don't Fight the Cycle
Bitcoin cycles are driven by:
- Halving events (every 4 years)
- Market sentiment swings
- Institutional adoption waves

Our cycle position indicator tracks days since halving to identify which phase we're in.

### 3. Leverage Strategically, Not Emotionally
- HF > 1.5 = Healthy position, can consider borrowing
- LTV < 45% = Safe zone
- LTV 45-55% = Warning zone
- LTV 55-60% = Aggressive (near max)
- Score < 35 = Good zone for leverage (accumulation)

### 4. Position Size Matters
DCA scales with portfolio:
- 2% of total Aave position per week (base)
- Multiplied by score factor (1.0 - 1.5x)
- More aggressive in deep accumulation

---

## Decision Framework

### DCA Decision Matrix

| Score | Zone | DCA Level | Rationale |
|-------|------|-----------|-----------|
| < 25 | Deep Bear | 150% | Maximum accumulation |
| 25-35 | Bear | 125% | Strong buy |
| 35-45 | Accumulation | 100% | Normal DCA |
| 45-55 | Neutral | 75% | Reduce exposure |
| 55-65 | Expensive | 50% | Minimal DCA |
| > 65 | Bubble | 0% | Stop DCA |

### Borrow Decision Matrix

| HF | LTV | Buffer | Score | Decision |
|----|-----|--------|-------|----------|
| > 2.0 | < 45% | > 30% | < 35 | ✅ YES - Borrow to DCA more |
| > 2.0 | < 50% | > 20% | < 40 | ✅ YES - Optional |
| > 1.5 | < 60% | > 15% | any | ⚪ Neutral |
| < 1.5 | > 50% | < 15% | any | ❌ NO - Reduce debt |
| < 1.3 | any | < 10% | any | ❌ NO - Deleverage |

### Repay Decision Matrix

| HF | Recommended Action |
|----|-------------------|
| > 2.0 | Focus on DCA instead |
| 1.5-2.0 | Optional - depends on cashflow |
| 1.3-1.5 | 5-10% of debt this week |
| < 1.3 | 20%+ of debt ASAP |

---

## Risk Management

### Liquidation Buffer
We maintain minimum 20% buffer above liquidation price:
- If BTC drops 50%, can we survive?
- HF should stay above 1.3 at minimum
- Emergency plan if HF drops below 1.2

### LTV Limits
- Target: 40-50% LTV
- Warning: > 45%
- Action needed: > 50%

### Position Sizing
- Never borrow more than 2x weekly DCA
- Always keep 6 months of DCA in reserve
- If HF drops, reduce debt first

---

## Why These Specific Indicators?

### MVRV (25%)
The Market Value to Realized Value ratio is the best single indicator of cycle bottoms. When MVRV < 1.0, BTC is trading below what holders actually paid - historically marks major bottoms.

### RSI (15%)
Relative Strength Index on weekly candles filters out daily noise. < 40 = oversold, > 70 = overbought.

### 50W MA Discount (12%)
The 50-week moving average is a key cycle indicator. When price drops 20%+ below 50W MA, we're in bear territory.

### Fear & Greed (12%)
Captures sentiment extremes. Fear = buy, Greed = sell. Weekly average smooths daily volatility.

### Cycle Position (10%)
Days since halving. History shows:
- 0-180 days: Early bull (not ideal for DCA)
- 600-750 days: Bear market = BEST accumulation
- 900+ days: Late bear/early bull

---

## Backtesting Notes

Historical performance of this approach:
- 2018-2019 bear: Score hit 20-25, DCA at $3k-$6k
- 2022 bear: Score hit 25-30, DCA at $20k-$30k
- Both periods led to 3-5x returns within 2-3 years

---

## Strategy Versions

| Version | Date | Change |
|---------|------|--------|
| v1.0 | Early 2024 | Basic RSI + MVRV model |
| v3.0 | 2024 | Added cycle, fear/greed |
| v5.0 | March 2026 | Weekly candles (long-term) |
| v5.1 | March 2026 | Research-based weights |
| v5.2 | March 2026 | Professional advisory |
| v5.3 | March 2026 | Auto-scaled DCA |

---

*Last Updated: 2026-03-26*
*Strategy Owner: Colombia Staking*
*Advisor: Alice (AI Assistant)*