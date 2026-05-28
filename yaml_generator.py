#!/usr/bin/env python3
"""
TGE YAML Generator for Home Assistant
Converts TGE price data to Home Assistant entity YAML format
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import yaml
import sys


def generate_yaml_from_json(json_data: dict, output_file: str = None) -> str:
    """
    Convert TGE JSON data to Home Assistant YAML format
    
    Args:
        json_data: Dictionary with 'fixing_i_prices' list
        output_file: Optional file path to write YAML to
    
    Returns:
        YAML formatted string
    """
    
    if not json_data or "fixing_i_prices" not in json_data:
        raise ValueError("Invalid JSON data structure")
    
    prices = json_data["fixing_i_prices"]
    
    if not prices:
        raise ValueError("No price data available")
    
    # Get timezone-aware current time (assume Poland timezone UTC+2 in summer, +1 in winter)
    # For simplicity, use UTC+2 (CEST)
    now = datetime.now(timezone(timedelta(hours=2)))
    
    # Parse delivery dates and organize by date
    prices_by_date = {}
    for entry in prices:
        # Format: "2026-05-29_H01" -> extract date and hour
        data_dostawy = entry["data_dostawy"]  # e.g., "2026-05-29_H01"
        
        # Parse the data_dostawy format
        if "_H" in data_dostawy:
            date_part, hour_part = data_dostawy.split("_H")
            hour_num = int(hour_part)
            prices_by_date[date_part] = prices_by_date.get(date_part, [])
            prices_by_date[date_part].append({
                "hour": hour_num,
                "price": entry["fixing_i_price_pln_mwh"]
            })
    
    # Get today's date (for business_date field)
    today_str = now.strftime("%Y-%m-%d")
    
    # Build price entries with hourly format
    # The prices we fetch are for tomorrow, so we use them as "today's available prices"
    price_entries = []
    
    for date_str in sorted(prices_by_date.keys()):
        hourly_prices = sorted(prices_by_date[date_str], key=lambda x: x["hour"])
        
        for hourly_data in hourly_prices:
            hour = hourly_data["hour"]
            price = hourly_data["price"]
            
            # Convert hour number (1-24) to 24-hour format
            hour_24 = hour % 24
            
            # Create datetime for this hour
            year, month, day = date_str.split("-")
            dtime = datetime(int(year), int(month), int(day), hour_24, 0, 0)
            dtime_str = dtime.strftime("%Y-%m-%d %H:%M:%S")
            
            # Period format: "HH:MM - HH:MM"
            hour_start = hour_24 - 1 if hour_24 > 0 else 23
            hour_end = hour_24
            period = f"{hour_start:02d}:00 - {hour_end:02d}:00"
            
            # Use today's date for business_date
            entry = {
                "dtime": dtime_str,
                "period": period,
                "rce_pln": price,
                "business_date": today_str
            }
            price_entries.append(entry)
    
    # Build the complete YAML structure
    yaml_data = {
        "last_update": now.isoformat(),
        "data_points": len(price_entries),
        "prices": price_entries,
        "unit_of_measurement": "PLN/MWh",
        "icon": "mdi:cash",
        "friendly_name": "TGE RDN - Cena dzis"
    }
    
    # Convert to YAML string with custom formatting
    yaml_str = yaml.dump(yaml_data, 
                         default_flow_style=False,
                         allow_unicode=True,
                         sort_keys=False)
    
    # Write to file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_str)
        print(f"YAML written to {output_file}", file=sys.stderr)
    
    return yaml_str


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python yaml_generator.py <json_file> [output_yaml_file]", file=sys.stderr)
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Read JSON from file or stdin
        if json_file == "-":
            json_data = json.load(sys.stdin)
        else:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        
        yaml_output = generate_yaml_from_json(json_data, output_file)
        print(yaml_output)
        
    except FileNotFoundError:
        print(f"Error: File {json_file} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
