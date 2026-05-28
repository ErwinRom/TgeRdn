#!/usr/bin/env python3
"""
TGE Scheduler - Runs scraper and generates YAML every hour
For Home Assistant integration
"""

import subprocess
import sys
import time
import schedule
import json
from datetime import datetime, timedelta
from pathlib import Path


class TGEScheduler:
    def __init__(self, output_dir: str = "/tmp/tgerdn"):
        """
        Initialize scheduler
        
        Args:
            output_dir: Directory to store output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.script_dir = Path(__file__).parent
    
    def get_date_string(self) -> str:
        """Get today's date in DD-MM-YYYY format"""
        return datetime.now().strftime("%d-%m-%Y")
    
    def get_tomorrow_date_string(self) -> str:
        """Get tomorrow's date in DD-MM-YYYY format"""
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%d-%m-%Y")
    
    def run_scraper(self) -> bool:
        """Run the scraper for today and tomorrow"""
        try:
            dates = [
                ("dzis", self.get_date_string(), "tgerdn_prices.yaml"),
                ("jutro", self.get_tomorrow_date_string(), "tgerdn_prices_tomorrow.yaml")
            ]
            
            for label, date_str, output_file in dates:
                print(f"[{datetime.now().isoformat()}] Running scraper for {label}: {date_str}")
                
                result = subprocess.run(
                    ["python", str(self.script_dir / "scraper.py"), date_str],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"Scraper error for {label}: {result.stderr}", file=sys.stderr)
                    continue
                
                # Parse JSON output
                json_data = json.loads(result.stdout)
                
                # Save JSON to file
                json_filename = output_file.replace(".yaml", ".json")
                json_file = self.output_dir / json_filename
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                print(f"[{datetime.now().isoformat()}] JSON saved to {json_file}")
                
                # Generate YAML
                yaml_file = self.output_dir / output_file
                result = subprocess.run(
                    ["python", str(self.script_dir / "yaml_generator.py"), 
                     str(json_file), str(yaml_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"YAML generator error for {label}: {result.stderr}", file=sys.stderr)
                    continue
                
                print(f"[{datetime.now().isoformat()}] YAML saved to {yaml_file}")
                print(f"[{datetime.now().isoformat()}] Generated {json_data.get('data_points', 0)} data points for {label}")
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"[{datetime.now().isoformat()}] Scraper timeout", file=sys.stderr)
            return False
        except json.JSONDecodeError as e:
            print(f"[{datetime.now().isoformat()}] JSON parse error: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error: {e}", file=sys.stderr)
            return False
    
    def job(self):
        """Scheduled job"""
        success = self.run_scraper()
        status = "✓" if success else "✗"
        print(f"[{datetime.now().isoformat()}] Job completed {status}\n")
    
    def run(self, interval: int = 1, hour: str = "*"):
        """
        Start the scheduler
        
        Args:
            interval: Run every N hours (default: 1)
            hour: Specific hour to run (default: every hour)
        """
        print(f"TGE Scheduler started")
        print(f"Output directory: {self.output_dir}")
        
        # Schedule the job
        if hour == "*":
            schedule.every(interval).hours.do(self.job)
            print(f"Scheduled to run every {interval} hour(s)")
        else:
            schedule.every().day.at(hour).do(self.job)
            print(f"Scheduled to run daily at {hour}")
        
        # Run first job immediately
        print("\nRunning initial job...")
        self.job()
        
        # Keep scheduler running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped")
            sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TGE Scheduler for Home Assistant')
    parser.add_argument('--output-dir', default='/tmp/tgerdn',
                        help='Output directory for generated files')
    parser.add_argument('--interval', type=int, default=1,
                        help='Run every N hours (default: 1)')
    parser.add_argument('--hour', default='*',
                        help='Specific hour to run (HH:MM format, default: every hour)')
    
    args = parser.parse_args()
    
    scheduler = TGEScheduler(output_dir=args.output_dir)
    scheduler.run(interval=args.interval, hour=args.hour)


if __name__ == "__main__":
    main()
