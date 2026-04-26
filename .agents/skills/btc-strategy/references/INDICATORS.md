# Indicator Definitions (v7.0 - COMPOSITE INDICATORS)

## NEW: Composite Indicator Structure

v7.0 combines related indicators into composites with SYNERGY BONUSES. When two related indicators both signal the same direction, the composite score gets an additional bonus adjustment (up to ±12 points) for more accurate cycle detection.

---

## COMPOSITE 1: VALUATION (30% total weight)

**Components:** MVRV (60%) + RSI (40%)

### MVRV - Market Value / Realized Value
**What it measures:** Ratio of Bitcoin's market cap to realized cap (cost basis of all BTC)

**Why it matters:**
- MVRV < 1.0: Price below average cost basis = UNDERVALUED
- MVRV ~1.0: Fair value
- MVRV > 2.0: Overvalued (bubble territory)

**Scoring:**
- < 0.7: Score 5 (Deep value)
- 0.7-0.9: Score 15 (Good value)
- 0.9-1.1: Score 22 (Fair)
- 1.1-1.5: Score 35 (Normal)
- 1.5-2.0: Score 55 (Expensive)
- > 2.0: Score 75-90 (Bubble)

### RSI - Relative Strength Index (Weekly)
**What it measures:** Momentum indicator measuring speed/change of price movements

**Why it matters:** Weekly RSI filters daily noise for long-term signals

**Scoring:**
- < 30: Score 5 (Oversold)
- 30-40: Score 15 (Accumulate)
- 40-50: Score 25 (Buy zone)
- 50-60: Score 45 (Neutral)
- 60-70: Score 65 (Overbought)
- > 70: Score 85 (Bubble)

### VALUATION SYNERGY BONUS
When **BOTH** MVRV < 1.0 **AND** RSI < 40:
→ **-12 bonus** to composite score (stronger bottom signal)

---

## COMPOSITE 2: TREND (20% total weight)

**Components:** 50W MA Discount (50%) + Cycle Position (50%)

### 50 Week MA Discount
**What it measures:** Percentage price is below/above 50-week moving average

**Implementation (v6.2+):** TRUE 50W MA from weekly closing prices

**Historical context:**
- 2018 bottom: Price 70%+ below 50W MA
- 2022 bottom: Price 30%+ below 50W MA
- 2021 top: Price 100%+ above (bubble)

**Scoring:**
- < -40%: Score 8 (Massive discount)
- -40% to -25%: Score 18 (Deep discount)
- -25% to -15%: Score 28 (Discount)
- -15% to 0%: Score 38 (Below MA)
- 0% to +15%: Score 50 (Near MA)
- +15% to +30%: Score 65 (Premium)
- > +30%: Score 85 (Extreme premium)

### Cycle Position
**What it measures:** Days since most recent halving

**Why it matters:** Bitcoin has predictable 4-year cycles

**Historical patterns:**
- 0-180 days: Early bull (not ideal)
- 180-400 days: Mid cycle
- 400-600 days: Late cycle / Peak
- 600-750 days: BEAR = BEST ACCUMULATION
- 750-900 days: Deep bear = Maximum accumulation
- 900+ days: Late bear / Early bull

**Scoring:**
- 600-750 days: Score 15 (Bear accumulation)
- 750-900 days: Score 8 (Deep bear)
- 0-180 days: Score 40 (Early bull)
- 180-400 days: Score 30-40 (Mid cycle)
- 400-600 days: Score 45-50 (Late cycle)
- Other: Score 35

### TREND SYNERGY BONUS
When **BOTH** 50W MA deeply discounted (< -20%) **AND** in bear phase (600-900 days):
→ **-10 bonus** to composite score (confirmed deep bear)

---

## COMPOSITE 3: SENTIMENT (17% total weight)

**Components:** Fear & Greed (60%) + ETF Sentiment (40%)

### Fear & Greed Index
**What it measures:** Market sentiment from multiple sources

**Why it matters:** Extreme fear (0-25) marks bottoms. Extreme greed (75-100) marks tops.

**Scoring:**
- 0-20: Score 5 (Extreme fear = Buy)
- 20-30: Score 18 (Fear = Accumulate)
- 30-45: Score 30 (Cautious)
- 45-55: Score 45 (Neutral)
- 55-70: Score 65 (Greed)
- 70-85: Score 82 (Extreme greed)
- 85-100: Score 95 (Bubble)

### ETF Sentiment
**What it measures:** Net flows in Bitcoin ETFs (institutional sentiment)

**Why it matters:** Since 2024, ETF flows drive BTC price

**Scoring:**
- > +3000 BTC/day: Score 5 (Massive inflows)
- +1500 to +3000: Score 15 (Strong inflows)
- +500 to +1500: Score 25 (Positive)
- -500 to +500: Score 45 (Neutral)
- -500 to -1500: Score 65 (Outflows)
- -1500 to -3000: Score 80 (Heavy outflows)
- < -3000: Score 92 (Capitulation)

### SENTIMENT SYNERGY BONUS
When **BOTH** Fear & Greed < 25 (extreme fear) **AND** ETF outflows > 1500 BTC/day:
→ **-12 bonus** to composite score (CAPITULATION signal)

---

## COMPOSITE 4: MOMENTUM (12% total weight)

**Components:** MACD (50%) + Bollinger Bands (50%)

### MACD (Weekly)
**What it measures:** 12/26/9 weekly EMA crossover

**Important:** Detects intra-cycle rallies (bear market bounces)

**Scoring:**
- < -5000: Score 8 (Strong bear momentum - bottoming)
- -5000 to -2000: Score 18 (Bear weakening)
- -2000 to -500: Score 28 (Early accumulation)
- -500 to +500: Score 45 (Neutral)
- +500 to +2000: Score 55 (Bull momentum)
- +2000 to +5000: Score 70 (Strong bull)
- > +5000: Score 85 (Extreme - topping)

### Bollinger Bands (Weekly)
**What it measures:** Price position relative to 20-week bands

**Scoring:**
- < 0 (below lower band): Score 5 (Extreme discount)
- 0-0.2: Score 12 (Near lower band)
- 0.2-0.4: Score 22 (Lower half)
- 0.4-0.6: Score 45 (Middle)
- 0.6-0.8: Score 60 (Upper half)
- 0.8-1.0: Score 75 (Near upper band)
- > 1.0: Score 88 (Above upper band)

### MOMENTUM SYNERGY BONUS
When **BOTH** MACD histogram deeply negative (< -2000) **AND** price at lower Bollinger band (< 0.2):
→ **-10 bonus** to composite score (momentum bottom)

---

## STANDALONE INDICATORS

### Geopolitical Risk (5%)
**What it measures:** Global risk via VIX + DXY

**Scoring:**
- VIX > 30 (Extreme crisis): Score 10
- VIX 25-30 (High crisis): Score 20
- VIX 20-25 (Elevated): Score 35
- VIX 15-20 (Moderate): Score 45
- VIX < 15 (Low risk): Score 40

### Pi Cycle (3%)
**What it measures:** 111-day MA × 2 vs 350-day MA crossover

**Scoring:**
- < -20%: Score 8 (Bottom pattern)
- -20% to -5%: Score 18 (Recovering)
- -5% to +30%: Score 40 (Normal bull)
- +30% to +60%: Score 60 (Extended)
- +60% to +100%: Score 80 (Warning)
- > +100%: Score 95 (Bubble)

### Stock-to-Flow (3%)
**What it measures:** Scarcity model - supply vs annual production

**Post-2024 halving S2F ~120** = most scarce BTC has ever been

**Scoring:**
- > 110: Score 10 (Extreme scarcity)
- 90-110: Score 18 (Very scarce)
- 70-90: Score 30 (High scarcity)
- 50-70: Score 50 (Moderate)
- < 50: Score 70 (Less scarce)

---

## SYNERGY SUMMARY (v7.0)

| Composite | When Both Signal Bullish | Bonus |
|-----------|------------------------|-------|
| Valuation | MVRV < 1.0 AND RSI < 40 | -12 |
| Trend | 50W MA < -20% AND Bear phase | -10 |
| Sentiment | F&G < 25 AND ETF outflows | -12 |
| Momentum | MACD < -2000 AND BB < 0.2 | -10 |

**Total potential bonus:** Up to -44 points when ALL composites align at cycle bottom!

**Note:** Negative bonus = LOWER score = MORE bullish for accumulation

---

*Last Updated: 2026-03-27 (v7.0)*
