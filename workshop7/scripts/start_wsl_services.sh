#!/usr/bin/env bash
# Starts both services for the benchmark, without logs. Ctrl+C stops them.
# Usage: bash scripts/start_wsl_services.sh [ingestion_port] [wa_mock_port]
set -u
cd "$(dirname "$0")/.."

export W7_QUIET=1
python="$HOME/w7-venv/bin/python"
ingestion_port="${1:-8000}"
wa_mock_port="${2:-8001}"

trap 'trap - EXIT INT TERM; kill 0' EXIT INT TERM

"$python" -m uvicorn services.ingestion_service:app \
  --host 0.0.0.0 --port "$ingestion_port" --no-access-log --log-level warning &
"$python" -m uvicorn services.wa_mock_service:app \
  --host 0.0.0.0 --port "$wa_mock_port" --no-access-log --log-level warning &

echo "services running on ports $ingestion_port and $wa_mock_port (Ctrl+C to stop)"
wait
