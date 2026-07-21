#!/usr/bin/env bash
#
# run_if_needed.sh
# -----------------
# Runs the NSE pipeline only if it hasn't already succeeded today. Meant to
# be called often (e.g. every 30 minutes via cron) on a machine that isn't
# always on - whichever run happens first after the machine wakes up does
# the day's work; every other check that day is a fast no-op.
#
# This intentionally does NOT rely on cron firing at one exact time, since
# a laptop/desktop being asleep at that moment would just mean a missed day.
# Frequent checks + "already done today?" logic means it self-heals
# regardless of when the machine happens to be on.
#
# Usage (manual test):
#   ./scripts/run_if_needed.sh
#
# Usage (crontab - see README for setup):
#   */30 * * * * /path/to/nse-dashboard/scripts/run_if_needed.sh >> /path/to/nse-dashboard/logs/cron.log 2>&1

set -euo pipefail

# @reboot cron entries can fire before networking is actually up, which
# would make the Postgres connectivity check below fail spuriously. A
# short fixed delay is simpler and more portable across distros than
# scripting a "wait for network" loop.
sleep 30

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/pipeline.log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$BACKEND_DIR"

# Load env vars (POSTGRES_*, etc.) from backend/.env if present, without
# clobbering anything already exported in the calling shell/cron env.
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

# Activate the venv if one exists at backend/venv (adjust path if yours
# lives elsewhere).
if [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "venv/bin/activate"
fi

ALREADY_DONE="$(python3 -c "
from datetime import date
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    row = conn.execute(text('''
        SELECT 1 FROM etl_run_log
        WHERE run_date = :today AND status = 'success'
        LIMIT 1
    '''), {'today': date.today()}).first()
    print('yes' if row else 'no')
" 2>>"$LOG_FILE")"

if [ "$ALREADY_DONE" = "yes" ]; then
    # Quiet on purpose - this runs every 30 min, most checks should be silent.
    exit 0
fi

log "=== No successful run for today yet - starting pipeline ==="

run_step() {
    local step_name="$1"
    local script="$2"
    log "-> $step_name"
    if python3 "$script" >> "$LOG_FILE" 2>&1; then
        log "   OK: $step_name"
    else
        log "   FAILED: $step_name (see $LOG_FILE for details)"
        log "=== Pipeline run FAILED at step: $step_name ==="
        exit 1
    fi
}

run_step "Scraping NSE"            "etl/scrape_nse.py"
run_step "Loading Postgres"        "etl/load_postgres.py"
run_step "Exporting static JSON"   "etl/build_static_export.py"
run_step "Exporting Power BI CSVs" "etl/export_powerbi.py"

log "=== Pipeline run complete ==="
