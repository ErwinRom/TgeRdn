#!/usr/bin/env python3
"""
TGE Energy Prices Scraper
Fetches Fixing I prices and delivery dates from the TGE website

Optimizations:
- Uses `datetime.strptime` with error handling for date parsing instead of regex.
- Reuses HTTP connections via a session object.
- Refactors row processing into helper logic per table.

"""

import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime, timedelta
from typing import Optional
import re

def scrape_tge_prices(date_show: Optional[str] = None, type_param: int = 1) -> Optional[dict]:
    if not date_show:
        date_show = datetime.now().strftime("%d-%m-%Y")
    
    query_date_str = (datetime.strptime(date_show, "%d-%m-%Y") 
                        - timedelta(days=1)).strftime("%d-%m-%Y")
    
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
        data = {
            "date_fetched": datetime.now().isoformat(),
            "url": url,
            "delivery_date": datetime.strptime(date_show, "%d-%m-%Y").strftime("%Y-%m-%d"),
            "data_fetched": False,
            "fixing_i_prices": []
        }
        
        tables = soup.find_all('table')
        if not tables:
            print("No tables found on page", file=sys.stderr)
        
        for table in tables:
            text = table.get_text()
            if 'Fixing I' not in text or 'Data dostawy' not in text:
                continue
            
            rows = list(table.find_all('tr'))
            
            # Find Data dostawy column index
            data_dostawy_col_idx = -1
            fixing_i_col_idx = -1
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                if 'Data dostawy' in ''.join(cell_texts):
                    data_dostawy_col_idx = cell_texts.index('Data dostawy')
                
                for col, text in enumerate(cell_texts):
                    if 'Kurs [PLN/MWh]' in text and (col > data_dostawy_col_idx):
                        fixing_i_col_idx = col
                        break
            
            entries = []
            # Process each row to extract valid date entries
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells or len(cells) < 2:
                    continue
                first_cell_text = cells[0].get_text(strip=True)
                
                try:
                    date_text, hour_text = first_cell_text.split('_H', 1)
                    delivery_date = datetime.strptime(date_text, "%Y-%m-%d")
                    hour = int(hour_text)
                    if delivery_date.strftime("%d-%m-%Y") != date_show or not 1 <= hour <= 24:
                        continue

                    price_cell_text = cells[fixing_i_col_idx].get_text(strip=True) if fixing_i_col_idx >= 0 else ""
                    cleaned_price = re.sub(r'\s+', '', price_cell_text).replace(',', '.')
                    price = float(cleaned_price)

                    entries.append({
                        "data_dostawy": delivery_date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "fixing_i_price_pln_kwh": price / 1000
                    })
                except (ValueError, IndexError):
                    continue  # Skip rows with invalid date format
            
            data["fixing_i_prices"].extend(entries)

        data["data_fetched"] = bool(data["fixing_i_prices"])

        if not data["data_fetched"]:
            data["fixing_i_prices"] = [
                {
                    "data_dostawy": data["delivery_date"],
                    "hour": hour,
                    "fixing_i_price_pln_kwh": 0
                }
                for hour in range(1, 25)
            ]
        
        return data
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing data: {e}", file=sys.stderr)
        return None

def main():
    date_show = datetime.now().strftime("%d-%m-%Y")
    type_param = 1
    
    if len(sys.argv) > 1 and sys.argv[1]:
        date_show = sys.argv[1]
    if len(sys.argv) > 2:
        type_param = int(sys.argv[2])
    
    data = scrape_tge_prices(date_show, type_param)
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
if __name__ == "__main__":
    main()
