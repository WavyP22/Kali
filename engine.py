"""Pure risk/valuation logic. No trading functions."""
from datetime import datetime, timezone
from itertools import combinations
import math

def age_minutes(ts, now=None):
    try:
        d=datetime.fromisoformat(str(ts).replace('Z','+00:00'))
        if d.tzinfo is None:return None
        return ((now or datetime.now(timezone.utc))-d.astimezone(timezone.utc)).total_seconds()/60
    except (TypeError, ValueError):return None

def fresh(ts,minutes):
    a=age_minutes(ts)
    return a is not None and -5<=a<=minutes

def market_price(m, side='yes'):
    for key,scale in [(f'{side}_ask_dollars',1),(f'{side}_ask',100)]:
        try:
            v=float(m[key])/scale
            if math.isfinite(v) and 0<v<1:return v
        except (ValueError,TypeError,KeyError):pass
    return None

def gate(r):
    issues=[]
    if not str(r.get('league','')).strip():issues.append('Missing sport label')
    if not r.get('event_ticker'):issues.append('Missing event ID')
    if not fresh(r.get('market_at'),5):issues.append('Market snapshot older than 5 minutes')
    if r.get('lineup')!='Confirmed':issues.append('Starting lineup not confirmed')
    if r.get('injury')!='Reviewed':issues.append('Injury/suspension status not reviewed')
    if r.get('news')!='Reviewed':issues.append('News not reviewed')
    if not fresh(r.get('evidence_at'),180):issues.append('Evidence review older than 3 hours')
    if not str(r.get('source_url','')).startswith('https://'):issues.append('Evidence source URL missing')
    if r.get('model')!='Validated':issues.append('Independent model not validated')
    try:
        low=float(r.get('p_low'));mid=float(r.get('p_mid'));high=float(r.get('p_high'))
        if not 0<low<=mid<=high<1:issues.append('Probability interval invalid')
    except (ValueError,TypeError):issues.append('Probability interval missing')
    return issues

def evaluate(rows, quote_cost=None, gross_payout=None, fees=0, stress=0.05):
    issues=[]
    if len(rows) not in (2,3):issues.append('Only 2–3 legs supported')
    if len(set(r.get('event_ticker') for r in rows))!=len(rows):issues.append('Same-event legs excluded')
    for r in rows:issues.extend(f"{r.get('title','?')}: {x}" for x in gate(r))
    try:
        low=math.prod(float(r['p_low']) for r in rows)
        mid=math.prod(float(r['p_mid']) for r in rows)
        high=math.prod(float(r['p_high']) for r in rows)
        if not all(0<float(r['p_low'])<=float(r['p_mid'])<=float(r['p_high'])<1 for r in rows):raise ValueError()
        s=float(stress)
        if not 0<=s<=0.5:raise ValueError()
    except (ValueError,TypeError,KeyError):return {'status':'BLOCKED','issues':issues+['Invalid probabilities/stress']}
    result={'status':'SCENARIO ONLY','issues':issues,'p_conservative':max(0,low-s),'p_central':mid,'p_optimistic':min(1,high+s)}
    if quote_cost is None or gross_payout is None:
        result['issues'].append('No executable Kalshi combo quote')
        result['status']='BLOCKED'
        return result
    try:
        c=float(quote_cost);pay=float(gross_payout);f=float(fees)
        if not (c>0 and pay>f>=0 and math.isfinite(c+pay+f)):raise ValueError()
    except (TypeError,ValueError):return {'status':'BLOCKED','issues':issues+['Invalid quote']}
    result.update(break_even=c/(pay-f),ev_low=result['p_conservative']*(pay-f)-c,ev_mid=mid*(pay-f)-c,roi_low=(result['p_conservative']*(pay-f)-c)/c)
    result['issues'].append('Quote manually entered; authenticity and availability not verified')
    result['status']='BLOCKED'
    return result

def combos(rows,size=2,limit=100):
    valid=[r for r in rows if r.get('p_low') is not None]
    out=[]
    for group in combinations(valid,size):
        if len({r.get('event_ticker') for r in group})!=size:continue
        result=evaluate(group)
        out.append({'legs':' + '.join(r.get('title','?') for r in group),'probability_low':result.get('p_conservative'),'probability_mid':result.get('p_central'),'status':result['status'],'issues':'; '.join(result['issues'])})
        if len(out)>=limit:break
    return sorted(out,key=lambda x:x['probability_low'] or 0,reverse=True)
