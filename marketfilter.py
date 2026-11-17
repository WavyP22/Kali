"""Conservative game-market screening; unknowns do not enter daily picks."""
import re

FUTURES = re.compile(r"\b(expansion|expand|coach(?:ing)?|head coach|fired|hire[ds]?|retire|retirement|championship|champion|win the (?:title|league|conference|division|finals)|mvp|rookie of the year|award|draft|trade deadline|next season|playoffs|playoff berth|make the playoffs|president|election|before (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|by (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b",re.I)
TOTALS = re.compile(r"\b(over|under|total points|total goals|total runs|combined points|combined goals|combined runs)\b",re.I)
SPREAD = re.compile(r"(?:\bspread\b|\bhandicap\b|\bwin by (?:more than|at least|over|\d)|\b(?:cover|covers)\b|(?:^|\s)[+-]\d+(?:\.5)?(?:\s|$)|\b\d+(?:\.5)?\+?\s*(?:point|points|goal|goals|run|runs)\b)",re.I)
WIN = re.compile(r"\b(wins?|winner|beat|beats|defeat|defeats|moneyline|to win|will .* win)\b",re.I)
PERIOD = re.compile(r"\b(1st half|first half|2nd half|second half|quarter|period|inning)\b",re.I)

def market_type(row):
    title=str(row.get('title') or '')
    event=str(row.get('event_title') or '')
    combined=title+' '+event
    if FUTURES.search(combined):return 'Excluded: futures/non-game'
    if TOTALS.search(title):return 'Totals (Over/Under)'
    if SPREAD.search(title):return 'Game Lines (Spreads)'
    if WIN.search(title):return 'Moneyline / Winner'
    return 'Other / Needs review'

def game_eligible(row):
    return market_type(row) in ('Game Lines (Spreads)','Totals (Over/Under)','Moneyline / Winner')

def preference_rank(row):
    return {'Game Lines (Spreads)':0,'Moneyline / Winner':1,'Totals (Over/Under)':2}.get(market_type(row),3)
