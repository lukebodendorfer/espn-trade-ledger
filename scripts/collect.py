from fetch import *
import requests, os
from concurrent.futures import ThreadPoolExecutor
import sys
YEARS=range(2018,2027)
if '--refresh-current' in sys.argv:
    import glob
    for f in glob.glob(f'raw/*_{YEARS[-1]}*.json'): os.remove(f)
def cache(p, fn):
    if os.path.exists(p): return json.load(open(p))
    d=fn(); json.dump(d,open(p,'w')); return d
def players(y):
    filt={'players':{'limit':2000,'filterSlotIds':{'value':[0,2,4,6,16,17]},'sortPercOwned':{'sortPriority':1,'sortAsc':False},
          'filterStatsForTopScoringPeriodIds':{'value':18,'additionalValue':[f'00{y}',f'10{y}']}}}
    r=requests.get(f'{B}/seasons/{y}/segments/0/leagues/{LID}',params={'view':'kona_player_info'},cookies=CK,headers={'x-fantasy-filter':json.dumps(filt)})
    r.raise_for_status(); return r.json()
def byes(y):
    r=requests.get(f'{B}/seasons/{y}',params={'view':'proTeamSchedules_wl'},cookies=CK); r.raise_for_status()
    return {t['id']:t.get('byeWeek') for t in r.json()['settings']['proTeams']}
os.makedirs('raw',exist_ok=True)
jobs=[]
for y in YEARS:
    jobs.append((f'raw/meta_{y}.json', lambda y=y: get(y,{'view':['mSettings','mTeam','mStatus']},hist=False)))
    jobs.append((f'raw/players_{y}.json', lambda y=y: players(y)))
    jobs.append((f'raw/byes_{y}.json', lambda y=y: byes(y)))
    for w in range(0,19):
        jobs.append((f'raw/tx_{y}_{w}.json', lambda y=y,w=w: get(y,{'view':'mTransactions2','scoringPeriodId':w},hist=False)))
        if w: jobs.append((f'raw/roster_{y}_{w}.json', lambda y=y,w=w: get(y,{'view':'mRoster','scoringPeriodId':w},hist=False)))
def run(j):
    try: cache(*j)
    except Exception as e: print('ERR',j[0],e)
list(ThreadPoolExecutor(10).map(run,jobs))
for y in YEARS:
    m=json.load(open(f'raw/meta_{y}.json')); p=json.load(open(f'raw/players_{y}.json'))
    print(y,'teams',len(m['teams']),'final',m['status'].get('finalScoringPeriod'),'latest',m['status'].get('latestScoringPeriod'),'players',len(p['players']))
