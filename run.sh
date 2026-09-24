#!/usr/bin/env bash
set -euo pipefail

exec python3 - <<'PY'
import json

from scheduler import TGEScheduler

with open('/data/options.json', encoding='utf-8') as options_file:
	options = json.load(options_file)

output_dir = options.get('output_dir', '/config/tgerdn')
interval = int(options.get('interval', 1))
hour = options.get('hour', '*')

TGEScheduler(output_dir=output_dir).run(interval=interval, hour=hour)
PY
