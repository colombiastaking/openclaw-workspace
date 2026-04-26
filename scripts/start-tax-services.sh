#!/bin/bash
# Start Tax Tool services on Pi boot

echo "Starting Tax Tool services..."

# Cloudflared tunnel
echo "  Starting cloudflared tunnel..."
nohup cloudflared --config /home/raspberry/.cloudflared/config.yml tunnel run 6429a054-ec31-4f78-9b17-059e14ac58be > /tmp/cloudflared.log 2>&1 &
sleep 3

# Kepler proxy (port 3000)
echo "  Starting kepler-proxy (port 3000)..."
nohup node /home/raspberry/.openclaw/kepler/kepler-proxy.js > /tmp/kepler-proxy.log 2>&1 &
sleep 1

# Verify
sleep 2
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "  ✅ All services running"
else
    echo "  ⚠️ Some services may not have started properly"
fi
