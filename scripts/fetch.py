import os, json, requests
# ESPN cookies come from the environment. Never hard-code them.
LID=1146674
CK={'espn_s2':os.environ['espn_s2'],'SWID':os.environ['SWID']}
B='https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl'
def get(year, params, headers=None, hist=None):
    if hist is None: hist = year < 2018
    url = f'{B}/leagueHistory/{LID}?seasonId={year}' if hist else f'{B}/seasons/{year}/segments/0/leagues/{LID}'
    r = requests.get(url, params=params, cookies=CK, headers=headers or {})
    r.raise_for_status(); d = r.json()
    return d[0] if isinstance(d, list) else d
