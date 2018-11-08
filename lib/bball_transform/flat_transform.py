'''
transform takes a legacy.possession as input and output data needed for __getitem__
for PyTorch dataset. To add in order of players, refer to
https://gitlab.eecs.umich.edu/jiaxuan/bball2017/blob/master/lib/training/dataset.py
'''
from lib.process_possession import cutOnce
import numpy as np
import torch

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


def expand_trajectory(episode):
    """
    Fills in timeseries of x coordinates and y coordinates from beginning to end
    """
    x_vals = {}
    y_vals = {}
    for player in range(11):
        x_vals[p] = []
        y_vals[p] = []
    for frame in episode.frames:
        x_vals[0].append(frame.ball.x)
        y_vals[0].append(frame.ball.y)
        for i, player in enumerate(order_players(frame, episode.offensive_team)):
            x_vals[i + 1].append(player.x)
            y_vals[i + 1].append(player.y)

    final_ts = []

    for player in range(11):
        final_ts.append(np.array(x_vals[player]))
        final_ts.append(np.array(y_vals[player]))

    return np.array(final_ts)


def episode2ts(episode):
    return torch.from_numpy(expand_trajectory(episode)).float()


#################### main function #################################
def transform_producer(up_to=1):
    def transform_ts_data(poss):
        # chop it up, turn each episode into image data, and output (x, y)
        # use information up to up_to second to build the image
        episode, _ = cutOnce(poss, up_to)
        x = episode2ts(episode)
        y = poss.expected_outcome
        return x, y

    return transform_ts_data