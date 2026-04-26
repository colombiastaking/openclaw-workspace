# BTC Investment Strategy - Colombia Staking

## Overview
Professional BTC accumulation strategy combining:
- **BTC Accumulation Indicator** (custom scoring model)
- **Aave Position Management** (leverage & deleveraging)
- **Personalized Weekly Strategy** (DCA, borrow, repay decisions)

## Strategy Components

### 1. BTC Accumulation Score (btc_decision_engine.py)
Custom scoring model with COMPOSITE INDICATORS (v7.0):

| Composite | Indicators | Weight | Synergy |
|-----------|------------|--------|---------|
| Valuation | MVRV + RSI | 30% | Bottom detection bonus |
| Trend | 50W MA + Cycle Position | 20% | Bear phase confirmation |
| Sentiment | Fear & Greed + ETF | 17% | Capitulation detection |
| Momentum | MACD + Bollinger | 12% | Momentum bottom detection |
| Standalone | Geopolitical, Pi, S2F | 11% | - |
| Buffer | AI discretion | 10% | Edge cases |

**Key Innovation (v7.0): SYNERGY BONUSES**
When related indicators confirm each other, score gets additional boost (up to ±12 points per composite)

**Score < 30** = Strong Accumulation Zone  
**Score 30-45** = Good Accumulation  
**Score 45-60** = Neutral  
**Score > 60** = Expensive

### 2. Aave Position Management
- Health Factor monitoring
- LTV management (target: 60% max)
- Liquidation buffer tracking
- Automated deleveraging signals

### LTV Limits (v5.4 - March 2026)
| Zone | LTV | Action |
|------|-----|--------|
| Safe | < 45% | Room for more leverage |
| Warning | 45-55% | Monitor closely |
| Aggressive | 55-60% | Near max |
| Max | 60% | Reduce above |

### 3. Weekly Strategy (daily_strategy_report.py)
Personalized recommendations based on:
- BTC Accumulation Score
- Aave position (HF, LTV, buffer)
- Total portfolio size

Decisions generated:
- DCA amount (auto-scaled to position)
- Borrow more? (Y/N + amount)
- Repay loan? (Y/N + amount)
- Use BTC for debt? (Y/N)

## Files

```
btc-strategy/
├── scripts/
│   ├── btc_decision_engine.py  # Core accumulation scoring
│   ├── aave_btc_monitor.py     # Aave position monitor
│   └── daily_strategy_report.py # Daily report generator
├── docs/
│   ├── STRATEGY.md             # This file
│   └── INDICATORS.md           # Indicator definitions
└── reports/
    └── daily/                  # Daily report outputs
```

## Daily Report
Sent daily at 8:00 AM via Telegram with:
- Market status (score, price, indicators)
- Aave position (HF, LTV, buffer)
- This week's clear strategy decisions
- Professional rationale for each decision

## Version History
- v5.0 - Long-term holder version (weekly candles)
- v5.1 - Research-based weights applied
- v5.2 - Professional advisory with weekly auto-scaling
- v5.4 - LTV max increased to 60%
- v6.2 - TRUE 50W MA (from weekly closes) + removed 200W blend
- v7.0 - COMPOSITE INDICATORS with SYNERGY BONUSES