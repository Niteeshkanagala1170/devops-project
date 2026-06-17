#!/bin/bash
# LinuxOps Monitor - Log Scanner
# Scans system log files for critical errors and auth failures.
# Appends findings to incidents.log and outputs summaries.

# Get current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCIDENTS_LOG="${SCRIPT_DIR}/incidents.log"
HOSTNAME=$(hostname)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Default target files
SYSLOG="/var/log/syslog"
AUTHLOG="/var/log/auth.log"

# Mock fallbacks for non-Linux or local development testing
MOCK_SYSLOG="${SCRIPT_DIR}/mock_syslog.log"
MOCK_AUTHLOG="${SCRIPT_DIR}/mock_auth.log"

# Define patterns to search (grep expressions)
SYSLOG_PATTERNS="error|failed|CRITICAL|warning"
AUTHLOG_PATTERNS="Failed password|Invalid user|security error|fatal"

echo "========================================="
echo "LOG SCANNER REPORT - ${TIMESTAMP}"
echo "========================================="

# ---------------------------------------------------------
# Syslog Scan
# ---------------------------------------------------------
TARGET_SYSLOG=""
USING_MOCK_SYSLOG=0

if [ -f "$SYSLOG" ]; then
    # Verify read permission
    if [ -r "$SYSLOG" ]; then
        TARGET_SYSLOG="$SYSLOG"
    else
        echo "[WARNING] Permission denied to read $SYSLOG. Trying mock fallback."
    fi
fi

if [ -z "$TARGET_SYSLOG" ]; then
    if [ -f "$MOCK_SYSLOG" ]; then
        TARGET_SYSLOG="$MOCK_SYSLOG"
        USING_MOCK_SYSLOG=1
    else
        echo "[INFO] Syslog file not found: $SYSLOG (and no mock file at $MOCK_SYSLOG)."
    fi
fi

if [ -n "$TARGET_SYSLOG" ]; then
    if [ $USING_MOCK_SYSLOG -eq 1 ]; then
        echo "Scanning Syslog (Simulated: ${TARGET_SYSLOG})..."
    else
        echo "Scanning Syslog (${TARGET_SYSLOG})..."
    fi

    # Perform scan (case-insensitive grep)
    # Count occurrences
    SYSLOG_ERR_COUNT=$(grep -E -i "$SYSLOG_PATTERNS" "$TARGET_SYSLOG" | wc -l)
    
    echo "  - Total error/warning patterns found: ${SYSLOG_ERR_COUNT}"
    
    if [ "$SYSLOG_ERR_COUNT" -gt 0 ]; then
        echo "  - Most recent occurrences:"
        grep -E -i "$SYSLOG_PATTERNS" "$TARGET_SYSLOG" | tail -n 3 | while read -r line; do
            echo "    * ${line}"
        done
        
        # Incident logging threshold: e.g., > 5 syslog errors or warnings
        if [ "$SYSLOG_ERR_COUNT" -gt 5 ]; then
            SEVERITY="WARNING"
            # If count is extremely high, flag CRITICAL
            if [ "$SYSLOG_ERR_COUNT" -gt 20 ]; then
                SEVERITY="CRITICAL"
            fi
            echo "${HOSTNAME} | syslog_errors | ${SEVERITY} | ${TIMESTAMP}" >> "$INCIDENTS_LOG"
            echo "  [ALERT] Syslog error count exceeded threshold. Alert logged."
        fi
    fi
else
    echo "Syslog check skipped (No source file)."
fi

echo "-"

# ---------------------------------------------------------
# Auth log Scan
# ---------------------------------------------------------
TARGET_AUTHLOG=""
USING_MOCK_AUTHLOG=0

if [ -f "$AUTHLOG" ]; then
    if [ -r "$AUTHLOG" ]; then
        TARGET_AUTHLOG="$AUTHLOG"
    else
        echo "[WARNING] Permission denied to read $AUTHLOG. Trying mock fallback."
    fi
fi

if [ -z "$TARGET_AUTHLOG" ]; then
    if [ -f "$MOCK_AUTHLOG" ]; then
        TARGET_AUTHLOG="$MOCK_AUTHLOG"
        USING_MOCK_AUTHLOG=1
    else
        echo "[INFO] Auth log file not found: $AUTHLOG (and no mock file at $MOCK_AUTHLOG)."
    fi
fi

if [ -n "$TARGET_AUTHLOG" ]; then
    if [ $USING_MOCK_AUTHLOG -eq 1 ]; then
        echo "Scanning Auth Log (Simulated: ${TARGET_AUTHLOG})..."
    else
        echo "Scanning Auth Log (${TARGET_AUTHLOG})..."
    fi

    # Count failed logins and access violations
    AUTHLOG_FAIL_COUNT=$(grep -E -i "$AUTHLOG_PATTERNS" "$TARGET_AUTHLOG" | wc -l)
    
    echo "  - Total authentication incidents/failures found: ${AUTHLOG_FAIL_COUNT}"
    
    if [ "$AUTHLOG_FAIL_COUNT" -gt 0 ]; then
        echo "  - Most recent occurrences:"
        grep -E -i "$AUTHLOG_PATTERNS" "$TARGET_AUTHLOG" | tail -n 3 | while read -r line; do
            echo "    * ${line}"
        done
        
        # Any authentication failure is typically CRITICAL for L1 triage
        echo "${HOSTNAME} | auth_failures | CRITICAL | ${TIMESTAMP}" >> "$INCIDENTS_LOG"
        echo "  [ALERT] Authentication failure(s) detected. Alert logged."
    fi
else
    echo "Auth log check skipped (No source file)."
fi

echo "========================================="
