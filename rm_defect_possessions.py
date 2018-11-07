'''
remove defect possessions
'''
import glob, os
from sklearn.externals import joblib
import tqdm
import argparse

parser = argparse.ArgumentParser(description='bball 2018: remove defect possessions')
parser.add_argument('--savedir', required=True, type=str,
                    help='where defect_possessions.pkl is stored')

args = parser.parse_args()
savename = os.path.join(args.savedir, 'defect_possessions.pkl')

defect_possessions = joblib.load(savename)
for fn in defect_possessions:
    os.system("rm '%s'" % fn)

