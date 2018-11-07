import numpy as np
import random, os
import torch, warnings, glob
import multiprocessing
from pathos.multiprocessing import _ProcessPool as Pool
import tqdm, math, time
from sklearn.externals import joblib
from torch.utils.data import Dataset

class LoadedBballData(Dataset):

    def __init__(self, data_path):
        self.meta_info = joblib.load(os.path.join(data_path, 'meta.pkl'))
        self.data_path = data_path

    def __len__(self):
        return self.meta_info['len']

    def __getitem__(self, idx):
        file_index = math.floor(idx / self.meta_info['traj/file'])
        within_file_index = idx % self.meta_info['traj/file']
        xs, ys = joblib.load(os.path.join(self.data_path, '%d.pkl' % file_index))
        return xs[within_file_index], ys[within_file_index]

def save_bball_data_helper(dataset, indices, savename):
    # get dataset saved
    xs = []
    ys = []
    for i in tqdm.tqdm(indices):
        x, y = dataset[i]
        xs.append(x)
        ys.append(y)
    joblib.dump((xs, ys), savename)

def parallel_bball_data_helper(dataset, savedir, cpus=30):
    result_list = []
    pool = Pool(cpus)

    tasks_per_cpu = math.ceil(len(dataset) / cpus)
    # save meta information
    joblib.dump({'len': len(dataset),
                 'traj/file': tasks_per_cpu},
                os.path.join(savedir, 'meta.pkl'))

    index = 0
    i = 0
    while index < len(dataset):
        indices = range(index, min(index + tasks_per_cpu, len(dataset)))
        index = index + tasks_per_cpu
        savename = os.path.join(savedir, '%d.pkl' % i)
        i += 1
        result_list.append(pool.apply_async(func=save_bball_data_helper,
                                            args=(dataset, indices, savename)))
    while True:
        try:
            def call_if_ready(result):
                if result.ready():
                    result.get()
                    return True
                else:
                    return False  
            done_list = list(map(call_if_ready, result_list))
            print('{}/{} done'.format(sum(done_list), len(result_list)))
            if np.all(done_list):
                break
            time.sleep(3)
        except:
            pool.terminate()
            raise
    print('finished preprocessing')

def save_bball_data(dataset, savedir, override_existing=False):
    file_exist = os.path.exists(savedir)
    if file_exist:
        warnings.warn("%s exist, override: %r" % (savedir, override_existing))

    if not file_exist or override_existing:
        print("==>save data of size %d in %s" % (len(dataset), savedir))
        if file_exist:
            os.system('rm -r %s' % savedir)
        os.system('mkdir -p %s' % savedir)

        # get dataset saved
        parallel_bball_data_helper(dataset, savedir)

        # indices = range(len(dataset))
        # index = 0
        # save_bball_data_helper(dataset, indices,
        #                        os.path.join(savedir, "%d.pkl" % index))
        print("==>save data done")

def load_bball_data(load_path):
    print('==>load data %s' % load_path)
    dset = LoadedBballData(load_path)
    print('==>load data of size %d done' % len(dset))
    return dset
    
class BballDataset(Dataset):
    '''return one possession'''
    def __init__(self, traj_locations, transform):
        ''' 
        transform turns a possession into (x, y), see bball_transform/image_transform.py
        '''
        self.traj_locations = traj_locations
        self.transform = transform

    def __len__(self):
        return len(self.traj_locations)
        
    def __getitem__(self, idx):
        data = joblib.load(self.traj_locations[idx])
        return self.transform(data)
