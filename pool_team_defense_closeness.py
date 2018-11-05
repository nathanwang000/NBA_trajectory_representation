''' 
pool result/team_defense_closeness/* together into result/team_defense_closeness.pkl
'''
import tqdm, glob
import pickle
from sklearn.externals import joblib

team_defense_closeness = {}
for game in tqdm.tqdm(glob.glob('result/team_defense_closeness/*')):
    closeness = pickle.load(open(game, 'rb'))
    for k, v in closeness.items():
        if team_defense_closeness.get(k, None) is None:
            team_defense_closeness[k] = []
        team_defense_closeness[k].extend(v)

joblib.dump(team_defense_closeness, 'result/team_defense_closeness.pkl')
