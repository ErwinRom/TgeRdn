import argparse
import asyncio
import json
import logging
import signal
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import schedule
from scraper import scrape_tge_prices

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class TGEScheduler:
    def __init__(self, output_dir: str = "/tmp/tgerdn"):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._tasks = set()

    @staticmethod
    def get_date_string() -> str:
        return datetime.now().strftime("%d-%m-%Y")

    @staticmethod
    def get_tomorrow_date_string() -> str:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%d-%m-%Y")

    async def run_scraper(self) -> bool:
        labels_config = [
            ("dzis", self.get_date_string(), "tgerdn_prices.json"),
            ("jutro", self.get_tomorrow_date_string(), "tgerdn_prices_tomorrow.json")
        ]

        for label, date_str, _ in labels_config:
            logger.info(f"Running scraper for {label}: {date_str}")

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                results = await asyncio.gather(
                    *(scrape_tge_prices(date_str, session=session)
                      for _, date_str, _ in labels_config)
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected error while scraping prices")
            return False

        success_count = 0
        for (label, date_str, output_file), json_data in zip(labels_config, results):
            if json_data is not None:
                data_read = json_data.get("data_fetched", False)
                read_status = "yes" if data_read else "no"
                logger.info(f"Price data read from TGE page for {label} ({date_str}): {read_status}")
                self._save_json(json_data, output_file)
                success_count += 1
            else:
                logger.info(f"Price data read from TGE page for {label} ({date_str}): no (request or parsing failed)")
                logger.error(f"Scraper returned no data for {label}")

        return success_count > 0

    def _save_json(self, json_data, output_file: str):
        json_file = self.output_dir / output_file
        existing_data = None
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            pass
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Could not compare existing JSON at {json_file}: {e}")

        if isinstance(existing_data, dict):
            existing_data.pop("date_fetched", None)
        new_data = dict(json_data)
        new_data.pop("date_fetched", None)

        if existing_data is not None and existing_data == new_data:
            logger.info(f"JSON not updated; data unchanged: {json_file}")
            return

        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON updated: {json_file}")
        except IOError as e:
            logger.error(f"Failed to save JSON to {json_file}: {e}")

    async def job(self):
        success = await self.run_scraper()
        status = "✓" if success else "✗"
        logger.info(f"Job completed {status}")

    def _start_job(self):
        task = asyncio.create_task(self.job())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def run(self, interval: int = 1, hour: str = "*"):
        logger.info("TGE Scheduler started")
        logger.info(f"Output directory: {self.output_dir}")

        schedule.clear()
        try:
            if hour == "*":
                scheduled_job = schedule.every(interval).hours
                log_msg = f"Scheduled to run every {interval} hour(s)"
            else:
                scheduled_job = schedule.every().day.at(hour)
                log_msg = f"Scheduled to run daily at {hour}"
        except ValueError as e:
            logger.error(f"Invalid hour format '{hour}'. Expected HH:MM. Falling back to hourly.")
            try:
                scheduled_job = schedule.every(interval).hours
                log_msg = f"Scheduled to run every {interval} hour(s)"
            except Exception as e2:
                logger.error(f"Failed to set up schedule: {e2}")
                return

        scheduled_job.do(self._start_job)
        logger.info(log_msg)

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        registered_signals = []
        try:
            for stop_signal in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(stop_signal, stop_event.set)
                registered_signals.append(stop_signal)

            self._start_job()
            while not stop_event.is_set():
                schedule.run_pending()
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=1)
                except asyncio.TimeoutError:
                    pass
        finally:
            for task in tuple(self._tasks):
                task.cancel()
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            for stop_signal in registered_signals:
                loop.remove_signal_handler(stop_signal)
            logger.info("Scheduler stopped")


def main():
    parser = argparse.ArgumentParser(description='TGE Scheduler for Home Assistant')
    parser.add_argument('--output-dir', default='/tmp/tgerdn',
                        help='Output directory for generated files (default: /tmp/tgerdn)')
    parser.add_argument('--interval', type=int, default=1,
                        help='Run every N hours (default: 1)')
    parser.add_argument('--hour', default='*',
                        help='Specific hour to run (HH:MM format, default: every hour)')
    args = parser.parse_args()

    scheduler = TGEScheduler(output_dir=args.output_dir)
    asyncio.run(scheduler.run(interval=args.interval, hour=args.hour))


if __name__ == "__main__":
    main()