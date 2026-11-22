import json
from collections import defaultdict
POS={1:'QB',2:'RB',3:'WR',4:'TE',5:'K',16:'D/ST'}
REPL_RANK={'QB':12,'RB':30,'WR':30,'TE':12,'K':12,'D/ST':12}
out={'seasons':{},'trades':[]}
for y in range(2018,2027):
    meta=json.load(open(f'raw/meta_{y}.json'))
    final=meta['status']['finalScoringPeriod']
    if y==2026: final=meta['status']['latestScoringPeriod']-1   # completed weeks only
    mem={m['id']:f"{m.get('firstName','')} {m.get('lastName','')}".strip() or m.get('displayName') for m in meta['members']}
    teams={t['id']:{'team':t.get('name') or f"{t.get('location','')} {t.get('nickname','')}".strip(),
                    'owner':mem.get(t.get('primaryOwner') or (t.get('owners') or ['?'])[0],'?').title()} for t in meta['teams']}
    BYES=json.load(open(f'raw/byes_{y}.json'))
    # players
    P={}
    for pl in json.load(open(f'raw/players_{y}.json'))['players']:
        p=pl['player']; pos=POS.get(p['defaultPositionId'])
        if not pos: continue
        wk={}
        for s in p.get('stats',[]):
            if s['statSourceId']==0 and s['statSplitTypeId']==1 and 1<=s['scoringPeriodId']<=final:
                st=s.get('stats',{}); played=(st['210']>0) if '210' in st else any(k not in ('155','156','157') for k in st)
                wk[s['scoringPeriodId']]=(s.get('appliedTotal',0.0), played)
        tms=[st['proTeamId'] for st in sorted(p.get('stats',[]),key=lambda st:st['scoringPeriodId']) if st['statSplitTypeId']==1 and st['scoringPeriodId']<=final and st.get('proTeamId')]
        P[p['id']]={'name':p['fullName'],'pos':pos,'wk':wk,'team':tms[-1] if tms else p.get('proTeamId'),'tot':sum(v[0] for v in wk.values()),'gp':sum(1 for v in wk.values() if v[1])}
    # replacement levels
    repl={}
    ranks=REPL_RANK if len(teams)>=12 else {'QB':10,'RB':25,'WR':25,'TE':10,'K':10,'D/ST':10}
    for pos,n in ranks.items():
        ranked=sorted((x for x in P.values() if x['pos']==pos),key=lambda x:-x['tot'])
        if len(ranked)<n: continue
        r=ranked[n-1]; bw=BYES.get(str(r['team']),0); sg=final-(1 if bw and bw<=final else 0)
        repl[pos]={'rank':n,'player':r['name'],'total':round(r['tot'],2),'gp':r['gp'],'season_games':sg,'ppg':round(r['tot']/sg,3)}
    # weekly rosters
    R={}; SLOT={}
    for w in range(1,19):
        d=json.load(open(f'raw/roster_{y}_{w}.json'))
        R[w]={e['playerId']:t['id'] for t in d['teams'] for e in t['roster']['entries']}
        SLOT[w]={e['playerId']:e['lineupSlotId'] for t in d['teams'] for e in t['roster']['entries']}
    # trades: tx log
    trades={}
    adds=set()
    for w in range(19):
        for t in json.load(open(f'raw/tx_{y}_{w}.json')).get('transactions',[]):
            its=t.get('items',[])
            if t['type'] in('TRADE_ACCEPT','TRADE_UPHOLD') and any(i['type']=='TRADE' for i in its):
                mv=sorted((i['playerId'],i['fromTeamId'],i['toTeamId']) for i in its if i['type']=='TRADE')
                wk=t['scoringPeriodId']
                pair=tuple(sorted({m[1] for m in mv}|{m[2] for m in mv}))
                trades.setdefault((wk,pair),{'week':wk,'moves':mv,'src':'log'})
            elif 'TRADE' not in t['type'] and t.get('status')=='EXECUTED':
                for i in its:
                    if i['type']=='ADD': adds.add((i['playerId'],i['toTeamId']))
    # trades: roster inferred
    logged={(m[0],m[2]) for tr in trades.values() for m in tr['moves']}
    grp=defaultdict(list)
    for w in range(2,19):
        for p,tm in R[w].items():
            a=R[w-1].get(p)
            if a and a!=tm and (p,tm) not in adds and (p,tm) not in logged:
                grp[(w,tuple(sorted((a,tm))))].append((p,a,tm))
    for (w,pair),mv in grp.items():
        if any(k[1]==pair and abs(k[0]-w)<=1 for k in trades): continue
        trades[(w,pair)]={'week':w,'moves':sorted(mv),'src':'rosters'}
    # value
    for (wk,pair),tr in sorted(trades.items()):
        sides={tid:{'teamId':tid,**teams[tid],'received':[]} for tid in pair}
        start=max(wk,1)
        for pid,fr,to in tr['moves']:
            p=P.get(pid)
            if not p: p={'name':f'Unknown {pid}','pos':'?','wk':{}}
            rp=repl.get(p['pos'],{'ppg':0})['ppg']
            games=[]; exit_=None
            for w in range(start,final+1):
                bye = w not in p['wk']
                if exit_=='dropped':
                    if bye: continue
                    games.append({'w':w,'pts':0.0,'vorp':round(-rp,2),'played':False,'started':False,'dropped':True,'missed':w in p['wk'] and not p['wk'][w][1]}); continue
                if R.get(w,{}).get(pid)!=to:
                    if w==start: continue
                    if any(m[0]==pid and m[1]==to and abs(k[0]-w)<=1 for k,t2 in trades.items() for m in t2['moves']):
                        exit_='traded'; break
                    exit_='dropped'; break
                if bye: continue
                pts,played=p['wk'].get(w,(0.0,False))
                games.append({'w':w,'pts':round(pts,2),'vorp':round(pts-rp,2),'played':played,'missed':w in p['wk'] and not played,'started':SLOT[w].get(pid) not in (20,21)})
            sides[to]['received'].append({'playerId':pid,'name':p['name'],'pos':p['pos'],'from':fr,'repl_ppg':rp,
                'exit':exit_,'missed':sum(1 for g in games if g['missed']),'first_missed':next((g['w'] for g in games if g['missed']),None),'weeks_rostered':sum(1 for g in games if not g.get('dropped')),'weeks_counted':len(games),'remaining_weeks':final-start+1,'games':sum(g['played'] for g in games),'starts':sum(g['started'] for g in games),'points':round(sum(g['pts'] for g in games),2),
                'vorp':round(sum(g['vorp'] for g in games),2),'weeks':games})
        for s in sides.values(): s['vorp']=round(sum(x['vorp'] for x in s['received']),2); s['points']=round(sum(x['points'] for x in s['received']),2)
        out['trades'].append({'season':y,'week':wk,'source':tr['src'],'final_week':final,'sides':list(sides.values())})
    out['seasons'][y]={'final_week':final,'teams':len(teams),'replacement':repl}
json.dump(out,open('data/trades.json','w'),indent=1)
for t in out['trades']:
    print(t['season'],'wk',t['week'],t['source'])
    for s in t['sides']:
        print(f"   {s['owner']:<22} VORP {s['vorp']:>7}  pts {s['points']:>6} | "+', '.join(f"{x['name']} ({x['pos']}) {x['vorp']}/{x['games']}g" for x in s['received']))
for y,s in out['seasons'].items(): print(y,{k:(v['player'],v['ppg']) for k,v in s['replacement'].items()})
