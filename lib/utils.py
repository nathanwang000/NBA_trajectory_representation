import time, math, torch, shutil, glob
import numpy as np

import os

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.sum_2 = 0 # sum square
        self.var = 0
        self.count = 0
    
    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count
        self.sum_2 += val**2 * n
        self.var = self.sum_2 / self.count - self.avg**2

class PrintTable(object):
    '''print tabular data in a nice format'''
    def __init__(self, nstr=15, nfloat=5):
        self.nfloat = nfloat
        self.nstr = nstr

    def _format(self, x):
        if type(x) is float:
            x_tr = ("%." + str(self.nfloat) + "f") % x
        else:
            x_tr = str(x)
        return ("%" + str(self.nstr) + "s") % x_tr

    def print(self, row):
        print( "|".join([self._format(x) for x in row]) )

def smooth(sequence, step=1):
    out = np.convolve(sequence, np.ones(step), 'valid') / step
    return out

def random_split_dataset(dataset, proportions):
    n = len(dataset)
    ns = [int(math.floor(p*n)) for p in proportions]
    ns[-1] += n - sum(ns)
    return torch.utils.data.random_split(dataset, ns)
    
def timeSince(since):
    now = time.time()
    s = now - since
    m = math.floor(s / 60)
    s -= m * 60
    return '%dm %ds' % (m, s)

def get_traj_locations(data_dir, criterion=lambda fn: True):
    '''return traj_locations given data_dir, assume data directory contains
    subdirectories containing individual possessions'''
    traj_locations = []

    for fn in glob.glob(data_dir + "/*"):
        for poss_fn in glob.glob(fn + "/*"):
            # print(poss_fn)
            # print(criterion(poss_fn))
            if criterion(poss_fn):
                traj_locations.append(poss_fn)
    return traj_locations

# criteria for get_traj_locations
def shot_only_criterion(fn):
    if fn.split(',')[-2].strip() in ('Field Goal Made', 'Field Goal Missed'):
        return True
    return False

def shot_length_criterion(fn, min_len=3, max_len=24):

    '''

    This criterion selects shot possessions with length >= 3secs and <= 24 secs

    :param fn: trajectory filename
    :param min_len: minimum number of frames
    :param max_len: maximum number of frames
    :return: True or False
    '''

    traj_len = eval(fn.split(',')[2]) # calculate trajectory length using wall clock time

    if shot_only_criterion(fn) and traj_len >= min_len and traj_len <= max_len:
        return True

    return False
