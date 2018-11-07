import numpy as np
import os, copy
import torch
import torch.nn as nn
from torch.autograd import Variable
import torchvision.transforms as transforms
import torch.nn.functional as F
import torch.optim as optim
import time
import math, tqdm
from lib.utils import timeSince
from lib.utils import random_split_dataset
import random
from lib.model import MODELS
import torch.backends.cudnn as cudnn
import warnings, argparse
from lib.experiment import SYNTHETIC_EXPERIMENTS

model_names = MODELS.keys()
exp_names = SYNTHETIC_EXPERIMENTS.keys()

# parse arguments
parser = argparse.ArgumentParser(description='bball 2018: trajectory representation')
parser.add_argument('--arch', '-a', metavar='ARCH', default='MLP',
                    choices=model_names,
                    help='model architecture: ' +
                    ' | '.join(model_names) +
                    ' (default: MLP)')
parser.add_argument('--seed', default=None, type=int,
                    help='seed for initializing training. ')
parser.add_argument('--use_gpu', action='store_true',
                    help='whether or not use gpu')
parser.add_argument('--smdir', default='models', type=str,
                    help='directory to save model')
parser.add_argument('--sddir', default='bball_data', type=str,
                    help='directory to save bball data')
parser.add_argument('--batch_size', default=32, type=int, metavar='B',
                    help='batch_size')
parser.add_argument('--niters', default=500, type=int, metavar='N',
                    help='number of total iterations to run')
parser.add_argument('--n_save_model', default=10, type=int,
                    help='number of model save and validation eval in trainer')
parser.add_argument('--exp', default="example", type=str,
                    choices=exp_names,
                    help='experiment name to run')
parser.add_argument('--debug', action='store_true',
                    help='debug mode')
args = parser.parse_args()

################################## setting ############################################
os.system('mkdir -p %s' % args.smdir)
os.system('mkdir -p %s' % args.sddir)

if args.seed is not None:
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    cudnn.deterministic = True
    warnings.warn('You have chosen to seed training. '
                  'This will turn on the CUDNN deterministic setting, '
                  'which can slow down your training considerably! '
                  'You may see unexpected behavior when restarting '
                  'from checkpoints.')
    
################################### get data ###########################################
experiment = SYNTHETIC_EXPERIMENTS[args.exp]
data = experiment.get_data(args)

# todo: should do temporal splitting, but good for now
train_set, val_set, test_set = random_split_dataset(data, [0.6, 0.1, 0.3])

savedir_tr = os.path.join(args.sddir, 'train')
savedir_val = os.path.join(args.sddir, 'val')
savedir_te = os.path.join(args.sddir, 'test')

train_data = experiment.wrap_dataset(train_set, savedir_tr, args)
val_data = experiment.wrap_dataset(val_set, savedir_val, args)
test_data = experiment.wrap_dataset(test_set, savedir_te, args)

######################################### run models ###################################
experiment.run(args, train_data, val_data)
