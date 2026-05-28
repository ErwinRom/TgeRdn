# Home Assistant Configuration for TGE Sensors

## Overview
Two REST sensors that update automatically every hour:
1. `sensor.tge_rdn_cena_dzis` - Today's electricity prices
2. `sensor.tge_rdn_cena_jutro` - Tomorrow's electricity prices

## Prerequisites
1. Install the scraper: `pip install -r requirements.txt`
2. Run the scheduler: `python scheduler.py --output-dir /tmp/tgerdn`
3. Ensure `/tmp/tgerdn/` is readable by Home Assistant

## Configuration

Add to your `configuration.yaml`:

```yaml
rest:
  - resource: "file:///tmp/tgerdn/tgerdn_prices.yaml"
    name: "TGE RDN Cena Dzis"
    unique_id: tgerdn_cena_dzis
    scan_interval: 300  # Check every 5 minutes for updates
    json_attributes:
      - prices
      - last_update
      - data_points
      - unit_of_measurement
      - friendly_name
    value_template: "{{ value_json.data_points }}"

  - resource: "file:///tmp/tgerdn/tgerdn_prices_tomorrow.yaml"
    name: "TGE RDN Cena Jutro"
    unique_id: tgerdn_cena_jutro
    scan_interval: 300
    json_attributes:
      - prices
      - last_update
      - data_points
      - unit_of_measurement
      - friendly_name
    value_template: "{{ value_json.data_points }}"
```

## Template Sensors (Optional)

Get the current hour price automatically:

```yaml
template:
  - sensor:
      - name: "Current Hour TGE Price"
        unique_id: tgerdn_current_price_dzis
        unit_of_measurement: "PLN/MWh"
        state_class: measurement
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for p in prices if p.period.split(' - ')[0][:2]|int == hour %}
              {{ p.rce_pln }}
            {%- endif %}
          {%- endif %}
        
      - name: "Tomorrow's Hour Price"
        unique_id: tgerdn_current_price_jutro
        unit_of_measurement: "PLN/MWh"
        state_class: measurement
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for p in prices if p.period.split(' - ')[0][:2]|int == hour %}
              {{ p.rce_pln }}
            {%- endif %}
          {%- endif %}
      
      - name: "Min Price Today"
        unique_id: tgerdn_min_price_dzis
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}
      
      - name: "Max Price Today"
        unique_id: tgerdn_max_price_dzis
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | max) }}
          {%- endif %}
      
      - name: "Min Price Tomorrow"
        unique_id: tgerdn_min_price_jutro
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}
      
      - name: "Max Price Tomorrow"
        unique_id: tgerdn_max_price_jutro
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | max) }}
          {%- endif %}
```

## Automations

### Example 1: Notify when price is below threshold

```yaml
automation:
  - alias: "Cheap electricity today"
    trigger:
      platform: state
      entity_id: sensor.tge_rdn_cena_dzis
      for: "00:05:00"
    condition:
      - condition: template
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) < 100 }}
          {%- endif %}
    action:
      service: notify.mobile_app_<your_device>
      data:
        title: "TGE Alert"
        message: "Electricity price is low today!"
```

### Example 2: Track cheapest hour

```yaml
automation:
  - alias: "Find cheapest hour today"
    trigger:
      platform: state
      entity_id: sensor.tge_rdn_cena_dzis
    action:
      service: script.log_cheapest_hour_today

script:
  log_cheapest_hour_today:
    sequence:
      - service: system_log.write
        data:
          level: info
          logger: custom_component.tge
          message: |
            Today's cheapest hour: {% set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}{{ prices | map(attribute='dtime') | list | first }} - {{ (prices | map(attribute='rce_pln') | list | min) }} PLN/MWh
```

## Accessing Data

In automations and templates, access the data like this:

```jinja
# Get all prices
{{ state_attr('sensor.tge_rdn_cena_dzis', 'prices') }}

# Get current hour
{{ now().hour }}

# Get cheapest price
{{ (state_attr('sensor.tge_rdn_cena_dzis', 'prices') | map(attribute='rce_pln') | list | min) }}

# Get most expensive price
{{ (state_attr('sensor.tge_rdn_cena_dzis', 'prices') | map(attribute='rce_pln') | list | max) }}

# Get specific hour (e.g., 10:00)
{% set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
{% for p in prices %}
  {% if '10:00' in p.dtime %}
    {{ p.rce_pln }}
  {% endif %}
{% endfor %}
```

## File Structure

The scheduler creates these files in `/tmp/tgerdn/`:

```
/tmp/tgerdn/
├── tgerdn_prices.json           # Today's raw JSON
├── tgerdn_prices.yaml           # Today's YAML (read by sensor)
├── tgerdn_prices_tomorrow.json  # Tomorrow's raw JSON
└── tgerdn_prices_tomorrow.yaml  # Tomorrow's YAML (read by sensor)
```

## Update Frequency

- **Scraper runs:** Every 1 hour (0:00, 1:00, 2:00, etc.)
- **Home Assistant reads:** Every 5 minutes (scan_interval)
- **Data freshness:** At most 5 minutes stale from the last hour update

## Troubleshooting

### Sensors show unavailable
1. Check scheduler is running: `ps aux | grep scheduler.py`
2. Verify files exist: `ls -la /tmp/tgerdn/`
3. Check file is readable: `cat /tmp/tgerdn/tgerdn_prices.yaml | head`
4. Reload REST integration: Developer Tools → YAML → Press "Reload custom YAML configurations"

### File permissions
```bash
# Ensure Home Assistant can read the files
sudo chown homeassistant:homeassistant /tmp/tgerdn
chmod 755 /tmp/tgerdn
chmod 644 /tmp/tgerdn/*.yaml
```

### No data in prices attribute
- Ensure YAML file is valid: `python -m yaml /tmp/tgerdn/tgerdn_prices.yaml`
- Check scraper is working: `cd /home/erwin/Projekty/TgeRdn && python scraper.py 28-05-2026`

## Performance Notes

- Each sensor queries a local YAML file (very fast)
- No API rate limits since we're reading local files
- Scheduler uses ~0.5% CPU for ~10 seconds each hour
- YAML files are ~2-3 KB each

## Next Steps

1. Add to `configuration.yaml`
2. Restart Home Assistant
3. Check Developer Tools → States for `sensor.tge_rdn_cena_dzis` and `sensor.tge_rdn_cena_jutro`
4. Create automations as needed
5. Add cards to dashboard to visualize the data
