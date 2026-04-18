#!/usr/bin/env python3
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import sys
import json

SENDER_EMAIL = os.environ.get('BASEBALL_STATS_SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('BASEBALL_STATS_SENDER_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('BASEBALL_STATS_RECIPIENT_EMAIL')

# MLB StatsAPI - official, free, no blocking
MLB_API = "https://statsapi.mlb.com/api/v1"

def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def get_player_id(player_name):
    """Get MLB player ID by name"""
    try:
        url = f"{MLB_API}/people/search?names={player_name}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('people'):
            return data['people'][0]['id']
        return None
    except Exception as e:
        print(f"Error finding player {player_name}: {str(e)}")
        return None

def get_player_stats(player_name, stat_type='season'):
    """Get player stats from MLB API"""
    try:
        player_id = get_player_id(player_name)
        if not player_id:
            return f"Could not find {player_name}"

        # Get player info
        url = f"{MLB_API}/people/{player_id}?hydrate=stats(group=[hitting,pitching])"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        player = data.get('people', [{}])[0]
        stats_text = f"=== {player.get('fullName', player_name).upper()} ===\n\n"

        # Extract stats
        if 'stats' in player:
            for stat_group in player['stats']:
                group_type = stat_group.get('group', {}).get('displayName', '')
                stat_data = stat_group.get('stats', {})

                if group_type:
                    stats_text += f"{group_type}:\n"

                # Format key stats
                if group_type == 'hitting':
                    stats_text += format_hitting_stats(stat_data)
                elif group_type == 'pitching':
                    stats_text += format_pitching_stats(stat_data)

                stats_text += "\n"

        return stats_text if stats_text != f"=== {player.get('fullName', player_name).upper()} ===\n\n" else f"No stats available for {player_name}"

    except Exception as e:
        return f"Error fetching {player_name} stats: {str(e)}"

def format_hitting_stats(stats):
    """Format hitting stats"""
    text = ""
    key_stats = ['gamesPlayed', 'atBats', 'hits', 'doubles', 'triples', 'homeRuns',
                 'rbi', 'baseOnBalls', 'strikeOuts', 'avg', 'obp', 'slg']

    for stat_key in key_stats:
        if stat_key in stats:
            value = stats[stat_key]
            text += f"  {stat_key}: {value}\n"

    return text

def format_pitching_stats(stats):
    """Format pitching stats"""
    text = ""
    key_stats = ['gamesPlayed', 'inningsPitched', 'wins', 'losses', 'era', 'strikeOuts',
                 'walks', 'hits', 'homeRuns', 'completeGames', 'shutouts']

    for stat_key in key_stats:
        if stat_key in stats:
            value = stats[stat_key]
            text += f"  {stat_key}: {value}\n"

    return text

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

    # Fetch stats for both players
    ohtani_stats = get_player_stats("Shohei Ohtani")
    judge_stats = get_player_stats("Aaron Judge")

    # Compose email
    subject = f"Baseball Stats for {yesterday}"
    body = f"""Baseball Stats for {yesterday}

{ohtani_stats}

{judge_stats}

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
