"""Fail-closed schedule filtering. Never substitute close/expiration for game start."""
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

TIMEZONES={"Eastern (ET)":"America/New_York","Central (CT)":"America/Chicago","Mountain (MT)":"America/Denver","Pacific (PT)":"America/Los_Angeles","Alaska":"America/Anchorage","Hawaii":"Pacific/Honolulu","UTC":"UTC"}

def parse_start(value):
    if not isinstance(value,str) or not value.strip():return None
    try:
        dt=datetime.fromisoformat(value.strip().replace('Z','+00:00'))
        # Naive dates cannot be assigned a reliable local time zone.
        return dt if dt.tzinfo and dt.utcoffset() is not None else None
    except ValueError:return None

def local_day(row, tz_name):
    dt=parse_start(row.get('game_start_time'))
    return dt.astimezone(ZoneInfo(tz_name)).date() if dt else None

def day_scope(rows, tz_name, selected_day):
    verified=[];unknown=[];other=[]
    for r in rows:
        d=local_day(r,tz_name)
        if d is None:unknown.append(r)
        elif d==selected_day:verified.append(r)
        else:other.append(r)
    return verified,unknown,other

def selected_date(label, today):
    return today if label=='Today' else today+timedelta(days=1)
