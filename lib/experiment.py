import torch.nn as nn
import math, torch, os
from lib.train import TrainFeedForward
from lib.model import MODELS
from torch.utils.data import DataLoader
from lib.data import BballDataset, save_bball_data, load_bball_data
from lib.utils import get_traj_locations
from lib.bball_transform.image_transform import transform_producer

# exact setting for each experiment ran
SYNTHETIC_EXPERIMENTS = {}

class ImageExperiment(object):

    def get_data(self, args):
        raise NotImplementedError()
        
    def run(self, args, train_data, val_data):
        net = MODELS[args.arch]([94 * 50 * 11, 30, 1])

        if args.arch == 'MLP':
            savename = 'mlp.pth.tar'
        
        savename = os.path.join(args.smdir, savename)
        optimizer = torch.optim.Adam(net.parameters())
        criterion = nn.MSELoss()

        trainer = TrainFeedForward(net, optimizer, criterion, train_data,
                                   save_filename=savename, val_data=val_data,
                                   use_gpu=args.use_gpu, n_iters=args.niters,
                                   n_save=args.n_save_model,
                                   batch_size=args.batch_size)
        if os.path.exists(savename):
            trainer.load_checkpoint(savename)

        trainer.train()

class ExampleExperiment(ImageExperiment):

    def get_data(self, args):
        if args.debug:
            path = '../debug_traj_data'
        else:
            path = '../traj_data'
        traj_locations = get_traj_locations(path)
        transform_image_data = transform_producer(1)
        bball_dataset = BballDataset(traj_locations, transform=transform_image_data)
        return bball_dataset

    def wrap_dataset(self, dset, savedir, args):
        # save the data
        save_bball_data(dset, savedir)

        # return dataloader of the saved data
        # todo: shuffle data, increase number of worker
        dset = load_bball_data(savedir)
        return DataLoader(dset, batch_size=args.batch_size) 

SYNTHETIC_EXPERIMENTS['example'] = ExampleExperiment()
