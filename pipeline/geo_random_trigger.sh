#!/bin/bash
# Wasteland GEO Pipeline — Random Scheduling Script v2
# Called by Hermes cron daily at 10:00.
# Target: 15-20 times per week → each daily trigger has ~83% chance.
# After running, schedules next run via `at` within 8-24 hours.
# Also counts runs from the `run_geo.py` log, not just shell triggers.

PIPELINE="$HOME/webengine/pipeline/run_geo.py"
LOG_FILE="$HOME/.wasteland_geo_log.jsonl"

echo "=== [cron] daily-wasteland-geo-evolution v2 (15-20x/week) ==="

# Count this week's deploys from the JSONL log
THIS_WEEK_START=$(date -v-$(date +%u)d +%Y-%m-%d)  # Monday of this week
RUNS_THIS_WEEK=0
if [ -f "$LOG_FILE" ]; then
    RUNS_THIS_WEEK=$(grep "deploy_time" "$LOG_FILE" 2>/dev/null | grep -c "$THIS_WEEK_START")
fi

# Hard ceiling: 20 runs/week
if [ "$RUNS_THIS_WEEK" -ge 20 ]; then
    echo "[SILENT] Weekly ceiling reached (20 runs)"
    exit 0
fi

# Run the pipeline
cd "$HOME/webengine"
python3 "$PIPELINE"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Status: FAIL — Pipeline returned $EXIT_CODE"
    exit 1
fi

# Schedule next random run: 4-24 hours from now, random minute
RANDOM_HOURS=$((4 + RANDOM % 21))
RANDOM_MINUTE=$((RANDOM % 60))
NEXT_TIME=$(date -v+${RANDOM_HOURS}H -v${RANDOM_MINUTE}M "+%H:%M %m/%d/%Y")

echo "Status: OK — Next run in ~${RANDOM_HOURS}h${RANDOM_MINUTE}m at ${NEXT_TIME}"

# Use `at` for next schedule (falls back to cron-only if unavailable)
echo "cd $HOME/webengine && python3 $PIPELINE" | at "$NEXT_TIME" 2>/dev/null || echo "(note: 'at' unavailable, relying on cron-only trigger)"
