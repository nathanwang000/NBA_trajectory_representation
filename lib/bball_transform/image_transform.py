''' 
transform takes a legacy.possession as input and output data needed for __getitem__
for PyTorch dataset. To add in order of players, refer to 
https://gitlab.eecs.umich.edu/jiaxuan/bball2017/blob/master/lib/training/dataset.py
'''
from lib.process_possession import cutOnce
import numpy as np
import torch

def order_team_players(players, gamecode):
    # todo: sort by position
    # see https://gitlab.eecs.umich.edu/jiaxuan/bball2017/blob/master/lib/training/dataset.py
    return sorted(players, key=lambda p: p.id)
                  
def order_players(frame, offense_team):
    players = frame.players
    gamecode = frame.frameInfo.gamecode
    # first order by teams, offense team first
    offense = filter(lambda p: p.team == offense_team, players)
    defense = filter(lambda p: p.team != offense_team, players)

    # within each team, order by player position, break tie using player id
    # {'C', 'F', 'F/C', 'G', 'G/F', 'PF', 'PG', 'SF', 'SG'}
    offense = order_team_players(offense, gamecode)
    defense = order_team_players(defense, gamecode)

    players = []
    players.extend(list(offense))
    players.extend(list(defense))

    return players
                                                    
def fill_trajectory(episode, decay_rate, right):
    """
    Fills in court frame by frame (from end to beginning)
    decay_rate determines exponential decay of intensity
    if attack right, flip to the left side
    """
    # choosing 11x94x50 pixel rep
    court = np.zeros((11, 94, 50))
    fill_val = 1
    for frame in reversed(episode.frames):
        im = fill_court(court[0], frame.ball, fill_val, right)
        court[0] = im
        for i, player in enumerate(order_players(frame, episode.offensive_team)):
            im = fill_court(court[i+1], player, fill_val, right)
            court[i+1] = im
        fill_val = fill_val * decay_rate

    return court

def fill_court(court, item, fill, right):
    """
    Given a court and a frame, fill the court values
    according to frame positions
    """
    if right:
        # map to the other side
        x = 94 - item.x
        y = 50 - item.y
    else:
        x = item.x
        y = item.y

    discrete_x = np.clip(round(x)-1, 0, 93)
    discrete_y = np.clip(round(y)-1, 0, 49)    
    court[discrete_x, discrete_y] = fill
    return court
    
def episode2image(episode):
    decay_factor = 0.99
    return torch.from_numpy(fill_trajectory(episode,
                                            decay_factor,
                                            episode.attack_right)).float()

#################### main function #################################
def transform_producer(up_to=1):
    
    def transform_image_data(poss):
        # chop it up, turn each episode into image data, and output (x, y)
        # use information up to up_to second to build the image
        episode, _ = cutOnce(poss, up_to)
        x = episode2image(episode)
        y = poss.expected_outcome
        return x, y
    
    return transform_image_data
