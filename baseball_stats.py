#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import sys
import time

SENDER_EMAIL = os.environ.get('BASEBALL_STATS_SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('BASEBALL_STATS_SENDER_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('BASEBALL_STATS_RECIPIENT_EMAIL')

# Better headers to avoid 403 blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.baseball-reference.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def scrape_player_stats(player_name):
    """Scrape Baseball-Reference for player stats with retries"""
    try:
        search_url = f"https://www.baseball-reference.com/search/search.fcgi?search={player_name}"

        # Retry logic for 403 errors
        for attempt in range(3):
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=10)
                if response.status_code == 403:
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise

        soup = BeautifulSoup(response.content, 'html.parser')
        player_link = soup.find('a', href=lambda x: x and '/players/' in x)

        if not player_link:
            return f"Could not find {player_name} on Baseball-Reference"

        time.sleep(1)  # Be polite to the server

        player_url = f"https://www.baseball-reference.com{player_link['href']}"
        player_response = requests.get(player_url, headers=HEADERS, timeout=10)
        player_response.raise_for_status()

        player_soup = BeautifulSoup(player_response.content, 'html.parser')
        stats = extract_stats(player_soup, player_name)
        return stats

    except Exception as e:
        return f"Could not fetch {player_name} stats: {str(e)}"

def extract_stats(soup, player_name):
    """Extract batting and pitching stats from player page"""
    stats_text = f"=== {player_name.upper()} ===\n\n"

    try:
        # Try to find 2024/2025 stats
        tables = soup.find_all('table')
        for table in tables:
            if 'batting' in str(table).lower() or 'pitching' in str(table).lower():
                rows = table.find_all('tr')
                # Get most recent season stats
                if rows:
                    stats_text += extract_table_data(table, player_name)

    except Exception as e:
        stats_text += f"Could not parse detailed stats: {str(e)}\n"

    return stats_text

def extract_table_data(table, player_name):
    """Extract data from stats table"""
    text = ""
    headers = []
    rows = table.find_all('tr')

    # Get headers
    header_row = rows[0] if rows else None
    if header_row:
        headers = [th.text for th in header_row.find_all(['th', 'td'])]

    # Get last few rows (recent stats)
    for row in rows[-3:]:
        cells = row.find_all(['td', 'th'])
        if cells:
            row_data = [cell.text for cell in cells]
            text += " | ".join(row_data[:10]) + "\n"

    return text

def send_email(subject, body):
    """Send email with stats"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Send via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {RECIPIENT_EMAIL}")
        return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def main():
    """Fetch stats and send email"""
    yesterday = get_yesterday_date()
    print(f"Fetching baseball stats for {yesterday}...")

    # Fetch stats for both players
    ohtani_stats = scrape_player_stats("Shohei Ohtani")
    judge_stats = scrape_player_stats("Aaron Judge")

    # Compose email
    subject = f"Baseball Stats for {yesterday}"
    body = f"""Baseball Stats for {yesterday}

{ohtani_stats}

{judge_stats}

Note: Box scores include both batting and pitching stats where applicable.
"""

    # Send email
    if send_email(subject, body):
        print("Stats email sent successfully!")
    else:
        print("Failed to send stats email")
        sys.exit(1)

if __name__ == "__main__":
    main()
