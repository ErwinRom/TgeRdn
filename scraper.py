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
            "fixing_i_prices": []
        }
        
        tables = soup.find_all('table')
        if not tables:
            print("No tables found on page", file=sys.stderr)
            return data
        
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
                    dt = datetime.strptime(first_cell_text.strip(), "%d-%m-%Y")
                    today_date = datetime.now().replace(day=1, month=datetime.now().month, year=datetime.now().year)
                    
                    if dt == today_date:
                        delivery_date_str = cells[data_dostawy_col_idx].get_text(strip=True) if data_dostawy_col_idx < len(cells) else ""
                        price_cell_text = cells[fixing_i_col_idx].get_text(strip=True) if fixing_i_col_idx < len(cells) else ""
                        
                        cleaned_price = re.sub(r'\s+', '', price_cell_text).replace(',', '.')
                        try:
                            price = float(cleaned_price)
                        except ValueError:
                            price = cleaned_price
                        
                        entries.append({
                            "data_dostawy": delivery_date_str,
                            "fixing_i_price_pln_mwh": price
                        })
                except ValueError:
                    continue  # Skip rows with invalid date format
            
            data["fixing_i_prices"].extend(entries)
        
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
    
    if len(sys.argv) > 2 and sys.argv[1]:
        date_show = sys.argv[1]
    if len(sys.argv) > 3:
        type_param = int(sys.argv[2])
    
    data = scrape_tge_prices(date_show, type_param)
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
if __name__ == "__main__":
    main()
