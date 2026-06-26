# Heartbeat Checklist

Rotate through these checks 2-4x/day. **Do not re-run the BTC daily report from the heartbeat** — it is handled by the 8:00 AM system cron. Only check `/tmp/btc_daily_report.log` and alert if the cron run failed or produced bad data.

## Morning (8-10 AM)
- [ ] Node status check
- [ ] System resources (CPU/disk/memory)
- [ ] Git status - any uncommitted changes?

## Midday (12-2 PM)
- [ ] Memory maintenance - review recent notes
- [ ] Project status checks

## Evening (6-8 PM)
- [ ] Node monitoring summary
- [ ] Backup verification
- [ ] Plan tomorrow if needed

## When to reach out:
- Node alerts or downtime
- Disk space > 80%
- Unusual system behavior
- Important calendar events in next 2h
- BTC report cron failed or delivered bad MVRV/score
