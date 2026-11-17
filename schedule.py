"""Conservative ESPN scoreboard enrichment for verified scheduled game starts.

ESPN's public site endpoint is unofficial and may change. Never infer a start
from Kalshi market close/expiration, or from an ambiguous team match.
"""
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

LEAGUES = {
    'NBA': ('basketball', 'nba'), 'WNBA': ('basketball', 'wnba'),
    'CBB': ('basketball', 'mens-college-basketball'),
    'WCBB': ('basketball', 'womens-college-basketball'),
    'NFL': ('football', 'nfl'), 'NCAAF': ('football', 'college-football'),
    'MLB': ('baseball', 'mlb'), 'NHL': ('hockey', 'nhl'),
    'MLS': ('soccer', 'usa.1'),
}


def _norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s or '').casefold()).strip()


def _contains_team(text, team):
    """Match complete team names only, never city alone or abbreviations."""
    t = _norm(text)
    name = _norm(team)
    return bool(name and len(name.split()) >= 2 and re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', t))


def scoreboard_games(session, level, selected_day, tz_name):
    if level not in LEAGUES:
        return []
    sport, league = LEAGUES[level]
    # Look one day either side to catch local-day / source-day boundaries.
    dates = [(selected_day + timedelta(days=offset)).strftime('%Y%m%d') for offset in (-1, 0, 1)]
    games = {}
    for day in dates:
        url = f'https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard'
        try:
            response = session.get(url, params={'dates': day, 'limit': 500}, timeout=12)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            continue
        for event in data.get('events', []):
            competition = (event.get('competitions') or [{}])[0]
            teams = [entry.get('team', {}).get('displayName', '') for entry in competition.get('competitors', [])]
            raw = event.get('date') or competition.get('date')
            if len(teams) != 2 or not all(teams) or not raw:
                continue
            try:
                start = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                if start.tzinfo is None or start.astimezone(ZoneInfo(tz_name)).date() != selected_day:
                    continue
            except (ValueError, KeyError):
                continue
            games[event.get('id', f'{level}-{raw}-{teams[0]}')] = {'teams': teams, 'start': start.isoformat(), 'level': level}
    return list(games.values())


def enrich_start_times(rows, selected_day, tz_name, session=None):
    """Enrich only missing starts, requiring exactly one two-team schedule match."""
    from datefilter import parse_start
    from classify import classify
    own_session = session is None
    session = session or requests.Session()
    try:
        levels = {classify(r)[1] for r in rows if not parse_start(r.get('game_start_time'))}
        schedules = {level: scoreboard_games(session, level, selected_day, tz_name) for level in levels if level in LEAGUES}
        output = []
        for original in rows:
            r = dict(original)
            if parse_start(r.get('game_start_time')):
                output.append(r)
                continue
            level = classify(r)[1]
            # Market title can describe a team only. Use event title when available;
            # never use ticker abbreviations to guess a matchup.
            text = ' '.join(str(r.get(k, '') or '') for k in ('event_title', 'event_subtitle', 'title'))
            matches = [game for game in schedules.get(level, []) if all(_contains_team(text, team) for team in game['teams'])]
            if len(matches) == 1:
                r['game_start_time'] = matches[0]['start']
                r['start_time_source'] = 'ESPN scoreboard (two-team exact match)'
            output.append(r)
        return output
    finally:
        if own_session:
            session.close()
