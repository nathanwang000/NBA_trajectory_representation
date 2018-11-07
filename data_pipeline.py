from load_possession import loadPossession
from legacy.code_mapping import code2team, team2code
from legacy.reward import reward
from legacy.court import Court, REGIONS
import numpy as np
import os
import multiprocessing
from sklearn.externals import joblib
from lib.process_possession import is_attack_right
import time
import argparse

parser = argparse.ArgumentParser(description='bball 2018: data generataion')
parser.add_argument('--debug', action='store_true',
                    help='debug mode')
args = parser.parse_args()

def process(games, output=False, savedir='../traj_data'):

    COURT = Court()
    for i, possession in enumerate(loadPossession(None, games)):

        # deal with ill possessions
        if len(possession.frames) < 25 or\
           len(possession.shots) > 1 or\
           possession.num_shots != len(possession.shots) or\
                                   (possession.end_event == 'Field Goal Missed' and
                                    len(possession.shots) == 0) or\
                                    (possession.end_event == 'Field Goal Made' and
                                     len(possession.shots) == 0) or\
                                     (possession.end_event == 'Field Goal Made' and
                                      possession.points == 0):
            continue

        # get final reward for this possession
        final_reward = 0

        # design choice: final rewards = sum of expected score on all shots
        for shot in possession.shots: 
            pid, x, y, time = shot.player_id, shot.x, shot.y, shot.time
            location = COURT.region([(x, y)])[0]

            # league average
            twoRegions = range(12)
            if location in twoRegions:
                average = 3 * 0.35 
            else:
                average = 2 * 0.45
                
            final_reward += reward(location=location,
                                   average=average,
                                   player_id=pid,
                                   time=time,
                                   mix=True)

        if output is True:
            print(possession)
            print("%d shots" % len(possession.shots))
            print("reward %.3f\n" % final_reward)
        
        # endx, endy = possession.endplayer_x, possession.endplayer_y
        # endeventloc = COURT.region([(endx, endy)])[0]

        # get state, action for this possession
        possession.attack_right = is_attack_right(possession)
        possession.expected_outcome = final_reward

        savesubdir = os.path.join(savedir, str(possession.gamecode))
        savename = os.path.join(savesubdir, '%s.pkl' % str(possession))
        os.system('mkdir -p %s' % savesubdir)
        joblib.dump(possession, savename)
        
def learning_free():
    # generate learning free data for sloan
    result_list = []
    pool = multiprocessing.Pool(60)
    with open('gamecodes.txt') as f:
        for l in f:
            game = l.strip()
            result_list.append(pool.apply_async(func=process,
                                                args=([game],)))
    while True:
        done_list = list(map(multiprocessing.pool.ApplyResult.ready, result_list))
        print('{}/{} done'.format(sum(done_list), len(result_list)))
        if np.all(done_list):
            break
        time.sleep(3)
    print('finished preprocessing')

if __name__ == '__main__':
    if args.debug:
        process(['2015030907'], output=True, savedir='../debug_traj_data')
    else:
        learning_free()
