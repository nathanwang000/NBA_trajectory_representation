'''
make sure possession data is not flawed in anyway, return a list of flawed possessions
'''
import glob, os
from sklearn.externals import joblib
import tqdm
import argparse

parser = argparse.ArgumentParser(description='bball 2018: remove defect possessions')
parser.add_argument('--dir', '-d', required=True, type=str, help="dir containig data (required)")
parser.add_argument('--savedir', required=True, type=str,
                    help='directory to save defect possession')

args = parser.parse_args()
savename = os.path.join(args.savedir, 'defect_possessions.pkl')
os.system('mkdir -p %s' % args.savedir)

def frames_have_ball(poss):
    for frame in poss.frames:
        if frame.ball is None:
            return False
    return True

def frames_players(poss):

    player_id_set = set()

    for frame in poss.frames:
        players = frame.players

        # 10 players
        if len(players) != 10:
            return False
        
        # same 10 players
        if len(player_id_set) == 0: # first time
            player_id_set = set([p.id for p in players])
        else:
            if len(player_id_set ^ set([p.id for p in players])) != 0:
                return False

        # 5 offense, 5 defense
        offense = [p for p in players if poss.offensive_team == p.team]
        defense = [p for p in players if poss.defensive_team == p.team]
        if len(offense) != 5:
            return False
        if len(defense) != 5:
            return False
    return True
    
defect_possessions = []
for game in tqdm.tqdm(glob.glob(args.dir + "/*")):
    for fn in glob.glob(game + "/*"):
        if fn.split('/')[-1] == "Possession().pkl":
            defect_possessions.append(fn)
            continue
        poss = joblib.load(fn)
        # all frames has ball
        if not frames_have_ball(poss):
            defect_possessions.append(fn)
            continue
        # 5 offensive players and 5 defensive players for all frames and are consistent
        if not frames_players(poss):
            defect_possessions.append(fn)
            continue
    print('found %d defect possessions' % len(defect_possessions))
    joblib.dump(defect_possessions, savename)
