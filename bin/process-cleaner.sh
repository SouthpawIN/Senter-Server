#!/bin/bash
# Process Cleaner - Prevents SSH/speak process accumulation
# Run this periodically via cron or systemd timer

STUCK_SSH_PATTERN="ssh.*100\.(79|93)"  # TailScale phone IPs
MAX_AGE_MINUTES=10
LOG_FILE="${HOME}/.senter/logs/process-cleaner.log"

mkdir -p "$(dirname $LOG_FILE)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Process Cleaner Started ==="

# Find and kill stuck SSH processes to phones
STUCK_COUNT=$(ps aux | grep -E "$STUCK_SSH_PATTERN" | grep -v grep | wc -l)

if [ "$STUCK_COUNT" -gt 0 ]; then
    log "⚠ Found $STUCK_COUNT stuck SSH processes"
    
    # Show what we found
    ps aux | grep -E "$STUCK_SSH_PATTERN" | grep -v grep | head -5 >> "$LOG_FILE"
    
    # Kill them
    pkill -9 -f "$STUCK_SSH_PATTERN" 2>/dev/null
    
    KILLED=$(ps aux | grep -E "$STUCK_SSH_PATTERN" | grep -v grep | wc -l)
    log "✓ Killed stuck processes. Remaining: $KILLED"
else
    log "✓ No stuck SSH processes found"
fi

# Clean up speak queue if it's been stuck too long
if [ -f "/tmp/speak_playing" ]; then
    PLAYING_AGE=$(( $(date +%s) - $(stat -c %Y /tmp/speak_playing) ))
    
    if [ $PLAYING_AGE -gt $((MAX_AGE_MINUTES * 60)) ]; then
        log "⚠ Speak playing marker stuck for ${PLAYING_AGE}s - clearing"
        rm -f /tmp/speak_playing
        echo "[]" > /tmp/speak_queue
    fi
fi

# Check speak queue size
if [ -f "/tmp/speak_queue" ]; then
    QUEUE_SIZE=$(cat /tmp/speak_queue | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    
    if [ "$QUEUE_SIZE" -gt 10 ]; then
        log "⚠ Speak queue has $QUEUE_SIZE items - clearing backlog"
        echo "[]" > /tmp/speak_queue
    fi
fi

log "=== Process Cleaner Complete ==="