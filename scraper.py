#!/usr/bin/env python3
"""
TGE Energy Prices Scraper
Fetches Fixing I prices and delivery dates from the TGE website
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime, timedelta
from typing import Optional
import re

def scrape_tge_prices(date_show: Optional[str] = None, type_param: int = 1) -> Optional[dict]:
    """
    Scrape TGE electricity prices and delivery dates.
    
    Args:
        date_show: Date parameter in format DD-MM-YYYY. If omitted, today's date is used.
        type_param: Type parameter (1 for standard)
    
    Returns:
        Dictionary containing prices and delivery dates, or None if failed
    """
    
    if not date_show:
        date_show = datetime.now().strftime("%d-%m-%Y")
    
    # TGE returns prices for the NEXT day, so we need to query one day before
    # to get prices for the requested date
    date_obj = datetime.strptime(date_show, "%d-%m-%Y")
    query_date = date_obj - timedelta(days=1)
    query_date_str = query_date.strftime("%d-%m-%Y")
    
    url = f"https://tge.pl/energia-elektryczna-rdn?dateShow={query_date_str}&type={type_param}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"Fetching: {url}", file=sys.stderr)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the main data table
        data = {
            "date_fetched": datetime.now().isoformat(),
            "url": url,
            "fixing_i_prices": []
        }
        
        # Find all tables
        tables = soup.find_all('table')
        
        if not tables:
            print("No tables found on page", file=sys.stderr)
            return data
        
        # Look for the table with "Fixing I" data (typically table 2)
        for table_idx, table in enumerate(tables):
            table_text = table.get_text()
            
            # Check if this table contains Fixing I data
            if 'Fixing I' not in table_text or 'Data dostawy' not in table_text:
                continue
            
            print(f"Found relevant data in table {table_idx}", file=sys.stderr)
            rows = table.find_all('tr')
            
            # Find header row to identify column indices
            fixing_i_col_idx = -1
            data_dostawy_col_idx = -1
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                row_text = [cell.get_text(strip=True) for cell in cells]
                
                # Check if this is the sub-header row
                if 'Data dostawy' in row_text:
                    data_dostawy_col_idx = row_text.index('Data dostawy')
                    # Find Kurs [PLN/MWh] column for Fixing I
                    for col_idx, cell_text in enumerate(row_text):
                        if 'Kurs [PLN/MWh]' in cell_text and col_idx > data_dostawy_col_idx:
                            # This is the first "Kurs [PLN/MWh]" after Data dostawy, which is Fixing I
                            fixing_i_col_idx = col_idx
                            break
                    print(f"Header: Data dostawy at col {data_dostawy_col_idx}, Fixing I price at col {fixing_i_col_idx}", file=sys.stderr)
                
                # Parse data rows (not header rows)
                elif len(row_text) > 0 and data_dostawy_col_idx >= 0 and fixing_i_col_idx >= 0:
                    # Check if this looks like a data row (first cell should be a date or hour)
                    first_cell = row_text[0]
                    
                    if re.match(r'\d{4}-\d{2}-\d{2}', first_cell):  # Looks like a date
                        delivery_date = row_text[data_dostawy_col_idx] if data_dostawy_col_idx < len(row_text) else ""
                        price_str = row_text[fixing_i_col_idx] if fixing_i_col_idx < len(row_text) else ""
                        
                        # Parse price (remove spaces and convert comma to dot)
                        price = None
                        if price_str:
                            try:
                                # Remove spaces and convert Polish notation (comma) to dot
                                price = float(price_str.replace(' ', '').replace(',', '.'))
                            except ValueError:
                                price = price_str
                        
                        entry = {
                            "data_dostawy": delivery_date,
                            "fixing_i_price_pln_mwh": price
                        }
                        data["fixing_i_prices"].append(entry)
        
        return data
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing data: {e}", file=sys.stderr)
        return None

def main():
    """Main entry point"""
    
    # Default parameters
    date_show = datetime.now().strftime("%d-%m-%Y")
    type_param = 1
    
    # Allow command-line arguments
    if len(sys.argv) > 1 and sys.argv[1]:
        date_show = sys.argv[1]
    if len(sys.argv) > 2:
        type_param = int(sys.argv[2])
    
    data = scrape_tge_prices(date_show, type_param)
    
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"error": "Failed to fetch data"}, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
