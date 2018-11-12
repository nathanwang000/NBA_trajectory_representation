from legacy.possession import *
from legacy.court import Court
from collections import defaultdict
import multiprocessing
import numpy as np
import time
import os
import copy

COURT = Court()

def cutOnce(possession, up_to=1, crop_len=None):
    # cut possession into two parts: 1:(n-second), (n-second+1):n
    frames_per_second = 25
    episode_frames = int(frames_per_second * up_to)
    total_frames = len(possession.frames)
    
    first, second = copy.deepcopy(possession), copy.deepcopy(possession)

    if total_frames <= episode_frames:
        cutoff = 0
    else:
        cutoff = total_frames - episode_frames

    # cutoff = -(up_to * frames_per_second)
        
    second.set(possession.frames[cutoff:])
    first.set(possession.frames[:cutoff])

    if crop_len is not None:
        start_frame = cutoff - crop_len * frames_per_second

        # some of the 3 sec trajs have less than 75 frames, so we need to check if the start_frame is less than 0, otherwise the seq will be empty
        if start_frame < 0:
            possession.set([possession.frames[0]] * (int(-start_frame)) + possession.frames)
            start_frame = 0

            total_frames = len(possession.frames)
            cutoff = total_frames - episode_frames

        first.set(possession.frames[start_frame:cutoff])

    return first, second
    
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
        episode.expected_outcome = possession.expected_outcome
        episode.attack_right = possession.attack_right
        
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
    # previous location
    pleft, pmiddle, pright = False, False, False

    for episode in cutPoss(poss):
        left, right = on_left_or_right(episode)
        middle = not left and not right

        if (pmiddle or pright) and left:
            return False
        if (pmiddle or pleft) and right:
            return True
        if pleft and middle:
            return True
        if pright and middle:
            return False
        
        pleft, pmiddle, pright = left, middle, right

    if pmiddle: # all in transition, then look at ball direction
        return poss.frames[-1].ball.x - poss.frames[0].ball.x > 0
    return pright

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
    # game_dirs often given by glob.glob('../traj_data/*')

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
    
