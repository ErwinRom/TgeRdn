#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${OUTPUT_DIR}"
exec python3 /app/scheduler.py --output-dir "${OUTPUT_DIR}" --interval "${INTERVAL}" --hour "${HOUR}"
