'''
transform takes a legacy.possession as input and output data needed for __getitem__
for PyTorch dataset. To add in order of players, refer to
https://gitlab.eecs.umich.edu/jiaxuan/bball2017/blob/master/lib/training/dataset.py
'''
from lib.process_possession import cutOnce
# from collections import namedtuple
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


def episode2flat(episode):

    # traj = namedtuple('Trajectory', ['xp', 'yp', 'xb', 'yb', 'zb'])
    xp = []
    yp = []
    xb = []
    yb = []
    zb = []
    for frame in episode.frames:
        for player in frame.players:
            xp.append(player.x)
            yp.append(player.y)

        xb.append(frame.ball.x)
        yb.append(frame.ball.y)
        zb.append(frame.ball.z)

    xp, yp, xb, yb, zb = np.array(xp), np.array(yp), np.array(xb), np.array(yb), np.array(zb)

    xp = xp.reshape(-1,10)
    yp = yp.reshape(-1,10)
    xb = xb.reshape(-1,1)
    yb = yb.reshape(-1,1)
    zb = zb.reshape(-1,1)

    return np.hstack((xp, yp, xb, yb, zb)).reshape(-1)

#################### main function #################################
def transform_producer(up_to=1, crop_len=2):
    '''
    :param up_to: up to the last _ seconds
    :param crop_len: crop _ seconds before the last second as the input data
    :return: cropped raw data
    '''


    def transform_flat_data(poss):
        # chop it up, turn each episode into raw data with length crop_len
        episode, _ = cutOnce(poss, up_to, crop_len)
        x = episode2flat(episode)
        y = poss.expected_outcome
        return x, y

    return transform_flat_data