#!/usr/bin/env bash
#
# run_pipeline.sh
# ----------------
# Runs the full NSE scrape -> load -> export pipeline via docker-compose exec,
# meant to be called from the HOST machine's crontab (not from inside a
# container). This is the simplest possible scheduler for a single daily
# task - no Airflow webserver/scheduler overhead, just cron calling this
# script once a day.
#
# Usage (manual test):
#   ./scripts/run_pipeline.sh
#
# Usage (crontab - see README section below for the full line):
#   16:05 Nairobi time, weekdays -> runs this script, logs to logs/pipeline.log
#
# Exit code is non-zero if any step fails, so cron's own failure handling
# (e.g. MAILTO in the crontab) can alert you.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/pipeline.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

mkdir -p "$LOG_DIR"

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR"

log "=== Starting NSE pipeline run ==="

run_step() {
    local step_name="$1"
    local script="$2"
    log "-> $step_name"
    if docker-compose exec -T backend python "$script" >> "$LOG_FILE" 2>&1; then
        log "   OK: $step_name"
    else
        log "   FAILED: $step_name (see $LOG_FILE for details)"
        log "=== Pipeline run FAILED at step: $step_name ==="
        exit 1
    fi
}

run_step "Scraping NSE"          "etl/scrape_nse.py"
run_step "Loading Postgres"      "etl/load_postgres.py"
run_step "Exporting static JSON" "etl/build_static_export.py"
run_step "Exporting Power BI CSVs" "etl/export_powerbi.py"

log "=== Pipeline run complete ==="
