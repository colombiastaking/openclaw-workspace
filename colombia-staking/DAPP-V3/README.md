# 🇨🇴 Colombia Staking DApp

**Live:** [https://colombia-staking.com](https://colombia-staking.com)

## Overview

The Colombia Staking DApp is a Web3 application for MultiversX staking with:
- **Dual staking**: eGLD + COLS tokens for bonus APR
- **Gamified ranking**: Gold/Silver/Bronze leagues
- **Tax report generation**: Automated tax reports for stakers
- **Live blockchain data**: Real-time APR, rankings, and statistics

---

## Features

### APR & Ranking System

The DApp calculates dynamic APR based on:
- **COLS/eGLD staking ratio** - Higher ratio = higher bonus
- **DAO rewards** - Redistributed to dual stakers
- **League system** - Gold/Silver/Bronze based on APR ranking

#### APR Formula
```
Total APR = Base APR + COLS Bonus + DAO Rewards
```

| User Staking | Formula |
|--------------|---------|
| COLS + eGLD  | `baseApr + APR_BONUS + DAO` |
| COLS only    | `APR_COLS_ONLY` |
| Neither      | `baseApr` |

### Tax Report Generation

Users can generate tax reports for any year:
- **Cost**: 5 COLS per year per address
- **Payment**: On-chain via smart contract
- **Reports**: Cover 2020-2026

---

## Tech Stack

- **Framework**: React + TypeScript + Vite
- **Blockchain**: MultiversX SDK (sdk-dapp)
- **Styling**: CSS with responsive design
- **API**: MultiversX API + Custom stats-api.php

---

## Project Structure

```
DAPP-V3/
├── src/
│   ├── components/     # React components
│   │   └── Stake/     # Staking UI (RankingTable, Stake.tsx)
│   ├── hooks/         # Custom React hooks
│   │   └── useColsApr.ts  # APR calculation
│   └── ...
├── scripts/           # Distribution scripts
│   ├── execute_bonus_distribution_v3.cjs
│   ├── execute_distribution_fixed.cjs
│   └── send_missing_bonus.cjs
├── build/             # Production build
└── public/            # Static assets
```

---

## Recent Changes

### v2026.03 - Tax Report Fixes
- Fixed: include GOLD in execute --all
- Fixed: remove duplicate pay button
- Fixed: year dropdown (removed 2020 - no historical prices)
- Fixed: payment status check response path
- Fixed: BigUint handling in payment verification
- Fixed: ESDTTransfer amount hex encoding
- Fixed: auto-refresh report after payment confirms
- Fixed: hide full tax report details until payment verified

### v2026.02 - Staking Improvements
- Added years 2020-2026 to tax report
- Improved mobile responsiveness
- Added live blockchain data for validators/staked amounts

---

## Smart Contract

- **Contract**: `erd1qqqqqqqqqqqqqpgqlc3h8hvk99r2jdqzcq7wdw5tca8d2c90uyrsf5h6au`
- **Network**: MultiversX Mainnet
- **Token**: COLS

---

## Scripts

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build

# Execute bonus distribution
node scripts/execute_bonus_distribution_v3.cjs --all

# Send missing bonus
node scripts/send_missing_bonus.cjs --recipients recipients.json
```

---

## Related Repos

| Repo | Purpose |
|------|---------|
| [Website](https://github.com/colombiastaking/Website) | 3-language website |
| [btc-strategy](https://github.com/colombiastaking/btc-strategy) | BTC investment strategy |
| [tax-report-payment](https://github.com/colombiastaking/tax-report-payment) | Tax payment smart contract |
| [alice-backup](https://github.com/colombiastaking/alice-backup) | Alice backup & disaster recovery |

---

## Links

- **DApp**: https://colombia-staking.com
- **Telegram (EN)**: https://t.me/ColombiaStakingChat
- **Telegram (ES)**: https://t.me/colombiastakingesp
- **Telegram (FR)**: https://t.me/colmbiastakingfr
