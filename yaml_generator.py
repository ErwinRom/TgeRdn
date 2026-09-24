#!/usr/bin/env python3
"""
TGE Energy Prices Scraper
Fetches Fixing I prices and delivery dates from the TGE website

Optimizations:
- Uses `datetime.strptime` with error handling for accurate date parsing.
- Reuses HTTP connections via a session object.
- Refactored row processing logic per table to improve efficiency.

"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from typing import Optional
import re
import sys
import argparse
import yaml

def scrape_tge_prices(date_show: Optional[str] = None, type_param: int = 1) -> dict:
    """
    Scrape TGE electricity prices and delivery dates.
    
    Args:
        date_show: Date parameter in format DD-MM-YYYY. If omitted, today's date is used.
        type_param: Type parameter (1 for standard)
    
    Returns:
        Dictionary containing prices and delivery dates
    """
    
    if not date_show:
        date_show = datetime.now().strftime("%d-%m-%Y")
    
    query_date_str = (datetime.strptime(date_show, "%d-%m-%Y") - timedelta(days=1)).strftime("%d-%m-%Y")
    
    url = f"https://tge.pl/energia-elektryczna-rdn?dateShow={query_date_str}&type={type_param}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    session = None
    if not session:
        session = requests.Session()
        session.headers.update(headers)
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        prices_by_date = {}
        tables = soup.find_all('table')
        
        if not tables:
            print("No tables found on page", file=sys.stderr)
            return prices_by_date
        
        for table in tables:
            text = table.get_text()
            if 'Fixing I' not in text or 'Data dostawy' not in text:
                continue
            
            rows = [row.extract() for row in table.find_all('tr')]
            
            data_dostawy_col_idx = -1
            fixing_i_col_idx = -1
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells or len(cells) < 2:
                    continue
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                if 'Data dostawy' in ''.join(cell_texts):
                    data_dostawy_col_idx = cell_texts.index('Data dostawy')
                
                for col, text in enumerate(cell_texts):
                    if 'Kurs [PLN/MWH]' in text and (col > data_dostawy_col_idx):
                        fixing_i_col_idx = col
                        break
            
            price_entries = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells or len(cells) < 2:
                    continue
                first_cell_text = cells[0].get_text(strip=True)
                
                try:
                    dt = datetime.strptime(first_cell_text.strip(), "%d-%m-%Y")
                    
                    # Use actual current date for business_date and period calculations
                    today_str = dt.strftime("%Y-%m-%d")
                    hour_24 = int(first_cell_text.split('_H')[-1].strip())
                    
                    if 0 <= hour_24 < 24:
                        price_cell_text = cells[fixing_i_col_idx].get_text(strip=True) if fixing_i_col_idx < len(cells) else ''
                        
                        cleaned_price = re.sub(r'\s+', '', price_cell_text).replace(',', '.')
                        try:
                            price = float(cleaned_price)
                        except ValueError:
                            price = cleaned_price
                        
                        entry = {
                            "hour": hour_24,
                            "price": price
                        }
                        prices_by_date[dt.strftime("%d-%m-%Y")] = prices_by_date.get(dt.strftime("%d-%m-%Y"), [])
                        prices_by_date[dt.strftime("%d-%m-%Y")].append(entry)
                except ValueError:
                    continue  # Skip rows with invalid date format
            
            for date_str in sorted(prices_by_date.keys()):
                hourly_prices = sorted(prices_by_date[date_str], key=lambda x: x["hour"])
                
                year, month, day = map(int, date_str.split('-'))
                price_entries.extend([
                    {
                        "dtime": f"{year}-{month:02d}-{day:02d} {hour_24:02d}:00",
                        "period": f"{(hour_24 - 1):02d}:00-{hour_24:02d}:00",
                        "rce_pln": price,
                        "business_date": today_str
                    }
                    for hour in hourly_prices
                ])
        
        return {
            "fixing_i_prices": prices_by_date.get("FIXING_I_PRICES", []),
            **price_entries
        }
    
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"Error parsing data: {e}", file=sys.stderr)
        return {}

def generate_yaml_from_json(json_data: dict, output_file: Optional[str] = None) -> str:
    """
    Convert TGE JSON data to Home Assistant YAML format
    
    Args:
        json_data: Dictionary with 'fixing_i_prices' list
        output_file: File path to write YAML to
        
    Returns:
        YAML formatted string
    """
    
    if not isinstance(json_data, dict) or "fixing_i_prices" not in json_data:
        raise ValueError("Invalid JSON data structure")
    
    prices = json_data["fixing_i_prices"]
    data = {
        "last_update": datetime.now().isoformat(),
        "data_points": len(prices),
        "prices": [],
        "unit_of_measurement": "PLN/kWh",
        "icon": "mdi:cash",
        "friendly_name": "TGE RDN - Cena dzis"
    }
    
    for entry in prices:
        date_obj = datetime.strptime(entry["data_dostawy"], "%Y-%m-%d")
        hour = int(entry["hour"])
        data["prices"].append({
            "dtime": datetime(date_obj.year, date_obj.month, date_obj.day, hour % 24, 0).isoformat(),
            "period": f"{(hour - 1):02d}:00-{hour:02d}:00",
            "rce_pln": entry["fixing_i_price_pln_kwh"],
            "business_date": date_obj.strftime("%Y-%m-%d")
        })
    
    return yaml.dump(data, allow_unicode=True, sort_keys=False)

def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Convert TGE price JSON to Home Assistant YAML"
    )
    parser.add_argument("input_file", nargs="?", help="Input JSON file")
    parser.add_argument("output_file", nargs="?", help="Output YAML file")
    parser.add_argument("-f", "--input", dest="input_option", help="Input JSON file")
    parser.add_argument("-o", "--output", dest="output_option", help="Output YAML file")
    args = parser.parse_args()

    input_file = args.input_option or args.input_file
    output_file = args.output_option or args.output_file

    if not input_file:
        parser.error("an input JSON file is required")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        yaml_output = generate_yaml_from_json(json_data, output_file)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(yaml_output)
            print(f"YAML written to {output_file}", file=sys.stderr)
        else:
            print(yaml_output)
    
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
