from glob import glob
from pathlib import Path

import torch
from torch.utils.data import Dataset


def save_dataset(dataset, save_dir: Path):
    # make the directory if it doesn't exist
    save_dir.mkdir(parents=True, exist_ok=True)

    for i in range(len(dataset)):
        torch.save(dataset[i], save_dir / f"{i}.pt")


class CachedDataset(Dataset):
    def __init__(self, load_dir, use_2d=True, keep_fraction=1.0):
        self.load_dir = load_dir
        self.files = sorted(glob(f"{load_dir}/*.pt"))
        self.use_2d = use_2d
        self.keep_fraction = keep_fraction

    def __getitem__(self, i):
        ret = torch.load(self.files[i])
        # if not self.use_2d:
        #     return {k: v for k, v in ret.items() if k != "coords"}
        return {k: v.to(torch.bfloat16) if k == "coords" else v for k, v in ret.items()}

    def __len__(self):
        return int(len(self.files) * self.keep_fraction)
