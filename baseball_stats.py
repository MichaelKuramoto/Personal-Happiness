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

PLAYER_IDS = {
    'Shohei Ohtani': 660271,
    'Aaron Judge': 592450
}

def get_yesterday_date():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def get_games_for_date(date_str):
    """Get all MLB games for a given date"""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    games = []
    for date_entry in data.get('dates', []):
        for game in date_entry.get('games', []):
            games.append(game.get('gamePk'))
    return games

def get_boxscore(game_pk):
    """Get boxscore for a game"""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def find_player_in_boxscore(boxscore, player_id):
    """Find a player's stats in the boxscore"""
    for team_key in ['away', 'home']:
        team = boxscore.get('teams', {}).get(team_key, {})
        players = team.get('players', {})
        player_key = f"ID{player_id}"
        if player_key in players:
            return players[player_key]
    return None

def format_batting(batting):
    """Format batting stats"""
    if not batting:
        return ""
    text = "Batting:\n"
    text += f"  At Bats: {batting.get('atBats', 0)}\n"
    text += f"  Hits: {batting.get('hits', 0)}\n"
    text += f"  Runs: {batting.get('runs', 0)}\n"
    text += f"  Doubles: {batting.get('doubles', 0)}\n"
    text += f"  Triples: {batting.get('triples', 0)}\n"
    text += f"  Home Runs: {batting.get('homeRuns', 0)}\n"
    text += f"  RBIs: {batting.get('rbi', 0)}\n"
    text += f"  Walks: {batting.get('baseOnBalls', 0)}\n"
    text += f"  Strikeouts: {batting.get('strikeOuts', 0)}\n"
    text += f"  Stolen Bases: {batting.get('stolenBases', 0)}\n"
    return text

def format_pitching(pitching):
    """Format pitching stats"""
    if not pitching:
        return ""
    text = "Pitching:\n"
    text += f"  Innings Pitched: {pitching.get('inningsPitched', '0.0')}\n"
    text += f"  Hits Allowed: {pitching.get('hits', 0)}\n"
    text += f"  Runs Allowed: {pitching.get('runs', 0)}\n"
    text += f"  Earned Runs: {pitching.get('earnedRuns', 0)}\n"
    text += f"  Walks: {pitching.get('baseOnBalls', 0)}\n"
    text += f"  Strikeouts: {pitching.get('strikeOuts', 0)}\n"
    text += f"  Home Runs Allowed: {pitching.get('homeRuns', 0)}\n"
    text += f"  Pitches: {pitching.get('numberOfPitches', 0)}\n"
    text += f"  Strikes: {pitching.get('strikes', 0)}\n"
    return text

def format_season_stats(person_data):
    """Format season stats"""
    text = "\nSeason Stats:\n"
    try:
        seasonStats = person_data.get('seasonStats', {})
        if seasonStats.get('batting'):
            b = seasonStats['batting']
            text += f"  Batting: AVG {b.get('avg','N/A')}, HR {b.get('homeRuns',0)}, RBI {b.get('rbi',0)}, OBP {b.get('obp','N/A')}, SLG {b.get('slg','N/A')}\n"
        if seasonStats.get('pitching'):
            p = seasonStats['pitching']
            text += f"  Pitching: ERA {p.get('era','N/A')}, W-L {p.get('wins',0)}-{p.get('losses',0)}, K {p.get('strikeOuts',0)}, IP {p.get('inningsPitched','N/A')}\n"
    except Exception as e:
        text += f"  Could not fetch season stats: {str(e)}\n"
    return text

def get_player_stats_for_date(player_name, player_id, date_str):
    """Get a player's stats for a specific date"""
    try:
        game_pks = get_games_for_date(date_str)

        if not game_pks:
            return f"=== {player_name.upper()} ===\nNo games played on {date_str}\n"

        stats_text = f"=== {player_name.upper()} ({date_str}) ===\n\n"
        found = False

        for game_pk in game_pks:
            boxscore = get_boxscore(game_pk)
            player_data = find_player_in_boxscore(boxscore, player_id)

            if player_data:
                found = True
                stats = player_data.get('stats', {})

                if stats.get('batting'):
                    stats_text += format_batting(stats['batting'])

                if stats.get('pitching'):
                    stats_text += format_pitching(stats['pitching'])

                stats_text += format_season_stats(player_data)
                break

        if not found:
            stats_text += f"Did not play on {date_str}\n"

        return stats_text

    except Exception as e:
        return f"=== {player_name.upper()} ===\nError: {str(e)}\n"

def send_email(subject, body):
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
    yesterday = get_yesterday_date()
    print(f"Fetching baseball stats for {yesterday}...")

    stats_body = ""
    for player_name, player_id in PLAYER_IDS.items():
        stats = get_player_stats_for_date(player_name, player_id, yesterday)
        stats_body += stats + "\n"

    subject = f"Baseball Stats for {yesterday}"
    body = f"""Baseball Stats for {yesterday}

{stats_body}

Data from MLB StatsAPI
"""

    if send_email(subject, body):
        print("Stats email sent successfully!")
    else:
        print("Failed to send stats email")
        sys.exit(1)

if __name__ == "__main__":
    main()
