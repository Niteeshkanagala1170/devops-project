#!/bin/bash
# LinuxOps Monitor - Unified Execution Wrapper
# Serves as the master script run by cron, orchestrating monitor.py and log_scan.sh.

# Get current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCIDENTS_LOG="${SCRIPT_DIR}/incidents.log"

echo "========================================================================"
echo "      LINUXOPS MONITOR - MASTER HEALTH CHECK RUN"
echo "      Start Time: $(date "+%Y-%m-%d %H:%M:%S")"
echo "========================================================================"

# Track incidents count before running scripts
INITIAL_ALERTS=0
if [ -f "$INCIDENTS_LOG" ]; then
    INITIAL_ALERTS=$(wc -l < "$INCIDENTS_LOG")
fi

# 1. Run Python System Metrics Monitor
echo "Executing system metrics health check..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[CRITICAL ERROR] Python is not installed or not in PATH."
    exit 1
fi

$PYTHON_CMD "${SCRIPT_DIR}/monitor.py"
echo ""

# 2. Run Log Scanner
echo "Executing log file patterns scanner..."
if [ -f "${SCRIPT_DIR}/log_scan.sh" ]; then
    # Ensure it's executable
    chmod +x "${SCRIPT_DIR}/log_scan.sh"
    bash "${SCRIPT_DIR}/log_scan.sh"
else
    echo "[CRITICAL ERROR] log_scan.sh not found in ${SCRIPT_DIR}."
    exit 1
fi
echo ""

# 3. Check for any newly logged incidents
FINAL_ALERTS=0
if [ -f "$INCIDENTS_LOG" ]; then
    FINAL_ALERTS=$(wc -l < "$INCIDENTS_LOG")
fi

NEW_INCIDENTS_COUNT=$((FINAL_ALERTS - INITIAL_ALERTS))

echo "========================================================================"
echo "      HEALTH CHECK COMPLETED AT $(date "+%Y-%m-%d %H:%M:%S")"
if [ "$NEW_INCIDENTS_COUNT" -gt 0 ]; then
    echo "      ALERT: ${NEW_INCIDENTS_COUNT} new incident(s) appended to incidents.log!"
    echo "      --- Last ${NEW_INCIDENTS_COUNT} line(s) of incidents.log ---"
    tail -n "$NEW_INCIDENTS_COUNT" "$INCIDENTS_LOG" | sed 's/^/      /g'
else
    echo "      STATUS: Healthy. No new incident alerts logged."
fi
echo "========================================================================"
