import torch
from torch import nn

def save_dataset(dataset,save_dir):
    for i in range(len(dataset)):
        torch.save(dataset[i],f"{save_dir}/{i}.pt")

import os
class LoadedDataset(torch.utils.data.Dataset):
    def __init__(self,load_dir):
        self.load_dir = load_dir
    def __getitem__(self,i):
        return torch.load(f"{self.load_dir}/{i}.pt")
    def __len__(self):
        return len(os.listdir(self.load_dir)