"""Conservative metadata-based sport and league grouping."""
import re

def classify(row):
    s=' '.join(str(row.get(k,'') or '') for k in ('sport','series_ticker','league')).upper()
    patterns=[('Basketball','WCBB',r'\b(WCBB|NCAAW|WOMEN.S COLLEGE BASKETBALL|WOMENS COLLEGE BASKETBALL)\b'),('Basketball','CBB',r'\b(CBB|NCAAM|NCAA MEN.S BASKETBALL|COLLEGE BASKETBALL)\b'),('Basketball','WNBA',r'\bWNBA\b'),('Basketball','NBA',r'\bNBA\b'),('Football','NCAAF',r'\b(NCAAF|CFB|COLLEGE FOOTBALL)\b'),('Football','NFL',r'\bNFL\b'),('Baseball','MLB',r'\bMLB\b'),('Hockey','NHL',r'\bNHL\b'),('Soccer','MLS',r'\bMLS\b'),('Soccer','Soccer',r'\b(SOCCER|EPL|UEFA|CHAMPIONS LEAGUE|LA LIGA|SERIE A|BUNDESLIGA|WORLD CUP)\b'),('Tennis','Tennis',r'\b(TENNIS|ATP|WTA|WIMBLEDON)\b'),('Golf','Golf',r'\b(GOLF|PGA|LIV GOLF)\b'),('MMA','MMA/UFC',r'\b(MMA|UFC)\b'),('Football','Football',r'\bFOOTBALL\b'),('Basketball','Basketball',r'\bBASKETBALL\b'),('Baseball','Baseball',r'\bBASEBALL\b'),('Hockey','Hockey',r'\bHOCKEY\b')]
    for sport,level,pattern in patterns:
        if re.search(pattern,s):return sport,level
    return 'Other sports',str(row.get('sport') or row.get('series_ticker') or 'Unclassified')
