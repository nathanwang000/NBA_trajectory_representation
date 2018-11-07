from possession import *
from lib.process_possession import cutPoss, isTransition, parallel_game, get_ball_handler
from sklearn.externals import joblib
import numpy as np
import pandas as pd
import glob
import copy
import tqdm
from collections import Counter, defaultdict

####### data distribution
def end_event_dist():
    end_events = []
    for game in tqdm.tqdm(glob.glob('../new_traj_data/*')):
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)
            end_events.append(poss.end_event)
        joblib.dump(end_events, 'result/end_event_dist.pkl')

def traj_length_dist():
    lengths = []
    for game in tqdm.tqdm(glob.glob('../new_traj_data/*')):
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)
            lengths.append(poss.start_time - poss.end_time)
        joblib.dump(lengths, 'result/traj_length_dist.pkl')

def traj_length_debug():
    lengths = []
    for game in glob.glob('../new_traj_data/*'):
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)
            if poss.start_time - poss.end_time > 40:
                print(fn)
                return 

########## player of interest
def player_frames_count():
    count = {}
    for game in tqdm.tqdm(glob.glob('../new_traj_data/*')):
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)
            for f in poss.frames:
                for p in f.players:
                    count[p.id] = count.get(p.id, 0) + 1
        joblib.dump(count, 'result/player_frames_count.pkl')

def player_poss_count():
    count = {}
    for game in tqdm.tqdm(glob.glob('../new_traj_data/*')):
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)
            for f in poss.frames:
                for p in f.players:
                    count[p.id] = count.get(p.id, 0) + 1
                break
        joblib.dump(count, 'result/player_poss_count.pkl')

######### defense closeness
def player_dist(p0, p1):
    return np.sqrt((p0.x - p1.x)**2 + (p0.y - p1.y)**2)

def poss_defense_closeness(poss):
    dist = defaultdict(int) # distance for all offensive players
    nframes = defaultdict(int)

    for f in poss.frames:
        # from the view of offensive player
        for player in f.players:
            if player.team == poss.offensive_team:
                # find the defensive player
                dplayers = [(d, player_dist(d, player))
                            for d in f.players if d.team == poss.defensive_team]
                d = sorted(dplayers, key=lambda x: x[1])[0]
                dist[player.id] += d[1]
                nframes[player.id] += 1

    offensive_players = list(dist.keys())
    ballhandler = get_ball_handler(poss, offensive_players)
    isBallHandler = [op == ballhandler for op in offensive_players]
    return [dist[op] / nframes[op] for op in offensive_players], isBallHandler, offensive_players

def team_defense_closeness(game_dirs, savename):
    '''
    accurate to gamecode, quarter
    '''
    count = {}
    for game in game_dirs:
        for fn in glob.glob(game + '/*'):
            poss = joblib.load(fn)

            if count.get(poss.defensive_team, None) is None:
                count[poss.defensive_team] = []

            for episode in cutPoss(poss):
                dist, isBallHandler, offensive_players = poss_defense_closeness(episode)
                frameInfo = episode.frames[0].frameInfo
                frameInfo.transition = isTransition(episode, poss.attack_right)
                for i, d in enumerate(dist):
                    f = copy.deepcopy(frameInfo)
                    f.ballHandler = isBallHandler[i]
                    f.offensive_player = offensive_players[i]
                    count[episode.defensive_team].append((d, f))
                
        joblib.dump(count, savename)
        
if __name__ == '__main__':

    game_dirs =  glob.glob('../traj_data/*')
    
    ######################### Q1 #######################
    #end_event_dist()
    #traj_length_dist()
    #traj_length_debug() # for debugging purpose, print out the offending filename

    ######################### Q2 #######################
    #player_frames_count()
    #player_poss_count()

    ######################### Q3 #######################
    #team_defense_closeness(game_dirs, 'result/team_defense_closeness.pkl')

    ## cannot do this because I need to write a combine function first
    ## may not worth it, but definitely worth it for creating TMNIST dataset
    parallel_game(team_defense_closeness, game_dirs, savedir='result')
