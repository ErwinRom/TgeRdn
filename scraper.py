#!/usr/bin/env python3
import asyncio

from tge_rdn_scraper.scraper import main, scrape_tge_prices


if __name__ == "__main__":
    asyncio.run(main())
