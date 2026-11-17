"""Read-only discovery. No trading credentials or endpoints."""
import requests
import time
from classify import classify
from datetime import datetime, timezone
from engine import market_price
BASE = 'https://api.elections.kalshi.com/trade-api/v2'

class ScanRateLimited(Exception):
    """Stop the scan when Kalshi says to slow down."""

_last_call = 0.0

def fetch_json(session, path, params=None):
    """Space Kalshi requests, retry 429 briefly, then stop rather than hammering."""
    global _last_call
    for attempt in range(3):
        wait = max(0, 0.65 - (time.monotonic() - _last_call))
        if wait: time.sleep(wait)
        _last_call = time.monotonic()
        r = session.get(BASE + path, params=params, timeout=22,
                        headers={'User-Agent': 'KalshiGuardResearch/7.2'})
        if r.status_code == 429:
            if attempt == 2:
                raise ScanRateLimited('Kalshi is busy (429). Scan stopped to avoid more requests. Wait a few minutes and try again.')
            retry = r.headers.get('Retry-After', '')
            try: delay = min(15.0, max(1.0, float(retry)))
            except (TypeError, ValueError): delay = 2.0 * (attempt + 1)
            time.sleep(delay)
            continue
        r.raise_for_status()
        return r.json()


def sports_series(session, max_pages=10):
    """Discover sports series from Kalshi series metadata, not hardcoded league tickers."""
    found={};cursor=None;pages=0;errors=[]
    for _ in range(max_pages):
        params={'category':'Sports','limit':200}
        if cursor:params['cursor']=cursor
        try:data=fetch_json(session,'/series',params)
        except ScanRateLimited as e:
            errors.append(str(e));break
        except (requests.RequestException,ValueError) as e:
            errors.append(f'Series discovery failed: {type(e).__name__}: {e}');break
        pages+=1
        for s in data.get('series',[]):
            if str(s.get('category','')).casefold()!='sports':continue
            t=s.get('ticker')
            if t:found[t]=s
        nxt=data.get('cursor')
        if not nxt or nxt==cursor:break
        cursor=nxt
    return list(found.values()),{'pages':pages,'truncated':bool(cursor and pages>=max_pages),'errors':errors}

def scan_series(session,series,max_pages=2,max_series=60):
    rows=[];errors=[];scanned=0;page_count=0
    # Prioritize recognizable game leagues, instead of the first arbitrary 60 series.
    priority = {'NBA': 0, 'WNBA': 1, 'CBB': 2, 'WCBB': 3,
                'NFL': 4, 'NCAAF': 5, 'NHL': 6, 'MLB': 7, 'MLS': 8}
    def rank(item):
        sport, level = classify({'sport': item.get('title', ''),
                                 'series_ticker': item.get('ticker', '')})
        return (priority.get(level, 50), str(item.get('ticker', '')))
    selected=sorted(series, key=rank)[:max_series]
    rate_limited=False
    for s in selected:
        ticker=s.get('ticker','')
        cursor=None
        for _ in range(max_pages):
            params={'series_ticker':ticker,'status':'open','limit':200,'with_nested_markets':'true'}
            if cursor:params['cursor']=cursor
            try:data=fetch_json(session,'/events',params)
            except ScanRateLimited as e:
                errors.append(str(e));rate_limited=True;break
            except (requests.RequestException,ValueError) as e:
                errors.append(f'{ticker}: {type(e).__name__}: {e}');break
            page_count+=1
            for event in data.get('events',[]):
                for m in event.get('markets',[]):
                    price=market_price(m)
                    if price is None:continue
                    rows.append({'sport':s.get('title') or ticker,'series_ticker':ticker,
                        'event_ticker':event.get('event_ticker',''), 'ticker':m.get('ticker',''),
                        'title':m.get('title') or event.get('title',''), 'yes_ask':price,
                        'volume':m.get('volume',0),'close_time':m.get('close_time',''),
                        'market_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        'league':s.get('title') or ticker,
                        'game_start_time': (m.get('scheduled_start_time') or event.get('scheduled_start_time') or event.get('start_time') or ''),
                        'start_time_source': ('market.scheduled_start_time' if m.get('scheduled_start_time') else 'event.scheduled_start_time' if event.get('scheduled_start_time') else 'event.start_time' if event.get('start_time') else ''),
                        'event_subtitle':event.get('sub_title',''), 'event_title':event.get('title','')})
            nxt=data.get('cursor')
            if not nxt or nxt==cursor:break
            cursor=nxt
        scanned+=1
        if rate_limited: break
    return rows,{'series_scanned':scanned,'series_available':len(series),
                 'series_capped':len(series)>max_series,'pages_requested':page_count,
                 'per_series_page_limit':max_pages,'rate_limited':rate_limited,'errors':errors}
