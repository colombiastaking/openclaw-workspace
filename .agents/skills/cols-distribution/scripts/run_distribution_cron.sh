#!/bin/bash
#
# COLS Daily Distribution - Cron Version (Non-Interactive)
# Runs at 1:10 PM Colombia time, before notification at 1:15 PM
#

set -e

SCRIPTS_DIR="/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/scripts"
OUTPUT_DIR="/tmp/cols_distribution"
LOG_FILE="/tmp/cols_distribution_cron.log"

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

# Step 4: Execute distribution on blockchain (always force to ensure daily distribution)
# NOTE: Using fixed version with on-chain verification
log "🚀 Executing distribution on blockchain (FIXED VERSION with verification)..."
node execute_distribution_fixed.cjs --all --force 2>&1 | tee -a "$LOG_FILE"
log "✅ Distribution executed"

# Step 5: Execute GOLD distribution
log "🥇 Executing GOLD distribution..."
node execute_gold_distribution.cjs 2>&1 | tee -a "$LOG_FILE"
log "✅ GOLD distribution executed"

log "═══════════════════════════════════════════════════════════════"
log "Daily distribution complete!"
log "Notification will be posted at 1:15 PM"
log "═══════════════════════════════════════════════════════════════"
