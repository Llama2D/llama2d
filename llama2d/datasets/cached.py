import torch
from torch import nn

def save_dataset(dataset, save_dir):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    for i in range(len(dataset)):
        torch.save(dataset[i], f"{save_dir}/{i}.pt")


import os
from glob import glob


class CachedDataset(torch.utils.data.Dataset):
    def __init__(self, load_dir):
        self.load_dir = load_dir
        self.files = sorted(glob(f"{load_dir}/*.pt"))

    def __getitem__(self, i):
        return torch.load(self.files[i])

    def __len__(self):
        return len(self.files)
