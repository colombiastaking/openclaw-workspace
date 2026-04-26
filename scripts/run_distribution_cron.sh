#!/bin/bash
#
# COLS Daily Distribution - Cron Version (Non-Interactive)
# Runs at 1:10 PM Colombia time, before notification at 1:15 PM
#
# KEY FIX: Each pool runs INDEPENDENTLY
# - BONUS/GOLD/DAO all check their own conditions
# - One failing does NOT block the others
# - No "set -e" which would exit on first error
#

SCRIPTS_DIR="/home/raspberry/.openclaw/workspace/DAPP-V3/scripts"
OUTPUT_DIR="/tmp/cols_distribution"
LOG_FILE="/tmp/cols_distribution_cron.log"
TODAY=$(date +%Y-%m-%d)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════════════════════════"
log "COLS Daily Distribution - CRON JOB"
log "═══════════════════════════════════════════════════════════════"

cd "$SCRIPTS_DIR"

# Step 1: Fetch COLS stakers
log "📥 Fetching COLS stakers..."
node fetch_cols_stakers.mjs 2>&1 | tee -a "$LOG_FILE"
log "✅ Fetch complete"

# Step 2: Calculate BONUS distribution  
log "💰 Calculating BONUS distribution..."
node daily_distribution.mjs --recalc 2>&1 | tee -a "$LOG_FILE"
log "✅ BONUS calculation complete"

# Step 3: Calculate GOLD distribution
log "🥇 Calculating GOLD distribution..."
node calculate_gold_distribution.mjs 2>&1 | tee -a "$LOG_FILE"
log "✅ GOLD calculation complete"

# Step 4: Execute BONUS first, wait for completion, then GOLD (SEQUENTIALLY)
# IMPORTANT: BONUS and GOLD must NOT run in parallel — they share the same wallet nonce,
# causing GOLD txs to fail with lowerNonceInTx if BONUS is running concurrently.
log "🚀 Executing BONUS distribution (background)..."
node execute_distribution_fixed.cjs --bonus --force >> "$LOG_FILE" 2>&1 &
BONUS_PID=$!
log "   BONUS PID: $BONUS_PID"

# Wait for BONUS to finish (don't use set -e - we want to continue even if BONUS fails)
log "⏳ Waiting for BONUS to complete..."
wait $BONUS_PID
BONUS_EXIT=$?
log "   BONUS PID $BONUS_PID exited: code $BONUS_EXIT"

# Step 5: Execute GOLD AFTER BONUS (check if distribution file exists, not if BONUS succeeded)
if [ -f "$OUTPUT_DIR/gold_distribution_$TODAY.json" ]; then
    log "🥇 Executing GOLD distribution..."
    node execute_gold_distribution.cjs --force >> "$LOG_FILE" 2>&1
    GOLD_EXIT=$?
    if [ $GOLD_EXIT -eq 0 ]; then
        log "   ✅ GOLD distribution succeeded"
    else
        log "   ⚠️  GOLD exited with code $GOLD_EXIT (will retry manually if needed)"
    fi
else
    log "   ⏭️  No GOLD distribution file found, skipping"
    GOLD_EXIT=99
fi

# Step 6: Execute DAO INDEPENDENTLY
# DAO is completely separate from BONUS/GOLD user distributions
# It goes to the PeerMe contract, not to user wallets
# Run it even if BONUS/GOLD had issues
log "🚀 Executing DAO distribution..."
node execute_distribution_fixed.cjs --dao --force >> "$LOG_FILE" 2>&1
DAO_EXIT=$?
if [ $DAO_EXIT -eq 0 ]; then
    log "   ✅ DAO distribution succeeded"
else
    log "   ⚠️  DAO exited with code $DAO_EXIT"
fi

log "═══════════════════════════════════════════════════════════════"
log "Daily distribution complete!"
log "BONUS: exit $BONUS_EXIT | GOLD: exit $GOLD_EXIT | DAO: exit $DAO_EXIT"
log "Notification will be posted at 1:35 PM"
log "═══════════════════════════════════════════════════════════════"
