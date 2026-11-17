"""Research-only cross-event hypothetical combo math, not executable quotes."""
from itertools import combinations
from math import prod
from marketfilter import preference_rank

def candidates(rows, size, budget=10, max_rows=30, max_results=25):
    if size not in range(2,7):raise ValueError('size must be 2..6')
    eligible=[]
    for r in rows:
        try:p=float(r['yes_ask'])
        except (KeyError,ValueError,TypeError):continue
        if 0<p<1 and r.get('event_ticker') and r.get('ticker'):
            eligible.append(r)
    eligible=sorted(eligible,key=lambda r:(preference_rank(r),abs(float(r['yes_ask'])-0.6)))[:max_rows]
    out=[]
    for group in combinations(eligible,size):
        events=[r['event_ticker'] for r in group]
        if len(set(events))!=size:continue
        p=prod(float(r['yes_ask']) for r in group)
        # Illustrative synthetic price only. No actual Kalshi combo quote.
        gross=budget/p
        out.append({'plays':' + '.join(str(r['title']) for r in group), 'levels':' / '.join(str(r.get('level','')) for r in group), 'legs':size,'synthetic_implied_probability':p,'hypothetical_gross_payout':gross,'hypothetical_profit':gross-budget,'hypothetical_roi_pct':(gross/budget-1)*100,'status':'UNVERIFIED — NOT A FAVORABLE PICK','tickers':' | '.join(r['ticker'] for r in group), 'legs_detail':[{'title':r['title'],'ticker':r['ticker'],'event_ticker':r['event_ticker'],'yes_ask':r['yes_ask'],'category':r.get('category',''),'level':r.get('level',''),'game_start_time':r.get('game_start_time','')} for r in group]})
        if len(out)>=max_results:break
    return out
