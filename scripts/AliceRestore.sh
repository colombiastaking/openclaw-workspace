#!/bin/bash
#==============================================================================
# Alice Full Restore Script
# Purpose: Rebuild Alice from scratch using GitHub backup in < 10 minutes
# Usage: bash AliceRestore.sh [alice-backup-dir]
#==============================================================================

set -e

OPENCLAW_DIR="/home/raspberry/.openclaw"
WORKSPACE="$OPENCLAW_DIR/workspace"
BACKUP_REPO="https://github.com/colombiastaking/alice-backup"
PASSWORD_FILE="$OPENCLAW_DIR/alice-backup/.backup_password"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════"
echo -e "  🏛️  ALICE FULL RESTORE"
echo -e "  $(date '+%Y-%m-%d %H:%M')"
echo -e "═══════════════════════════════════════════════════════════════════${NC}"
echo ""

#------------------------------------------------------------------------------
# STEP 0: Check if already installed
#------------------------------------------------------------------------------
if systemctl --user is-active openclaw-gateway.service &>/dev/null; then
    echo -e "${YELLOW}⚠️  OpenClaw gateway is already running.${NC}"
    read -p "Continue anyway? (y/N): " confirm
    [[ "$confirm" != "y" ]] && exit 0
fi

#------------------------------------------------------------------------------
# STEP 1: Get password
#------------------------------------------------------------------------------
if [[ -f "$PASSWORD_FILE" ]]; then
    BACKUP_PWD=$(cat "$PASSWORD_FILE")
    echo -e "${GREEN}✅ Backup password loaded from $PASSWORD_FILE${NC}"
elif [[ -n "$RESTORE_PASSWORD" ]]; then
    BACKUP_PWD="$RESTORE_PASSWORD"
    echo -e "${GREEN}✅ Backup password loaded from RESTORE_PASSWORD env${NC}"
else
    echo -e "${YELLOW}⚠️  No .backup_password found.${NC}"
    echo "  This is expected on FIRST RUN of a fresh install."
    echo "  The script will use default password 'AliceRestore2026' for initial clone."
    echo "  If the repo was encrypted with a different password, set RESTORE_PASSWORD env."
    BACKUP_PWD="AliceRestore2026"
fi

#------------------------------------------------------------------------------
# STEP 2: Clone / update alice-backup repo
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📦 STEP 1: Cloning alice-backup repository...${NC}"

BACKUP_DIR="$OPENCLAW_DIR/alice-backup"
if [[ -d "$BACKUP_DIR/.git" ]]; then
    echo "  📍 Repo already exists — pulling latest..."
    cd "$BACKUP_DIR" && git pull origin main
else
    echo "  📍 Cloning fresh..."
    git clone "$BACKUP_REPO" "$BACKUP_DIR"
    cd "$BACKUP_DIR"
fi

# Try to decrypt with provided password; if fail, try defaults
decrypt_file() {
    local src="$1"
    local dst="$2"
    local pwd="${3:-$BACKUP_PWD}"
    
    # Try current password first, then fallback passwords
    for try_pwd in "$pwd" "AliceRestore2026" "iVP6!fphj@" ""; do
        if [[ -z "$try_pwd" ]]; then
            echo -e "    ❌ Cannot decrypt $src — no more passwords to try"
            return 1
        fi
        if openssl enc -aes-256-cbc -d -salt -pbkdf2 -in "$src" -pass "pass:$try_pwd" -out "$dst" 2>/dev/null; then
            echo -e "    ✅ Decrypted $src"
            return 0
        fi
    done
    echo -e "    ❌ Failed to decrypt $src with any password"
    return 1
}

#------------------------------------------------------------------------------
# STEP 3: Restore openclaw.json
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🔧 STEP 2: Restoring OpenClaw configuration...${NC}"

if [[ -f "$BACKUP_DIR/alice_config.enc" ]]; then
    decrypt_file "$BACKUP_DIR/alice_config.enc" "/tmp/alice_config.json" && \
        cp /tmp/alice_config.json "$OPENCLAW_DIR/openclaw.json" && \
        echo -e "    ✅ openclaw.json restored" || \
        echo -e "    ❌ Failed — copy openclaw.json.bak manually"
fi

#------------------------------------------------------------------------------
# STEP 4: Restore .env (all secrets)
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🔑 STEP 3: Restoring secrets (.env)...${NC}"

if [[ -f "$BACKUP_DIR/alice_env.enc" ]]; then
    decrypt_file "$BACKUP_DIR/alice_env.enc" "$OPENCLAW_DIR/.env" && \
        echo -e "    ✅ .env restored" || \
        echo -e "    ❌ Failed"
fi

#------------------------------------------------------------------------------
# STEP 5: Restore credentials (FTP, cPanel tokens)
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📂 STEP 4: Restoring credentials...${NC}"

mkdir -p "$OPENCLAW_DIR/secrets"

if [[ -f "$BACKUP_DIR/credentials.tar.enc" ]]; then
    TEMP_CREDS="/tmp/creds_restore.tar"
    decrypt_file "$BACKUP_DIR/credentials.tar.enc" "$TEMP_CREDS" && \
        tar -xf "$TEMP_CREDS" -C ~ && \
        echo -e "    ✅ credentials restored (~/.openclaw/secrets, ~/.telegram)" || \
        echo -e "    ❌ Failed"
    rm -f "$TEMP_CREDS"
fi

# Restore individual FTP credentials
if [[ -f "$BACKUP_DIR/secrets/.ftp_credentials" ]]; then
    mkdir -p "$OPENCLAW_DIR/secrets"
    cp "$BACKUP_DIR/secrets/.ftp_credentials" "$OPENCLAW_DIR/secrets/"
    echo -e "    ✅ FTP credentials restored"
fi

#------------------------------------------------------------------------------
# STEP 6: Restore wallet
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}💰 STEP 5: Restoring wallet...${NC}"

mkdir -p "$OPENCLAW_DIR/wallet"

if [[ -f "$BACKUP_DIR/wallet.tar.enc" ]]; then
    TEMP_WALLET="/tmp/wallet_restore.tar"
    if decrypt_file "$BACKUP_DIR/wallet.tar.enc" "$TEMP_WALLET"; then
        tar -xf "$TEMP_WALLET" -C "$OPENCLAW_DIR" && \
            echo -e "    ✅ wallet restored" || \
            echo -e "    ❌ wallet.tar extract failed"
        rm -f "$TEMP_WALLET"
    fi
fi

# Fallback: if wallet.tar.enc fails, check for raw hex key in memory
if [[ ! -s "$OPENCLAW_DIR/wallet/.private_key" ]] || [[ $(wc -c < "$OPENCLAW_DIR/wallet/.private_key") -lt 64 ]]; then
    echo -e "    ⚠️  Wallet file missing or invalid."
    echo -e "    ⚠️  You may need to restore manually from raw hex key."
    echo -e "    ⚠️  [KEY IN wallet_raw.enc - decrypt first]"
fi

#------------------------------------------------------------------------------
# STEP 7: Restore mcporter config
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🔗 STEP 6: Restoring MCP MultiversX server config...${NC}"

mkdir -p ~/.mcporter

if [[ -f "$BACKUP_DIR/mcporter-config.enc" ]]; then
    decrypt_file "$BACKUP_DIR/mcporter-config.enc" ~/.mcporter/mcporter.json && \
        echo -e "    ✅ mcporter.json restored" || \
        echo -e "    ❌ Failed"
fi

#------------------------------------------------------------------------------
# STEP 8: Restore cloudflared tunnel
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🌐 STEP 7: Restoring Cloudflare tunnel...${NC}"

mkdir -p ~/.cloudflared

if [[ -f "$BACKUP_DIR/cloudflared-credentials.enc" ]]; then
    decrypt_file "$BACKUP_DIR/cloudflared-credentials.enc" ~/.cloudflared/credentials.json && \
        echo -e "    ✅ cloudflared credentials.json restored" || \
        echo -e "    ❌ Failed"
fi

if [[ -f "$BACKUP_DIR/cloudflared-config.enc" ]]; then
    decrypt_file "$BACKUP_DIR/cloudflared-config.enc" ~/.cloudflared/config.yml && \
        echo -e "    ✅ cloudflared config.yml restored" || \
        echo -e "    ❌ Failed"
fi

#------------------------------------------------------------------------------
# STEP 9: Restore memory files
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🧠 STEP 8: Restoring memory & workspace files...${NC}"

mkdir -p "$WORKSPACE/memory"

if [[ -f "$BACKUP_DIR/memory.tar.enc" ]]; then
    TEMP_MEM="/tmp/memory_restore.tar"
    if decrypt_file "$BACKUP_DIR/memory.tar.enc" "$TEMP_MEM"; then
        tar -xf "$TEMP_MEM" -C "$WORKSPACE" && \
            echo -e "    ✅ memory restored" || \
            echo -e "    ❌ Failed"
        rm -f "$TEMP_MEM"
    fi
fi

# Restore key identity files
for file in AGENTS.md SOUL.md USER.md MEMORY.md TOOLS.md IDENTITY.md HEARTBEAT.md RESTORE.md; do
    if [[ -f "$BACKUP_DIR/$file" ]]; then
        cp "$BACKUP_DIR/$file" "$WORKSPACE/" && echo -e "    ✅ $file" || true
    fi
done

#------------------------------------------------------------------------------
# STEP 10: Restore Google / Microsoft tokens
#------------------------------------------------------------------------------
if [[ -f "$BACKUP_DIR/google-tokens.enc" ]]; then
    decrypt_file "$BACKUP_DIR/google-tokens.enc" "$WORKSPACE/google-tokens.json" && \
        echo -e "    ✅ google-tokens.json restored" || \
        echo -e "    ❌ Failed"
fi

#------------------------------------------------------------------------------
# STEP 11: Restore crontab
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}⏰ STEP 9: Restoring crontab...${NC}"

if [[ -f "$BACKUP_DIR/crontab.txt" ]]; then
    crontab "$BACKUP_DIR/crontab.txt" && \
        echo -e "    ✅ crontab restored" || \
        echo -e "    ❌ Failed"
fi

# Also restore system crontab if exists
if [[ -f "$BACKUP_DIR/raspberry-crontab.txt" ]]; then
    sudo crontab "$BACKUP_DIR/raspberry-crontab.txt" 2>/dev/null && \
        echo -e "    ✅ system crontab restored" || \
        echo -e "    ⚠️  system crontab restore skipped (needs sudo)"
fi

#------------------------------------------------------------------------------
# STEP 12: Restore skills
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🛠️  STEP 10: Installing OpenClaw skills...${NC}"

cd "$WORKSPACE"
if command -v openclaw &>/dev/null; then
    # Install all skills from the skills directory
    if [[ -d "$BACKUP_DIR/.agents/skills" ]]; then
        for skill_dir in "$BACKUP_DIR"/.agents/skills/*/; do
            skill_name=$(basename "$skill_dir")
            echo -e "    📦 Installing skill: $skill_name"
            openclaw skills install "$skill_name" 2>/dev/null || \
                echo -e "    ⚠️  $skill_name install failed (may need manual)"
        done
    fi
    
    # Try installing from ClawHub
    echo -e "    📦 Syncing ClawHub skills..."
    openclaw skills sync 2>/dev/null || true
else
    echo -e "    ⚠️  openclaw CLI not found — skipping skills install"
    echo -e "    ⚠️  Install OpenClaw first, then run: openclaw skills sync"
fi

#------------------------------------------------------------------------------
# STEP 13: Restore NPM packages (alice-mcp-multiversx)
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📦 STEP 11: Installing NPM packages...${NC}"

MCP_DIR="$WORKSPACE/alice-mcp-multiversx"
if [[ -d "$MCP_DIR" ]]; then
    cd "$MCP_DIR" && npm install --legacy-peer-deps 2>&1 | tail -3 && \
        npm run build 2>&1 | tail -3 && \
        echo -e "    ✅ alice-mcp-multiversx built" || \
        echo -e "    ⚠️  Build failed — check errors above"
else
    echo -e "    ⚠️  alice-mcp-multiversx not in backup — clone it"
fi

#------------------------------------------------------------------------------
# STEP 14: Restore systemd services
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🚀 STEP 12: Installing systemd services...${NC}"

mkdir -p ~/.config/systemd/user

for svc in kepler-proxy cloudflared-tunnel dapp-server btc-general-report; do
    if [[ -f "$BACKUP_DIR/systemd/${svc}.service" ]]; then
        cp "$BACKUP_DIR/systemd/${svc}.service" ~/.config/systemd/user/
        systemctl --user daemon-reload 2>/dev/null
        echo -e "    ✅ ${svc}.service installed"
    fi
done

#------------------------------------------------------------------------------
# STEP 15: Start services
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}▶️  STEP 13: Starting services...${NC}"

# Restart OpenClaw gateway
if command -v openclaw &>/dev/null; then
    openclaw gateway restart 2>/dev/null && \
        echo -e "    ✅ OpenClaw gateway restarted" || \
        openclaw gateway start 2>/dev/null && \
        echo -e "    ✅ OpenClaw gateway started"
fi

# Start cloudflared tunnel
if systemctl --user is-active cloudflared-tunnel.service &>/dev/null; then
    systemctl --user restart cloudflared-tunnel && echo -e "    ✅ cloudflared restarted"
else
    systemctl --user start cloudflared-tunnel && echo -e "    ✅ cloudflared started"
fi

# Start kepler-proxy
if systemctl --user is-active kepler-proxy.service &>/dev/null; then
    systemctl --user restart kepler-proxy && echo -e "    ✅ kepler-proxy restarted"
else
    systemctl --user start kepler-proxy && echo -e "    ✅ kepler-proxy started"
fi

# Start node monitors
~/node_monitor_full.sh &>/dev/null &
~/external-ip-monitor.sh &>/dev/null &
echo -e "    ✅ Node monitors started"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════"
echo -e "  ✅ RESTORE COMPLETE"
echo -e "═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Check status:   openclaw gateway status"
echo "  2. Verify services: systemctl --user status kepler-proxy"
echo "  3. Test Telegram:  Send a message to your bot"
echo ""
echo "If anything failed, check the error messages above."
echo "For wallet issues: restore manually using raw hex key from MEMORY.md"
