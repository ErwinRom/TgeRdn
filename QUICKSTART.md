# Quick Start Guide - TGE Scraper for Home Assistant

## Step 1: Install Dependencies

```bash
cd /home/erwin/Projekty/TgeRdn
pip install -r requirements.txt
```

## Step 2: Test the Scraper

```bash
# Request today's prices
python scraper.py 28-05-2026

# Request specific date (format: DD-MM-YYYY)
python scraper.py 27-05-2026
```

This outputs JSON with prices for the date you request:
```json
{
  "fixing_i_prices": [
    {"data_dostawy": "2026-05-28_H01", "fixing_i_price_pln_mwh": 569.94},
    {"data_dostawy": "2026-05-28_H02", "fixing_i_price_pln_mwh": 546.99},
    ...
  ]
}
```

## Step 3: Generate YAML

```bash
# Create both JSON and YAML files
python scraper.py 28-05-2026 > prices.json
python yaml_generator.py prices.json output.yaml

# View the YAML
cat output.yaml
```

## Step 4: Setup Hourly Scheduler

### Option A: Run as Background Service

```bash
# Start the scheduler in background (uses today's date automatically)
python scheduler.py --output-dir /tmp/tgerdn &

# Generated files:
# - /tmp/tgerdn/tgerdn_prices.yaml  (Home Assistant reads this)
# - /tmp/tgerdn/tgerdn_prices.json  (Raw data backup)
```

### Option B: Setup with Cron (Runs every hour automatically)

```bash
bash setup_cron.sh
```

Check status:
```bash
crontab -l | grep tgerdn
```

## Step 5: Configure Home Assistant

### Method 1: REST Sensor (reads YAML file)

Add to `configuration.yaml`:
```yaml
rest:
  - name: "TGE RDN Cena Dzis"
    unique_id: tgerdn_cena_dzis
    resource: "file:///tmp/tgerdn/tgerdn_prices.yaml"
    scan_interval: 300
    value_template: "{{ value_json.data_points }}"
    json_attributes:
      - prices
      - last_update
      - unit_of_measurement
      - friendly_name
```

### Method 2: Template Sensor (with custom logic)

```yaml
template:
  - sensor:
      - name: "TGE RDN Current Hour Price"
        unique_id: tgerdn_current_hour_price
        unit_of_measurement: "PLN/MWh"
        state_class: measurement
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for price in prices %}
              {%- if price.period.split(' - ')[0][:2] | int == hour %}
                {{ price.rce_pln }}
              {%- endif %}
            {%- endfor %}
          {%- endif %}
```

### Method 3: Custom Integration (Python script)

```python
# in configuration.yaml
python_script:
  # Enable python scripts
```

## Verification Steps

### 1. Check Scraper Works
```bash
python scraper.py 28-05-2026 | python -m json.tool
```

### 2. Check YAML Generator Works
```bash
python scraper.py 28-05-2026 > /tmp/test.json
python yaml_generator.py /tmp/test.json | head -20
```

### 3. Check Files Exist After Scheduling
```bash
ls -lah /tmp/tgerdn/
cat /tmp/tgerdn/tgerdn_prices.yaml | head -30
```

### 4. Test One Scheduler Run
```bash
python scheduler.py --output-dir /tmp/tgerdn --interval 1
# Should complete within 5 seconds and create files
```

## Troubleshooting

### YAML not updating?
```bash
# Check scheduler is running
ps aux | grep scheduler.py

# Check for errors
tail -f /var/log/tgerdn-scraper.log  # if using cron
sudo journalctl -u tgerdn-scraper.service -f  # if using systemd
```

### Wrong date in prices?
The scraper automatically adjusts dates to return the correct prices. If you request 28-05-2026, you'll get prices for 2026-05-28 (not tomorrow).

### File permissions issues?
```bash
# Make sure /tmp/tgerdn is writable
sudo chmod 777 /tmp/tgerdn
# Or create in user directory:
python scheduler.py --output-dir ~/tgerdn_prices
```

## Output Location

Default: `/tmp/tgerdn/`
- `tgerdn_prices.yaml` - Home Assistant reads this
- `tgerdn_prices.json` - Raw price data

## Testing in Home Assistant

After setup, reload templates:
```yaml
automation:
  - alias: "Test TGE Prices"
    trigger:
      platform: time_pattern
      minutes: "/10"
    action:
      service: homeassistant.reload_config_entry
      target:
        domain: rest
```

Or manually in Developer Tools → Template:
```jinja
{{ state_attr('sensor.tge_rdn_cena_dzis', 'prices') | first }}
```

## Next Steps

- [ ] Install dependencies
- [ ] Test scraper manually
- [ ] Generate YAML file
- [ ] Start scheduler
- [ ] Configure Home Assistant sensor
- [ ] Verify data updates hourly
- [ ] Create automations using the data
