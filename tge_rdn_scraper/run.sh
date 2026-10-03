#!/usr/bin/env bash
set -euo pipefail

exec python3 - <<'PY'
import asyncio
import json

from scheduler import TGEScheduler

with open('/data/options.json', encoding='utf-8') as options_file:
	options = json.load(options_file)

output_dir = options.get('output_dir', '/config/tgerdn')
hour = options.get('hour', '00:01,12:01')

asyncio.run(TGEScheduler(output_dir=output_dir).run(hour=hour))
PY