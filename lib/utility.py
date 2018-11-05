from legacy.possession import *
from legacy.court import Court
from collections import defaultdict
import multiprocessing
import numpy as np
import time
import os

COURT = Court()

def cutPoss(possession, second=1):
    '''
    granularity determined by how many seconds
    '''
    frames_per_second = 25
    episode_frames = int(frames_per_second * second)

    nframes = len(possession.frames)
    i = nframes % episode_frames # delete first few frames

    while i < nframes:
        episode = Possession()
        episode.set(possession.frames[i:i+episode_frames])
        episode.defensive_team = possession.defensive_team
        episode.offensive_team = possession.offensive_team
        episode.shots = possession.shots
        episode.fouled = possession.fouled

        yield episode

        i = i + episode_frames

def getPlayerCenter(episode):
    # calculate center of mass for each player
    center_x = defaultdict(int)
    center_y = defaultdict(int)
    cum_weight = 0 # previously: t
    for i, f in enumerate(episode.frames):
        weight = 1 # i+1 for linear weight
        cum_weight += weight
        for p in f.players:
            center_x[p.id] += weight * p.x
            center_y[p.id] += weight * p.y
    for k in center_x: # normalize
        center_x[k] /= cum_weight
        center_y[k] /= cum_weight
    return center_x, center_y

def on_left_or_right(episode):
    '''are all the players on left or right, if both not true, is transition'''
    all_on_left = True
    all_on_right = True

    center_x, _ = getPlayerCenter(episode)
    for pid in center_x:
        if center_x[pid] > COURT.width / 2:
            all_on_left = False
        else:
            all_on_right = False
    return all_on_left, all_on_right
    
def is_attack_right(poss):
    transition = False
    prev_on_left, prev_on_right = False, False
    for episode in cutPoss(poss):
        on_left, on_right = on_left_or_right(episode)
        if (prev_on_left or transition) and on_right:
            return True
        if (prev_on_right or transition) and on_left:
            return False
        transition = transition or (not on_left and not on_right)
        prev_on_left = on_left
        prev_on_right = on_right
    return prev_on_right
    
def isTransition(episode, attack_right):
    # see if all are on the same side
    all_on_left, all_on_right = on_left_or_right(episode)
    
    if attack_right:
        return not all_on_right
    else:
        return not all_on_left

def ball_player_difference(episode, pid, metric=np.linalg.norm):
    dist, Z = 0, 0
    for i, f in enumerate(episode.frames):
        for p in f.players:
            if p.id == pid and f.ball is not None:
                dist += metric(np.array([p.x, p.y]) - np.array([f.ball.x, f.ball.y]))
                Z += 1
    if Z is 0: return 100
    return dist / Z
    
def get_ball_handler(episode, offensive_pid):
    # assume ball handler is the offensive player closest to the ball on average
    cand = list(offensive_pid)
    min_ind = np.argmin([ball_player_difference(episode, pid) for pid in cand])
    ball_handler = cand[min_ind]
    return ball_handler
    
def parallel_game(f, game_dirs, savedir='result', cpus=60):
    # assumes do the same for each game
    # game_dirs often given by glob.glob('../new_traj_data/*')

    savedir = os.path.join(savedir, f.__name__)
    os.system('mkdir -p %s'  % savedir)
    
    result_list = []
    pool = multiprocessing.Pool(cpus)
    for game in game_dirs:
        savename = os.path.join(savedir, game.split('/')[-1]) + '.pkl'
        result_list.append(pool.apply_async(func=f,
                                            args=([game], savename)))
    while True:
        done_list = list(map(multiprocessing.pool.ApplyResult.ready, result_list))
        print('{}/{} done'.format(sum(done_list), len(result_list)))
        if np.all(done_list):
            break
        time.sleep(3)
    print('finished preprocessing')
    
