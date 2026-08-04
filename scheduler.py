import subprocess
import sys
import time
import schedule
import json
from datetime import datetime, timedelta
from pathlib import Path


class TGEScheduler:
    def __init__(self, output_dir: str = "/tmp/tgerdn"):
        self.output_dir = Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.script_dir = Path(__file__).parent

    @staticmethod
    def get_date_string() -> str:
        return datetime.now().strftime("%d-%m-%Y")

    @staticmethod
    def get_tomorrow_date_string() -> str:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%d-%m-%Y")

    def run_scraper(self) -> bool:
        try:
            for label, date_str, output_file in [
                ("dzis", self.get_date_string(), "tgerdn_prices.yaml"),
                ("jutro", self.get_tomorrow_date_string(), "tgerdn_prices_tomorrow.yaml")
            ]:
                print(f"[{datetime.now().isoformat()}] Running scraper for {label}: {date_str}")
                
                # Run the scraper
                result = subprocess.run(
                    [sys.executable, str(self.script_dir / "scraper.py"), date_str],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    print(f"Scraper error for {label}: {result.stderr}", file=sys.stderr)
                    continue
                
                # Save JSON to file and generate YAML
                json_data = json.loads(result.stdout)
                self._save_json(json_data, output_file)
                self._generate_yaml(json_data, output_file)

            return True

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"[{datetime.now().isoformat()}] Error: {e}", file=sys.stderr)
            return False

    def _save_json(self, json_data, output_file):
        json_filename = output_file.replace(".yaml", ".json")
        json_file = self.output_dir / json_filename
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"[{datetime.now().isoformat()}] JSON saved to {json_file}")

    def _generate_yaml(self, json_data, output_file):
        yaml_file = self.output_dir / output_file
        result = subprocess.run(
            ["python", str(self.script_dir / "yaml_generator.py"), 
             str(yaml_file.with_suffix('.json')), str(yaml_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"YAML generator error for {output_file}: {result.stderr}", file=sys.stderr)
        else:
            print(f"[{datetime.now().isoformat()}] YAML saved to {yaml_file}")
            print(f"[{datetime.now().isoformat()}] Generated {json_data.get('data_points', 0)} data points")

    def job(self):
        success = self.run_scraper()
        status = "✓" if success else "✗"
        print(f"[{datetime.now().isoformat()}] Job completed {status}\n")

    def run(self, interval: int = 1, hour: str = "*"):
        print(f"TGE Scheduler started")
        print(f"Output directory: {self.output_dir}")

        schedule.every(interval).hours.do(self.job) if hour == "*" else schedule.every().day.at(hour).do(self.job)
        
        print(f"Scheduled to run every {interval} hour(s)" if hour == "*" else f"Scheduled to run daily at {hour}")
        
        self.job()  # Run first job immediately
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped")
            sys.exit(0)


def main():
    import argparse
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
