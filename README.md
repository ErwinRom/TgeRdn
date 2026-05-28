# TGE Energy Prices Scraper for Home Assistant

A Python solution to scrape electricity prices from the TGE (Towarowa Giełda Energii / Polish Energy Exchange) website and generate Home Assistant compatible YAML files.

## Features

- ✅ **Two Sensors:**
  - `sensor.tge_rdn_cena_dzis` - Today's hourly electricity prices
  - `sensor.tge_rdn_cena_jutro` - Tomorrow's hourly electricity prices
- ✅ Fetches "Fixing I" electricity prices (Kurs PLN/MWh)
- ✅ Extracts delivery dates (Data dostawy)
- ✅ 24 hourly price points per day
- ✅ Generates Home Assistant entity YAML
- ✅ Automated hourly scheduling
- ✅ JSON and YAML output formats
- ✅ Both sensors update simultaneously every hour

## Installation

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Components

### 1. Scraper (`scraper.py`)
Core scraper that fetches price data from TGE website.

**Usage:**
```bash
# Default (current date)
python scraper.py

# Specify custom date (DD-MM-YYYY format)
python scraper.py 27-05-2026

# Specify type parameter
python scraper.py 27-05-2026 1
```

**Output:** JSON with hourly price data

### 2. YAML Generator (`yaml_generator.py`)
Converts JSON price data to Home Assistant entity YAML format.

**Usage:**
```bash
# From JSON file
python yaml_generator.py prices.json output.yaml

# From stdin
python scraper.py 28-05-2026 | python yaml_generator.py -

# Just print to stdout
python yaml_generator.py prices.json
```

**Output Format:**
```yaml
last_update: "2026-05-28T22:15:40+02:00"
data_points: 24
prices:
  - dtime: "2026-05-28 00:00:00"
    period: 23:00 - 00:00
    rce_pln: 569.02
    business_date: "2026-05-28"
  - dtime: "2026-05-28 01:00:00"
    period: 00:00 - 01:00
    rce_pln: 550.45
    business_date: "2026-05-28"
  # ... 22 more hourly entries
unit_of_measurement: PLN/MWh
icon: mdi:cash
friendly_name: TGE RDN - Cena dzis
```

### 3. Scheduler (`scheduler.py`)
Runs the scraper and YAML generator every hour automatically.

**Usage:**
```bash
# Run with defaults (generates files in /tmp/tgerdn, uses today's date)
python scheduler.py

# Custom output directory
python scheduler.py --output-dir /home/ha/tgerdn

# Custom interval (every 2 hours)
python scheduler.py --interval 2

# Specific time of day
python scheduler.py --hour "00:00"
```

**Options:**
- `--output-dir`: Directory for generated files (default: `/tmp/tgerdn`)
- `--interval`: Run every N hours (default: 1)
- `--hour`: Run at specific time in HH:MM format (default: every hour)

## Setup for Continuous Operation

### Option 1: Systemd Service (Recommended)

1. Edit `tgerdn-scraper.service` with your paths
2. Copy to systemd directory:
   ```bash
   sudo cp tgerdn-scraper.service /etc/systemd/system/
   ```
3. Create corresponding timer:
   ```bash
   sudo cp tgerdn-scraper.timer /etc/systemd/system/
   ```
4. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tgerdn-scraper.service
   sudo systemctl start tgerdn-scraper.service
   ```

### Option 2: Cron Job

Run the setup script:
```bash
bash setup_cron.sh
```

Or manually add to crontab:
```bash
# Run every hour at minute 0
0 * * * * cd /home/erwin/Projekty/TgeRdn && python3 scheduler.py --output-dir /tmp/tgerdn >> /var/log/tgerdn.log 2>&1
```

### Option 3: Docker Container

Create a Dockerfile for containerized deployment.

## Home Assistant Integration

1. Create a REST sensor in `configuration.yaml`:
   ```yaml
   rest:
     - name: "TGE RDN Prices"
       unique_id: "tgerdn_cena_dzis"
       resource_template: "file:///tmp/tgerdn/tgerdn_prices.yaml"
       scan_interval: 300
       value_template: "{{ value_json.data_points }}"
       json_attributes:
         - prices
         - last_update
         - unit_of_measurement
         - friendly_name
   ```

2. Or use File sensor:
   ```yaml
   file:
     - platform: template
       name: "TGE RDN Cena Dzis"
       unique_id: "tgerdn_cena_dzis"
       file_path: /tmp/tgerdn/tgerdn_prices.yaml
       unit_of_measurement: "PLN/MWh"
   ```

3. Access the data in automations or templates:
   ```jinja
   {% set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
   {% for price in prices %}
     {{ price.dtime }}: {{ price.rce_pln }} {{ price.unit_of_measurement }}
   {% endfor %}
   ```

## Output Files

### JSON Format
Located at: `{output_dir}/tgerdn_prices.json`
```json
{
  "date_fetched": "2026-05-28T22:15:40.579720",
  "url": "https://tge.pl/energia-elektryczna-rdn?dateShow=28-05-2026&type=1",
  "fixing_i_prices": [
    {
      "data_dostawy": "2026-05-29_H01",
      "fixing_i_price_pln_mwh": 650.7
    }
  ]
}
```

### YAML Format
Located at: `{output_dir}/tgerdn_prices.yaml`

Ready for Home Assistant integration with all hourly data and metadata.

## Troubleshooting

### Script runs but no output
- Check if TGE website is accessible
- Verify date parameters are correct
- Check network connectivity

### YAML not generated
- Ensure `PyYAML` is installed: `pip install PyYAML`
- Check JSON data contains `fixing_i_prices` key

### Scheduler not running
- For Cron: Check `crontab -l` to verify job
- For Systemd: Check `sudo journalctl -u tgerdn-scraper.service`
- Verify Python path is correct

### Logs location
- Cron: Check configured log file (default: `/var/log/tgerdn-scraper.log`)
- Systemd: `sudo journalctl -u tgerdn-scraper.service -f`

## Files

- `scraper.py` - Main TGE web scraper
- `yaml_generator.py` - JSON to YAML converter
- `scheduler.py` - Hourly task scheduler
- `requirements.txt` - Python dependencies
- `tgerdn-scraper.service` - Systemd service file
- `setup_cron.sh` - Cron job setup script

## Requirements

- Python 3.6+
- requests
- beautifulsoup4
- PyYAML
- schedule

## Notes

- Scraper automatically adjusts date: queries one day before to get prices for the requested date
- The date you provide is the date you'll receive prices for (no manual adjustment needed)
- Data includes 24 hourly price points per day
- Timezone: Poland (UTC+2 summer, UTC+1 winter)
- All prices in PLN/MWh
- Updates every hour automatically when scheduler is running
