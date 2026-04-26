---
name: kepler-proxy
description: |
  Kepler Proxy - MultiversX API proxy for tax tools and blockchain queries.
  Use when: (1) starting/stopping the kepler-proxy service, (2) debugging proxy issues,
  (3) checking proxy health or endpoints, (4) restarting after reboot, (5) updating
  Cloudflare tunnel routes, or (6) any tax tool/blockchain API proxy tasks.
---

# Kepler Proxy Skill

MultiversX API proxy service running on port 3000 for tax tools and blockchain queries.

## Quick Reference

| Item | Value |
|------|-------|
| **File** | `~/.openclaw/kepler/kepler-proxy.js` |
| **Port** | 3000 |
| **API Key** | `acea534bc927840076692374ffab66fb` |
| **Target** | `kepler-api.projectx.mx` |
| **Service** | `kepler-proxy.service` (systemd) |
| **Health** | `http://localhost:3000/health` |

## Service Management

### Start Services
```bash
# Manual start (if systemd not enabled)
nohup node ~/.openclaw/kepler/kepler-proxy.js > /tmp/kepler-proxy.log 2>&1 &
sleep 1 && curl -s http://localhost:3000/health
```

### systemd Service
```bash
systemctl --user daemon-reload
systemctl --user enable kepler-proxy.service
systemctl --user start kepler-proxy.service
systemctl --user status kepler-proxy.service
```

### Cloudflare Tunnel
```bash
# Start tunnel manually
cloudflared --config ~/.cloudflared/config.yml tunnel run 6429a054-ec31-4f78-9b17-059e14ac58be

# Or via nohup
nohup cloudflared --config ~/.cloudflared/config.yml tunnel run 6429a054-ec31-4f78-9b17-059e14ac58be > /tmp/cloudflared.log 2>&1 &
```

### Verify Services
```bash
# Check health
curl http://localhost:3000/health

# Check all endpoints
curl http://localhost:3000/api/blocks/count
curl http://localhost:3000/gateway/network/config
curl http://localhost:3000/tax-query
curl http://localhost:3000/delegation
```

## Cloudflare Tunnel Config

**Config file:** `~/.cloudflared/config.yml`
**Tunnel ID:** `6429a054-ec31-4f78-9b17-059e14ac58be`
**Credentials:** `~/.cloudflared/credentials.json`

```yaml
tunnel: 6429a054-ec31-4f78-9b17-059e14ac58be
credentials-file: /home/raspberry/.cloudflared/credentials.json
protocol: http2

ingress:
  # Tax query endpoint - routes to kepler-proxy on port 3000
  - hostname: colombia-staking.co
    path: /tax-query
    service: http://localhost:3000

  # Delegation endpoint - routes to kepler-proxy on port 3000
  - hostname: colombia-staking.co
    path: /delegation
    service: http://localhost:3000

  # API endpoints - routes to kepler-proxy on port 3000
  - hostname: colombia-staking.co
    path: /api
    service: http://localhost:3000

  # Gateway endpoints - routes to kepler-proxy on port 3000
  - hostname: colombia-staking.co
    path: /gateway
    service: http://localhost:3000

  # Elasticsearch endpoints - routes to kepler-proxy on port 3000
  - hostname: colombia-staking.co
    path: /es
    service: http://localhost:3000

  # Default fallback
  - service: http://localhost:3000
```

**⚠️ Common Issue:** Previously misconfigured to route `/tax-query` and `/delegation` to port 3001 (didn't exist). Fixed to route all to port 3000 where kepler-proxy handles them.

## Troubleshooting

### Service Won't Start
1. Check if port 3000 is in use: `lsof -i :3000`
2. Check logs: `tail -f /tmp/kepler-proxy.log`
3. Verify file exists: `ls -la ~/.openclaw/kepler/kepler-proxy.js`

### Cloudflare 502/504 Errors
1. Verify kepler-proxy is running: `curl localhost:3000/health`
2. Check Cloudflare logs: `tail -f /tmp/cloudflared.log`
3. Verify routes in `~/.cloudflared/config.yml` point to port 3000

### Reboot Recovery
On reboot, either:
1. Enable systemd service: `systemctl --user enable kepler-proxy.service`
2. Or add to crontab @reboot: `@reboot nohup node ~/.openclaw/kepler/kepler-proxy.js &`

## External Access

Public endpoints via `https://colombia-staking.co`:
- `https://colombia-staking.co/api/blocks/count`
- `https://colombia-staking.co/gateway/network/config`
- `https://colombia-staking.co/es/transactions/_search`
- `https://colombia-staking.co/tax-query`
- `https://colombia-staking.co/delegation`
