import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import streamlit as st
from discovery import sports_series,scan_series
from classify import classify
from smart import candidates
from datefilter import TIMEZONES,day_scope,local_day
from schedule import enrich_start_times
from marketfilter import market_type,game_eligible,preference_rank

st.set_page_config(page_title='Kalshi Guard v8',page_icon='🛡️',layout='wide')
st.title('🛡️ Kalshi Guard v8')
st.caption('Today’s games first • Game lines prioritized • 2–6 pick research groups • Read-only')
st.warning('Research only. No independent probability model, injury verification, executable combo quotes, or trade placement. Synthetic combo prices are NOT Kalshi offers.')

@st.cache_data(ttl=600,show_spinner=False)
def discover(pages):
    with requests.Session() as s:return sports_series(s,pages)
@st.cache_data(ttl=600,show_spinner=False)
def scan(series,pages,cap):
    with requests.Session() as s:return scan_series(s,series,pages,cap)

@st.cache_data(ttl=900,show_spinner=False)
def check_schedule(rows_json, day_iso, timezone_name):
    from datetime import date
    rows = json.loads(rows_json)
    return enrich_start_times(rows, date.fromisoformat(day_iso), timezone_name)

with st.sidebar:
    st.header('Settings')
    tz_label=st.selectbox('Time zone',list(TIMEZONES),index=0,help='Choose the time zone of your device. Eastern is the default; browser auto-detection is not available in this version.')
    tz=TIMEZONES[tz_label]
    today=datetime.now(ZoneInfo(tz)).date()
    st.caption(f'Local date: {today.isoformat()} • {tz}')
    day_choice=st.radio('Game date',['Today','Tomorrow','Choose a date'],index=0)
    chosen=today if day_choice=='Today' else today+timedelta(days=1) if day_choice=='Tomorrow' else st.date_input('Select date',value=today,min_value=today-timedelta(days=1),max_value=today+timedelta(days=30))
    st.caption(f'Showing starts on {chosen.isoformat()} (midnight to midnight local time).')
    with st.expander('Advanced scanner settings', expanded=False):
        series_pages=st.slider('Sports catalog pages',1,20,5,help='How many pages of Kalshi sports categories to check. More pages can find more leagues, but takes longer.')
        series_cap=st.slider('Sports categories to check',5,200,60,5,help='Maximum number of Kalshi sports series to scan. The app now checks recognizable leagues first. A higher number is slower.')
        event_pages=st.slider('Game pages per category',1,5,2,help='How deeply to look inside each sports category. Higher values make more Kalshi requests.')
        st.caption('Higher values scan more markets but can trigger Kalshi rate limits.')
    if st.button('Clear cached scan'):
        discover.clear();scan.clear();check_schedule.clear();st.session_state.pop('rows',None)
    st.caption('Tip: Start with the default settings. A bigger scan is slower and may trigger Kalshi limits. Games with uncertain start times are kept separate.')

if st.button('🔄 Scan Kalshi sports markets',type='primary'):
    with st.spinner('Discovering and scanning public sports markets…'):
        series,disc=discover(series_pages)
        rows,coverage=scan(series,event_pages,series_cap) if series else ([],{'errors':['No sports series returned']})
        st.session_state.update(rows=rows,disc=disc,coverage=coverage,series_count=len(series))

rows=st.session_state.get('rows',[])
coverage=st.session_state.get('coverage',{})
if coverage:
    a,b,c=st.columns(3)
    a.metric('Categories found',st.session_state.get('series_count',0),help='Kalshi sports series discovered; not the number of games.')
    b.metric('Categories checked',coverage.get('series_scanned',0),help='Number of series examined during this scan.')
    c.metric('Markets with YES prices',len(rows),help='Markets with a usable YES ask. Not all are games starting on the selected date.')
    if coverage.get('series_capped') or st.session_state.get('disc',{}).get('truncated'):
        st.warning('This is a partial scan. The app did not check every Kalshi sports category.')
    errors=coverage.get('errors',[])+st.session_state.get('disc',{}).get('errors',[])
    if errors:
        st.warning('Some games could not be loaded. Kalshi may be temporarily limiting requests. Your existing results are still shown.')
        with st.expander('Technical scan messages'):
            for message in errors[:8]:st.code(message)

if not rows:
    st.info('Press Scan Kalshi sports markets to load live public market data. No fake plays will be displayed.')
    st.stop()

annotated=[]
for r in rows:
    cat,level=classify(r)
    annotated.append({**r,'category':cat,'level':level,'market_type':market_type(r)})
excluded_count=sum(not game_eligible(r) for r in annotated)
annotated=[r for r in annotated if game_eligible(r)]
with st.spinner('Checking game schedules for missing start times…'):
    annotated=check_schedule(json.dumps(annotated,sort_keys=True,default=str),chosen.isoformat(),tz)
verified,unknown,other=day_scope(annotated,tz,chosen)
if coverage:
    st.caption(f'Game markets: {len(verified)} on selected day • {len(unknown)} start times not confirmed • {len(other)} other dates • {excluded_count} non-game or unclear markets hidden.')
    if not verified:
        st.info('The scan found market prices, but no games with confirmed starts for this date. Try Today, or open “Start time not confirmed” to see what was excluded.')

sport_names=sorted({r['category'] for r in verified})
a,b=st.columns(2)
with a:sport=st.selectbox('Sport',['All sports']+sport_names,help='Show only the selected sport. This filter applies to plays and combos.')
scoped=[r for r in verified if sport=='All sports' or r['category']==sport]
with b:level=st.selectbox('League / level',['All levels']+sorted({r['level'] for r in scoped}),help='Choose NBA, CBB, WCBB, etc. when available.')
scoped=[r for r in scoped if level=='All levels' or r['level']==level]
market_choice=st.selectbox('Market type',['Game Lines (Spreads)','All game markets','Moneyline / Winner','Totals (Over/Under)'],help='Game Lines are point spreads or handicaps. Only confirmed game markets are shown; futures are excluded.')
scoped=[r for r in scoped if market_choice=='All game markets' or r['market_type']==market_choice]
scoped=sorted(scoped,key=lambda r:(preference_rank(r),r.get('game_start_time',''),r.get('title','')))

plays_tab,combo_tab,unknown_tab,details_tab=st.tabs(['🎯 Today’s game markets','🧩 Suggested combos (2–6)','🕒 Start time not confirmed','🔎 Extra market info'])
with plays_tab:
    st.subheader(f'Games starting {chosen.strftime("%b %d, %Y")}')
    st.caption(f'{len(scoped)} game markets • {tz} • Price reflects the YES contract cost, not an independently predicted chance.')
    stake=st.number_input('Amount to spend ($)',help='Example amount used to calculate how many whole YES contracts you could afford, before fees.',min_value=1.0,value=10.0,step=5.0,key='play_budget')
    search=st.text_input('Search plays')
    display=[r for r in scoped if search.lower() in str(r.get('title','')).lower()]
    for r in display[:100]:
        p=float(r['yes_ask'])
        if not 0<p<1:continue
        contracts=int((stake+1e-9)//p)
        cost=contracts*p;profit=contracts-cost
        with st.container(border=True):
            st.markdown('**'+str(r['title'])+'**')
            dt=datetime.fromisoformat(r['game_start_time'].replace('Z','+00:00')).astimezone(ZoneInfo(tz))
            st.caption(f"{r['category']} • {r['level']} • {r['market_type']} • Starts {dt.strftime('%I:%M %p')}")
            x,y,z=st.columns(3)
            x.metric('YES price / break-even',f'{p*100:.1f}¢ / {p*100:.1f}%')
            y.metric('Payout if YES wins',f'${contracts:.2f}' if contracts else '—')
            z.metric('Profit before fees',f'${profit:.2f}' if contracts else '—',f'({(profit/cost*100):.1f}%)' if contracts else None,delta_color='off')
            st.caption(f'{contracts} whole contracts • Cost ${cost:.2f} • Before fees • YES must win')
    if len(display)>100:st.info('First 100 shown; narrow filters to see more.')
    if not display:st.info('No confirmed games match this date. Try Today, another date, or the Start time not confirmed tab.')

with combo_tab:
    st.subheader(f'Same-day combos • {chosen.strftime("%b %d")}')
    st.warning('Generated groups are hypothetical. This app does NOT confirm that Kalshi offers these combinations as one executable trade. Do not treat the synthetic payout as a real quote.')
    n=st.select_slider('Picks per group',help='Build example groups of 2 to 6 selections from different events on the selected day. These are not verified Kalshi combo tickets.',options=[2,3,4,5,6],value=2)
    budget=st.number_input('Example combo budget ($)',min_value=1.0,value=10.0,step=5.0,key='combo_budget')
    combos=candidates(sorted(scoped,key=preference_rank),n,budget)
    if not combos:st.info('Not enough different games with confirmed starts on this date to create this group.')
    for idx,item in enumerate(combos,1):
        with st.container(border=True):
            st.markdown(f'**Combo {idx} • {n} picks**')
            for leg in item['legs_detail']:
                st.write(f"• {leg['title']} — YES {float(leg['yes_ask'])*100:.1f}¢ ({leg['level']})")
                st.caption('Market ticker: '+str(leg['ticker']))
            x,y,z=st.columns(3)
            x.metric('Estimated break-even*',f"{item['synthetic_implied_probability']:.1%}")
            y.metric('Example payout*',f"${item['hypothetical_gross_payout']:.2f}")
            z.metric('Example profit*',f"${item['hypothetical_profit']:.2f}",f"({item['hypothetical_roi_pct']:.1f}%)",delta_color='off')
            st.caption('Not a real Kalshi combo quote. Multiplication assumes independent legs; real prices, fees and correlations may differ.')
    if combos:
        export=[{k:v for k,v in c.items() if k!='legs_detail'} for c in combos]
        st.download_button('Export combo research',pd.DataFrame(export).to_csv(index=False),'kalshi_v7_combo_research.csv','text/csv')

with unknown_tab:
    st.subheader('Game start time not confirmed')
    st.info(f'{len(unknown)} game-like markets could not be matched to a verified scheduled game start. They are deliberately NOT included in Today, Tomorrow or combos.')
    if unknown:
        st.dataframe(pd.DataFrame(unknown)[['category','level','market_type','title','ticker','event_ticker','close_time']],hide_index=True,use_container_width=True)
        st.download_button('Export unverified starts',pd.DataFrame(unknown).to_csv(index=False),'unverified_start_times.csv','text/csv')
    st.caption('These are NOT recommended plays. Market close times do not prove when a game starts. Futures and unclear markets are hidden entirely.')

with details_tab:
    st.subheader('Extra market information')
    st.caption('Includes markets from the selected day after sport/league filtering. Technical fields are hidden from the main plays view.')
    if scoped:
        st.dataframe(pd.DataFrame(scoped),hide_index=True,use_container_width=True)
        st.download_button('Export selected markets',pd.DataFrame(scoped).to_csv(index=False),'kalshi_v7_markets.csv','text/csv')
    st.write(f'Other-date game markets: {len(other)} • Unverified game starts: {len(unknown)} • Excluded non-game/unclear markets: {excluded_count}')
    st.caption('No browser timezone auto-detection, verified injuries, independently calibrated odds, or actual combo trading is implemented.')
