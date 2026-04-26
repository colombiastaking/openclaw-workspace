#!/bin/bash
# CPU and RAM monitoring script
# Run hourly and log to file

LOG_FILE="/home/raspberry/.openclaw/workspace/memory/system_stats.log"

# Get timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Get CPU usage (using top -bn1 for snapshot)
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

# Alternative method using /proc/stat
if [ -z "$CPU" ]; then
    CPU=$(awk '/^cpu / {usage=($2+$4)*100/($2+$4+$5)} END {print usage}' /proc/stat)
fi

# Get RAM usage
RAM_TOTAL=$(free -m | awk '/^Mem:/{print $2}')
RAM_USED=$(free -m | awk '/^Mem:/{print $3}')
RAM_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($RAM_USED/$RAM_TOTAL)*100}")

# Get Load Average
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

# Get temperature if available
TEMP=""
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)
    TEMP=" | Temp: ${TEMP}°C"
fi

# Log to file
echo "${TIMESTAMP} | CPU: ${CPU}% | RAM: ${RAM_USED}MB/${RAM_TOTAL}MB (${RAM_PERCENT}%) | Load: ${LOAD}${TEMP}" >> "$LOG_FILE"

# Also output to console
echo "${TIMESTAMP} | CPU: ${CPU}% | RAM: ${RAM_USED}MB/${RAM_TOTAL}MB (${RAM_PERCENT}%) | Load: ${LOAD}${TEMP}"
