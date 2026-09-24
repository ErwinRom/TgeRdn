import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import schedule

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
        # Use resolve() to ensure absolute paths work reliably in subprocess calls
        self.script_dir = Path(__file__).resolve().parent

    @staticmethod
    def get_date_string() -> str:
        return datetime.now().strftime("%d-%m-%Y")

    @staticmethod
    def get_tomorrow_date_string() -> str:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%d-%m-%Y")

    def run_scraper(self) -> bool:
        labels_config = [
            ("dzis", self.get_date_string(), "tgerdn_prices.json"),
            ("jutro", self.get_tomorrow_date_string(), "tgerdn_prices_tomorrow.json")
        ]

        success_count = 0
        for label, date_str, output_file in labels_config:
            logger.info(f"Running scraper for {label}: {date_str}")
            try:
                result = subprocess.run(
                    [sys.executable, str(self.script_dir / "scraper.py"), date_str],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"Scraper error for {label}: {result.stderr.strip()}")
                    continue

                json_data = json.loads(result.stdout)
                self._save_json(json_data, output_file)
                success_count += 1

            except subprocess.TimeoutExpired as e:
                logger.error(f"Scraper timed out for {label}: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {label}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {label}: {e}")

        return success_count > 0

    def _save_json(self, json_data, output_file: str):
        json_file = self.output_dir / output_file
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON saved to {json_file}")
        except IOError as e:
            logger.error(f"Failed to save JSON to {json_file}: {e}")

    def job(self):
        success = self.run_scraper()
        status = "✓" if success else "✗"
        logger.info(f"Job completed {status}")

    def run(self, interval: int = 1, hour: str = "*"):
        logger.info("TGE Scheduler started")
        logger.info(f"Output directory: {self.output_dir}")

        try:
            if hour == "*":
                schedule.every(interval).hours.do(self.job)
                log_msg = f"Scheduled to run every {interval} hour(s)"
            else:
                schedule.every().day.at(hour).do(self.job)
                log_msg = f"Scheduled to run daily at {hour}"
        except ValueError as e:
            logger.error(f"Invalid hour format '{hour}'. Expected HH:MM. Falling back to hourly.")
            try:
                schedule.every(interval).hours.do(self.job)
                log_msg = f"Scheduled to run every {interval} hour(s)"
            except Exception as e2:
                logger.error(f"Failed to set up schedule: {e2}")
                return

        logger.info(log_msg)
        self.job()  # Run first job immediately

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute (matches schedule library behavior)
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped")


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
    scheduler.run(interval=args.interval, hour=args.hour)


if __name__ == "__main__":
    main()
