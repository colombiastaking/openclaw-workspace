# Alice Automation - Cron Jobs

All scheduled tasks for Alice. Documented: 2026-03-28, last updated: 2026-04-16

---

## OpenClaw Cron Jobs (5 jobs)

Managed via: `openclaw cron list`

| Name | Schedule | Purpose |
|------|----------|---------|
| `node-alert-check` | `0 * * * *` (hourly) | Economic monitoring - ADD/REMOVE node analysis |
| `alice-daily-backup` | `0 18 * * *` (6 PM) | Full backup to GitHub |
| `Daily Strategy Report` | `0 8 * * *` (8 AM) | BTC strategy report + Aave position |
| `daily-distribution-execution` | `10 13 * * *` (1:10 PM) | COLS: Phase1 exec → Phase2 verify → Phase3 resend |
| `daily-distribution-summary` | `15 13 * * *` (1:15 PM) | Post COLS distribution summary to group |

### Script Paths

| Job | Script |
|-----|--------|
| `node-alert-check` | `/home/raspberry/.openclaw/workspace/node-monitor/node_monitor.py` |
| `alice-daily-backup` | `/home/raspberry/alice-backup/backup.sh` |
| `Daily Strategy Report` | `/home/raspberry/.openclaw/workspace/btc-monitor/daily_strategy_report.py` |
| `daily-distribution-execution` | `/home/raspberry/.openclaw/workspace/scripts/run_distribution_cron.sh` + verify + resend scripts |
| `daily-distribution-summary` | Reads verification JSONs from `/tmp/cols_distribution/` |

---

## System Crontab (6 jobs)

Managed via: `crontab -e` (user crontab)

```
# External node TCP monitoring (every 15 min)
*/15 * * * * /home/raspberry/external-ip-monitor.sh >> /tmp/external-ip-monitor.log 2>&1

# Health monitoring (every 15 min)
*/15 * * * * /home/raspberry/node_monitor_full.sh >> /tmp/node_monitor_full.log 2>&1

# Daily IP check (midnight)
0 0 * * * /home/raspberry/daily_ip.sh

# Plugin updates (Sunday 4 AM)
0 4 * * * openclaw plugins update @martian-engineering/lossless-claw >> /tmp/lossless-claw-update.log 2>&1

# Agent-browser install (Sunday 5 AM)
0 5 * * 0 npm install -g agent-browser >> /tmp/agent-browser-update.log 2>&1
0 5 * * 0 agent-browser install --force >> /tmp/agent-browser-chromium.log 2>&1
```

### External IP Monitor Nodes

| Node | IP | Port | Purpose |
|------|-----|------|---------|
| Shard0 | 192.168.0.120 | 55332 | Validator |
| Shard1 | 192.168.0.121 | 55336 | Validator |
| Shard2 | 192.168.0.122 | 55333 | Validator |
| Metachain | 192.168.0.124 | 55338 | Validator |
| ChagnaieBlanc | 82.66.243.38 | 55332 | External |
| ChagnaieNoir | 82.66.243.38 | 55333 | External |
| ExternalJuju | 176.160.237.59 | 55334 | Backup (disabled 2026-04-14) |

---

## Systemd User Services (3)

Located: `~/.config/systemd/user/`

| Service | Purpose | Status |
|---------|---------|--------|
| `kepler-proxy.service` | MultiversX API proxy for tax tool (port 3000) | ✅ |
| `openclaw-gateway.service` | OpenClaw gateway daemon | ✅ |
| `cloudflared-tunnel.service` | Cloudflare tunnel for colombia-staking.co | ✅ |

### Commands

```bash
# Check status
systemctl --user status kepler-proxy.service
systemctl --user status openclaw-gateway.service
systemctl --user status cloudflared-tunnel.service

# Restart
systemctl --user restart kepler-proxy.service
systemctl --user restart openclaw-gateway.service
systemctl --user restart cloudflared-tunnel.service

# View logs
journalctl --user -u kepler-proxy.service -f
```

---

## Pushover Notifications

Alerts sent via Pushover (token/user in `~/.openclaw/.secrets/monitoring.env`)

| Script | Trigger | Alert |
|--------|---------|-------|
| `external-ip-monitor.sh` | 2 consecutive failures (30 min) | Node DOWN |
| `node_monitor_full.sh` | DOWN, DESYNC, low peers | Pushover + Website |
| `daily_ip.sh` | Daily at midnight | Public IP change |

---

## File Locations

- **Scripts:** `/home/raspberry/external-ip-monitor.sh`, `/home/raspberry/node_monitor_full.sh`, `/home/raspberry/daily_ip.sh`
- **Node Monitor:** `/home/raspberry/.openclaw/workspace/node-monitor/node_monitor.py`
- **Aave Monitor:** `/home/raspberry/.openclaw/workspace/aave-monitor/`
- **BTC Monitor:** `/home/raspberry/.openclaw/workspace/btc-monitor/`
- **Kepler Proxy:** `/home/raspberry/.openclaw/kepler/kepler-proxy.js`
- **COLS Distribution:** `/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/scripts/`
- **Backup:** `/home/raspberry/alice-backup/backup.sh`