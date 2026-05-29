#!/bin/bash
# Wasteland GEO Pipeline — Random Scheduling Script
# Called by Hermes cron. Uses `at` to schedule next random execution.
# Target: 2-3 times per week, completely random time.

PIPELINE="$HOME/webengine/pipeline/run_geo.py"
LOG_FILE="$HOME/.wasteland_geo_log.jsonl"
HERMES_CRON_DIR="$HOME/.hermes/cron/output"

echo "=== [cron] daily-wasteland-geo-evolution v2 ==="

# Check if we should schedule anything: count this week's runs
THIS_WEEK=$(date +%Y-%U)
RUNS_THIS_WEEK=0
if [ -f "$LOG_FILE" ]; then
    RUNS_THIS_WEEK=$(grep -c "\"deploy_time\":\"$THIS_WEEK" "$LOG_FILE" 2>/dev/null || echo 0)
fi

# Already hit the weekly target (2-3 runs)
if [ "$RUNS_THIS_WEEK" -ge 3 ]; then
    echo "[SILENT] Weekly target reached ($RUNS_THIS_WEEK runs)"
    exit 0
fi

# Run the pipeline now
cd "$HOME/webengine"
python3 "$PIPELINE"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Status: FAIL — Pipeline returned $EXIT_CODE"
    exit 1
fi

# Schedule next run at random time (1-3 days from now, random hour)
RANDOM_DAYS=$((1 + RANDOM % 3))
RANDOM_HOUR=$((9 + RANDOM % 12))
RANDOM_MINUTE=$((RANDOM % 60))

echo "Status: OK — Next run scheduled in $RANDOM_DAYS day(s) at ${RANDOM_HOUR}:${RANDOM_MINUTE}"

# Schedule via `at`
NEXT_TIME=$(date -v+${RANDOM_DAYS}d -v${RANDOM_HOUR}H -v${RANDOM_MINUTE}M "+%H:%M %m/%d/%Y")
echo "cd $HOME/webengine && python3 $PIPELINE" | at "$NEXT_TIME" 2>/dev/null || echo "Note: 'at' scheduling unavailable, relying on cron trigger"
