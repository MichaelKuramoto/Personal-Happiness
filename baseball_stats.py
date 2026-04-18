#!/usr/bin/env python3
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import sys

SENDER_EMAIL = os.environ.get('BASEBALL_STATS_SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('BASEBALL_STATS_SENDER_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('BASEBALL_STATS_RECIPIENT_EMAIL')

# Known player IDs
PLAYER_IDS = {
    'Shohei Ohtani': 660271,
    'Aaron Judge': 592450
}

def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def get_player_stats_for_date(player_name, player_id, date_str):
    """Get player stats for a specific date using game data"""
    try:
        # Get games for the date
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        stats_text = f"=== {player_name.upper()} ({date_str}) ===\n\n"
        found = False

        for game in games:
            for team_key in ['away', 'home']:
                team = game.get(team_key, {})
                for player in team.get('players', {}).values():
                    if player.get('person', {}).get('id') == player_id:
                        found = True
                        stats = player.get('stats', {})

                        # Batting stats
                        if 'batting' in stats:
                            batting = stats['batting']
                            stats_text += "Batting:\n"
                            stats_text += f"  At Bats: {batting.get('atBats', 'N/A')}\n"
                            stats_text += f"  Hits: {batting.get('hits', 'N/A')}\n"
                            stats_text += f"  Doubles: {batting.get('doubles', 'N/A')}\n"
                            stats_text += f"  Home Runs: {batting.get('homeRuns', 'N/A')}\n"
                            stats_text += f"  RBIs: {batting.get('rbi', 'N/A')}\n"
                            stats_text += f"  Strikeouts: {batting.get('strikeOuts', 'N/A')}\n"
                            stats_text += f"  AVG: {batting.get('avg', 'N/A')}\n\n"

                        # Pitching stats
                        if 'pitching' in stats:
                            pitching = stats['pitching']
                            stats_text += "Pitching:\n"
                            stats_text += f"  Innings Pitched: {pitching.get('inningsPitched', 'N/A')}\n"
                            stats_text += f"  Wins: {pitching.get('wins', 'N/A')}\n"
                            stats_text += f"  Losses: {pitching.get('losses', 'N/A')}\n"
                            stats_text += f"  ERA: {pitching.get('era', 'N/A')}\n"
                            stats_text += f"  Strikeouts: {pitching.get('strikeOuts', 'N/A')}\n"
                            stats_text += f"  Pitches: {pitching.get('numberOfPitches', 'N/A')}\n\n"

        if not found:
            stats_text = f"No game found for {player_name} on {date_str}"

        return stats_text

    except Exception as e:
        return f"Error fetching {player_name} stats: {str(e)}"

def send_email(subject, body):
    """Send email with stats"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

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

    stats_body = ""

    # Fetch stats for both players
    for player_name, player_id in PLAYER_IDS.items():
        stats = get_player_stats_for_date(player_name, player_id, yesterday)
        stats_body += stats + "\n"

    # Compose email
    subject = f"Baseball Stats for {yesterday}"
    body = f"""Baseball Stats for {yesterday}

{stats_body}

Data from MLB StatsAPI
"""

    # Send email
    if send_email(subject, body):
        print("Stats email sent successfully!")
    else:
        print("Failed to send stats email")
        sys.exit(1)

if __name__ == "__main__":
    main()
