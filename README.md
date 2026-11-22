# UCSB Fantasy Football Trade Ledger

Every trade in the league since 2018, valued by **VORP (Value Over Replacement Player)**.

Open `site/index.html` in a browser to view it.

## How VORP is calculated

- **Replacement level** for each season is the season fantasy-point total of the Nth-best player at each position:

  | Seasons | QB | RB | WR | TE | K | D/ST |
  |---|---|---|---|---|---|---|
  | 2020– (12 teams) | 12 | 30 | 30 | 12 | 12 | 12 |
  | 2018–2019 (10 teams) | 10 | 25 | 25 | 10 | 10 | 10 |

  That total is divided by the games in the fantasy season (fantasy weeks minus the bye) to get points per game.
- **Player VORP** = points scored after the trade − (replacement points per game × games remaining).
  - Bye weeks are excluded. Injured weeks count as 0 points.
  - If the receiving team drops the player, the remaining weeks still count at 0 points.
  - If the receiving team trades the player away again, counting stops (the later trade picks it up).
- A trade's winner is the side whose received players have more total VORP. A gap under 5 is "even".

2012–2017 aren't covered: ESPN keeps no transaction log or bench rosters for those seasons.

## Rerunning

Requires Python 3 with `requests`, plus your ESPN cookies as environment variables (never commit them):

```bash
export espn_s2='...'
export SWID='{...}'
```

```bash
python3 scripts/collect.py                    # download raw data into raw/ (cached; ~290 MB)
python3 scripts/collect.py --refresh-current  # re-download the current season only
python3 scripts/analyze.py                    # compute VORP -> data/trades.json
python3 scripts/build.py                      # build site/index.html
```

Run all scripts from the repo root. For the current season, `analyze.py` counts only completed weeks.
