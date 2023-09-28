import os
from glob import glob

import torch


def save_dataset(dataset, save_dir):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    for i in range(len(dataset)):
        torch.save(dataset[i], f"{save_dir}/{i}.pt")


class CachedDataset(torch.utils.data.Dataset):
    def __init__(self, load_dir, use_2d=True, keep_fraction=1.0):
        self.load_dir = load_dir
        self.files = sorted(glob(f"{load_dir}/*.pt"))
        self.use_2d = use_2d
        self.keep_fraction = keep_fraction

    def __getitem__(self, i):
        ret = torch.load(self.files[i])
        if not self.use_2d:
            return {k: v for k, v in ret.items() if k != "coords"}
        return {k: v.to(torch.bfloat16) if k == "coords" else v for k, v in ret.items()}

    def __len__(self):
        return int(len(self.files) * self.keep_fraction)
