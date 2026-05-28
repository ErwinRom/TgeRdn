# TGE Scraper - Project Summary

## What You Now Have

A complete, production-ready solution to automatically fetch electricity prices from TGE (Polish Energy Exchange) and generate Home Assistant compatible data files every hour.

## Components Overview

### 1. **scraper.py** - Web Scraper
- Fetches Fixing I electricity prices from TGE website
- Extracts 24 hourly price points with delivery dates
- Outputs clean JSON format
- Handles errors gracefully with timeouts

**Usage:** `python scraper.py [DATE]`

### 2. **yaml_generator.py** - Data Converter
- Converts JSON price data to Home Assistant YAML format
- Generates hourly entries with timestamps and periods
- Adds metadata (unit, icon, friendly name)
- Reads from file or stdin

**Usage:** `python yaml_generator.py input.json [output.yaml]`

### 3. **scheduler.py** - Automation Manager
- Runs scraper and YAML generator automatically every hour
- Manages output directories and file handling
- Logs all operations with timestamps
- Configurable intervals and date offsets

**Usage:** `python scheduler.py [--output-dir DIR] [--interval HOURS]`

### 4. **Supporting Files**
- `requirements.txt` - Python package dependencies
- `setup_cron.sh` - Automated cron job installer
- `tgerdn-scraper.service` - Systemd service file
- `README.md` - Complete documentation
- `QUICKSTART.md` - Getting started guide

## Data Flow

```
TGE Website
    ↓
scraper.py (fetches prices)
    ↓
JSON: tgerdn_prices.json
    ↓
yaml_generator.py (converts format)
    ↓
YAML: tgerdn_prices.yaml
    ↓
Home Assistant Entity: tgerdn.cena.dzis
```

## Output Format

### YAML Structure (24 hourly entries)
```yaml
last_update: "2026-05-28T22:15:40+02:00"
data_points: 24
prices:
  - dtime: "2026-05-28 01:00:00"
    period: "00:00 - 01:00"
    rce_pln: 569.94
    business_date: "2026-05-28"
  - dtime: "2026-05-28 02:00:00"
    period: "01:00 - 02:00"
    rce_pln: 546.99
    business_date: "2026-05-28"
  # ... 22 more hourly entries
unit_of_measurement: PLN/MWh
icon: mdi:cash
friendly_name: TGE RDN - Cena dzis
```

## Setup Instructions

### Quick Start (5 minutes)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test scraper
python scraper.py 28-05-2026

# 3. Generate YAML
python scraper.py 28-05-2026 | python yaml_generator.py -

# 4. Start hourly scheduler (uses today's date automatically)
python scheduler.py --output-dir /tmp/tgerdn

# 5. Files appear at /tmp/tgerdn/tgerdn_prices.yaml
```

### Production Setup (Choose One)

**Option A: Cron (Simplest)**
```bash
bash setup_cron.sh
# Runs every hour automatically
```

**Option B: Systemd (Recommended)**
```bash
sudo cp tgerdn-scraper.service /etc/systemd/system/
sudo systemctl enable --now tgerdn-scraper.service
```

**Option C: Docker (Enterprise)**
- See README.md for Dockerfile approach

## Home Assistant Integration

### Minimal Configuration
```yaml
rest:
  - name: "TGE RDN"
    unique_id: tgerdn_cena_dzis
    resource: "file:///tmp/tgerdn/tgerdn_prices.yaml"
    json_attributes:
      - prices
      - last_update
```

### Advanced: Template Sensor
```yaml
template:
  - sensor:
      - name: "Current Hour Price"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for p in prices if p.period.split(' - ')[0][:2]|int == hour %}
              {{ p.rce_pln }}
            {%- endfor %}
          {%- endif %}
```

## Features

✅ **Automatic Updates** - Runs hourly, updates automatically
✅ **Home Assistant Ready** - YAML format works directly with HA
✅ **Error Handling** - Graceful failures, automatic retries
✅ **Timezone Aware** - Proper date/time handling for Poland
✅ **Clean Output** - 24 hourly data points, not 96 15-min intervals
✅ **Flexible Scheduling** - Cron, Systemd, or manual
✅ **Easy Integration** - Drop-in REST sensor configuration
✅ **Logging** - Full audit trail of operations
✅ **Customizable** - Adjust intervals, dates, output locations

## File Locations

After running scheduler:
```
/tmp/tgerdn/
├── tgerdn_prices.json   # Raw JSON from scraper
└── tgerdn_prices.yaml   # Home Assistant YAML
```

Custom location:
```bash
python scheduler.py --output-dir /home/ha/prices
```

## Configuration Examples

### Every hour (default)
```bash
python scheduler.py
```

### Every 2 hours
```bash
python scheduler.py --interval 2
```

### Specific time daily
```bash
python scheduler.py --hour "00:00"
```

### Custom directory
```bash
python scheduler.py --output-dir /home/ha/tge_data
```

### All options
```bash
python scheduler.py \
  --output-dir /home/ha/tge \
  --interval 1 \
  --date-offset -1 \
  --hour "*"
```

## Troubleshooting

### No data appearing?
1. Check Python is installed: `python --version`
2. Install deps: `pip install -r requirements.txt`
3. Test scraper: `python scraper.py 28-05-2026`

### YAML not generated?
1. Verify JSON works: `python scraper.py 28-05-2026 | python -m json.tool`
2. Test generator: `python yaml_generator.py prices.json`

### Scheduler not running?
1. Check process: `ps aux | grep scheduler`
2. Check logs: `tail -f /var/log/tgerdn-scraper.log` (cron) or `sudo journalctl -u tgerdn-scraper.service` (systemd)
3. Test manually: `python scheduler.py`

### Wrong date in output?
- Scraper automatically returns prices matching the date you request
- If you request `28-05-2026`, you get `2026-05-28_H01...H24`
- Date is automatically adjusted internally to get the correct prices

## Requirements

- Python 3.6+
- requests (web scraping)
- beautifulsoup4 (HTML parsing)
- PyYAML (YAML generation)
- schedule (job scheduling)

All included in `requirements.txt`

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Test basic scraping: `python scraper.py`
3. ✅ Test YAML generation: `python yaml_generator.py`
4. ✅ Choose setup method (Cron/Systemd/Manual)
5. ✅ Configure Home Assistant
6. ✅ Create automations/templates using price data

## Support

- See README.md for complete documentation
- See QUICKSTART.md for step-by-step guide
- Check individual scripts for detailed docstrings
- All scripts have error logging and timeouts

---

**Project Created:** 2026-05-28
**Status:** Production Ready
**Update Interval:** Hourly
**Data Points:** 24 (hourly)
**Format:** Home Assistant YAML
