#!/bin/bash
# Daily baseball stats runner for 5am PST (1pm UTC)

export BASEBALL_STATS_SENDER_EMAIL="roykuramoto@gmail.com"
export BASEBALL_STATS_SENDER_PASSWORD="HelpMichael2026$"
export BASEBALL_STATS_RECIPIENT_EMAIL="michaelkuramoto@gmail.com"
export BASEBALL_STATS_TIMEZONE="PST"
export BASEBALL_STATS_SCHEDULE_HOUR="5"

# Log file
LOG_FILE="/home/user/Personal-Happiness/baseball_stats.log"

# Run the script and log output
{
    echo "$(date): Running baseball stats fetch..."
    python3 /home/user/Personal-Happiness/baseball_stats.py
    echo "$(date): Completed"
} >> "$LOG_FILE" 2>&1
