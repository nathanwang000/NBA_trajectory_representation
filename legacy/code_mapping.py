import pandas as pd
from legacy.court import REGIONS
from itertools import product

# action code mapping: deprecated
code2action = dict((i+1, "%d->%d" % (src, tgt)) for i, (src, tgt) in
                   enumerate(product(range(REGIONS), range(REGIONS))))
code2action[0] = "all stay"
action2code = dict((v, n) for n, v in code2action.items())

# event code mapping
code2event = {
    1: "Free Throw Made",
    2: "Free Throw Missed",
    3: "Field Goal Made",
    4: "Field Goal Missed",
    5: "Offensive Rebound",
    6: "Defensive Rebound",
    7: "Turnover",
    8: "Foul",
    21: "Dribble",
    22: "Pass",
    23: "Possession",
    24: "Blocked Shot",
    25: "Assist"
}

event2code = dict((v, n) for n, v in code2event.items())

# team code mapping
code2team = {
    -1: "ball",
    -2: "referee",
    1: "Atlanta",
    2: "Boston",
    3: "New Orleans",
    4: "Chicago",
    5: "Cleveland",
    6: "Dallas",
    7: "Denver",
    8: "Detroit",
    9: "Golden State",
    10: "Houston",
    11: "Indiana",
    12: "Los Angeles Clippers",
    13: "Los Angeles Lakers",
    14: "Miami",
    15: "Milwaukee",
    16: "Minnesota",
    17: "New Jersey",
    18: "New York",
    19: "Orlando",
    20: "Philadelphia",
    21: "Phoenix",
    22: "Portland",
    23: "Sacramento",
    24: "San Antonio",
    25: "Oklahoma City",
    26: "Utah",
    27: "Washington",
    28: "Toronto",
    29: "Memphis",
    30: "Charlotte**"
}
team2code = dict((v, n) for n, v in code2team.items())

# player name mapping from gplayer_id to name
player_info = pd.read_csv("legacy/player_dict.csv")
def gid2name(gid):
    p = player_info[player_info.player_global_id==gid]
    if p.values.size == 0: return str(gid)
    fn = p.player_firstname.values[0]
    ln = p.player_lastname.values[0]
    return " ".join([fn, ln])
    
