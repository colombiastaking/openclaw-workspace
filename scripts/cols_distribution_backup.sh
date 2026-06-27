#!/bin/bash
#
# COLS Distribution Backup Runner
# Checks if GOLD/DAO were already sent today before re-running.
# Used by backup cron jobs at 13:15 (GOLD) and 13:20 (DAO).
#

SCRIPTS_DIR="/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/scripts"
STATE_FILE="/tmp/cols_distribution/state.json"
GOLD_STATE_FILE="/tmp/cols_distribution/gold_state.json"
LOG_FILE="/tmp/cols_distribution_cron.log"
TODAY=$(date +%Y-%m-%d)

cd "$SCRIPTS_DIR" || exit 1

run_gold() {
    if [ -f "$GOLD_STATE_FILE" ]; then
        local gold_date
        gold_date=$(node -e "console.log(require('fs').readFileSync('$GOLD_STATE_FILE','utf8').trim() ? JSON.parse(require('fs').readFileSync('$GOLD_STATE_FILE','utf8')).lastDistributionDate : '')")
        if [ "$gold_date" = "$TODAY" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🥇 GOLD already distributed today ($TODAY), skipping backup run" | tee -a "$LOG_FILE"
            return 0
        fi
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🥇 GOLD backup run starting..." | tee -a "$LOG_FILE"
    node execute_gold_distribution.cjs --force >> "$LOG_FILE" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🥇 GOLD backup run finished (exit $?)" | tee -a "$LOG_FILE"
}

run_dao() {
    if [ -f "$STATE_FILE" ]; then
        local dao_date
        dao_date=$(node -e "try { const s=JSON.parse(require('fs').readFileSync('$STATE_FILE','utf8')); console.log(s.lastDistributionDate || ''); } catch(e) { console.log(''); }")
        local dao_hash
        dao_hash=$(node -e "try { const s=JSON.parse(require('fs').readFileSync('$STATE_FILE','utf8')); console.log(s.lastDaoHash || ''); } catch(e) { console.log(''); }")
        if [ "$dao_date" = "$TODAY" ] && [ -n "$dao_hash" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🏛️ DAO already distributed today ($TODAY), skipping backup run" | tee -a "$LOG_FILE"
            return 0
        fi
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🏛️ DAO backup run starting..." | tee -a "$LOG_FILE"
    node execute_distribution_fixed.cjs --dao --force >> "$LOG_FILE" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🏛️ DAO backup run finished (exit $?)" | tee -a "$LOG_FILE"
}

case "$1" in
    gold)
        run_gold
        ;;
    dao)
        run_dao
        ;;
    *)
        echo "Usage: $0 {gold|dao}"
        exit 1
        ;;
esac
