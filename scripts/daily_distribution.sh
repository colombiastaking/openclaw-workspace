#!/bin/bash
#
# COLS Daily Distribution - Full Automation
# Runs BONUS + GOLD calculations and executes distribution
#

set -e

SCRIPTS_DIR="/home/raspberry/.openclaw/workspace/DAPP-V3/scripts"
OUTPUT_DIR="/tmp/cols_distribution"
LOG_FILE="/tmp/cols_distribution_full.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════════════════════════"
log "COLS Daily Distribution Starting"
log "═══════════════════════════════════════════════════════════════"

cd "$SCRIPTS_DIR"

# Step 1: Fetch COLS stakers
log "📥 Step 1: Fetching COLS stakers..."
node fetch_cols_stakers.mjs 2>&1 | tee -a "$LOG_FILE"
log "✅ Fetch complete"

# Step 2: Calculate BONUS distribution
log "💰 Step 2: Calculating BONUS distribution..."
node daily_distribution.mjs --recalc 2>&1 | tee -a "$LOG_FILE"
log "✅ BONUS calculation complete"

# Step 3: Calculate GOLD distribution
log "🥇 Step 3: Calculating GOLD distribution..."
node calculate_gold_distribution.mjs 2>&1 | tee -a "$LOG_FILE"
log "✅ GOLD calculation complete"

# Step 4: Show summary
log "📊 Distribution Summary:"
TODAY=$(date +%Y-%m-%d)
if [ -f "$OUTPUT_DIR/bonus_distribution_$TODAY.json" ]; then
    BONUS=$(cat "$OUTPUT_DIR/bonus_distribution_$TODAY.json" | node -p "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).bonus.totalBonus.toFixed(6)")
    COUNT=$(cat "$OUTPUT_DIR/bonus_distribution_$TODAY.json" | node -p "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).bonus.recipients.length")
    log "   BONUS: $BONUS COLS to $COUNT addresses"
fi
if [ -f "$OUTPUT_DIR/gold_distribution_$TODAY.json" ]; then
    GOLD=$(cat "$OUTPUT_DIR/gold_distribution_$TODAY.json" | node -p "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).totalCols.toFixed(6)")
    GCOUNT=$(cat "$OUTPUT_DIR/gold_distribution_$TODAY.json" | node -p "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).recipients.length")
    log "   GOLD: $GOLD COLS to $GCOUNT addresses"
fi

log "═══════════════════════════════════════════════════════════════"
log "Distribution calculation complete!"
log "Executing distribution..."

# Execute the distribution (auto-confirm with yes)
echo "yes" | ./run_distribution.sh execute --force 2>&1 | tee -a "$LOG_FILE"

log "═══════════════════════════════════════════════════════════════"
log "Distribution complete!"
log "═══════════════════════════════════════════════════════════════"
