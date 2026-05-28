#!/bin/bash
# Setup script for TGE scraper - creates cron job for hourly execution

SCRIPT_DIR="/home/erwin/Projekty/TgeRdn"
OUTPUT_DIR="/tmp/tgerdn"
LOG_FILE="/var/log/tgerdn-scraper.log"

# Create output directory
mkdir -p "$OUTPUT_DIR"
chmod 755 "$OUTPUT_DIR"

# Create cron entry for every hour
CRON_JOB="0 * * * * cd $SCRIPT_DIR && /usr/bin/python3 scheduler.py --output-dir $OUTPUT_DIR >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "tgerdn-scraper"; then
    echo "Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron job installed"
fi

# Create log file if needed
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE"
fi

echo "Setup complete!"
echo "Output directory: $OUTPUT_DIR"
echo "Log file: $LOG_FILE"
echo "YAML file: $OUTPUT_DIR/tgerdn_prices.yaml"
echo "JSON file: $OUTPUT_DIR/tgerdn_prices.json"
