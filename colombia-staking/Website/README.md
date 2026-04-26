# 🇨🇴 Colombia Staking Website

**Live:** [https://colombia-staking.com](https://colombia-staking.com)

## Overview

Official Colombia Staking website available in 3 languages:
- 🇬🇧 **English** - `/eng/`
- 🇪🇸 **Spanish** - `/esp/`
- 🇫🇷 **French** - `/fr/`

---

## Features

- **Validator statistics** - Live blockchain data via MultiversX API
- **Node status** - Real-time monitoring of 4 validator nodes
- **Staking information** - How to stake eGLD with Colombia Staking
- **Team presentation** - Meet the Colombia Staking team
- **Contact** - Telegram community links

---

## Structure

```
Website/
├── eng/           # English pages
├── esp/           # Spanish pages
├── fr/            # French pages
├── stats/         # Statistics & API
│   ├── node-status.html   # Live node status page
│   └── stats-api.php      # API for blockchain data
└── index.html     # Redirects to default language
```

---

## Node Monitoring

The website displays live node status from 4 validator nodes:

| Shard | IP | Node |
|-------|-----|------|
| 0 | 192.168.0.120 | Shard 0 |
| 1 | 192.168.0.121 | Shard 1 |
| 2 | 192.168.0.122 | Shard 2 |
| Metachain | 192.168.0.124 | Metachain |

**External nodes monitored:**
| Node | IP |
|------|-----|
| ExternalJuju | 176.160.237.59 |
| ChagnaieBlanc | 82.66.243.38 |
| ChagnaieNoir | 82.66.243.38 |

---

## Stats API

The `stats-api.php` fetches live data from MultiversX API:
- Total staked amount
- Number of validators
- Distribution statistics
- Node health

Data is cached and updated every 15 minutes via cron.

---

## Related Repos

| Repo | Purpose |
|------|---------|
| [DAPP-V3](https://github.com/colombiastaking/DAPP-V3) | Staking DApp |
| [btc-strategy](https://github.com/colombiastaking/btc-strategy) | BTC investment strategy |
| [tax-report-payment](https://github.com/colombiastaking/tax-report-payment) | Tax payment smart contract |
| [alice-backup](https://github.com/colombiastaking/alice-backup) | Alice backup & disaster recovery |

---

## Links

- **Website**: https://colombia-staking.com
- **DApp**: https://colombia-staking.com/dapp
- **Telegram (EN)**: https://t.me/ColombiaStakingChat
- **Telegram (ES)**: https://t.me/colombiastakingesp
- **Telegram (FR)**: https://t.me/colmbiastakingfr
- **Announcements**: https://t.me/ColombiaStakingAnn
