import types
from dataclasses import dataclass
from time import time

import numpy as np
import torch
from datasets import Dataset
from torch.utils import data

#
from llama2d.datasets.cached import CachedDataset


@dataclass
class DatasetInfo:
    repo: str
    desc: str


def dataset_dict_to_list(dataset_dict):
    """
    Converts a Torch dataset stored as a dictionary to a list of dictionaries.

    Args:
        dataset_dict (dict): The input dataset dictionary with keys 'input_ids', 'coords', 'labels', and 'attention_mask'.

    Returns:
        list: A list of dictionaries where each dictionary contains values for the keys at each index.
    """
    keys = dataset_dict.keys()
    num_samples = len(dataset_dict[list(keys)[0]])
    # Assuming all keys have the same length
    dataset_list = []
    for i in range(num_samples):
        sample_dict = dict.fromkeys(keys)
        for key in keys:
            sample_dict[key] = dataset_dict[key][i]
        dataset_list.append(sample_dict)
    return dataset_list


def to(a, device: torch.device):
    if torch.is_tensor(a):
        return a.to(device)
    elif isinstance(a, dict):
        return {k: to(v, device) for k, v in a.items()}
    elif isinstance(a, (list, tuple)):
        return type(a)(to(v, device) for v in a)
    else:
        return a


from tqdm import tqdm


def pt2hf(torch_dataset: data.Dataset, convert_type: types = torch.float32):
    torch_dataset = [el for el in tqdm(torch_dataset) if el is not None]
    if convert_type is not None:
        torch_dataset = to(torch_dataset, convert_type)
    # import pdb; pdb.set_trace()
    try:
        dset_hf = Dataset.from_list(torch_dataset)
    except Exception as e:
        print(f"Exception while converting to hf dataset: {e}")
        import pdb

        pdb.set_trace()
    return dset_hf


def publish_pt_dataset(ds_pt, dataset_info):
    try:
        ds = pt2hf(ds_pt)  # may require setting: convert_type=np.float32
        print(f"Dataset type:{ds}")
        ds.info.description = dataset_info.desc
        ds.set_format(type="torch", columns=list(ds[0].keys()))
        ds.push_to_hub(dataset_info.repo)
        print(f"Push succeeded.")
    except Exception as e:
        print(f"Exception while publishing: {e}")
        raise e


import torch
from datasets import load_dataset

dtypes = {
    "coords": torch.float16,
    "input_ids": torch.int64,
    "labels": torch.int64,
    "attention_mask": torch.int64,
}


class HuggingFaceDataset(torch.utils.data.Dataset):
    def __init__(
        self, repo: str, split: str, keep_fraction: float = 1.0, use_2d: bool = True
    ):
        print("Loading dataset...")
        start_time = time()

        hf_dataset = load_dataset(repo)

        print(f"Loaded dataset in {time()-start_time} seconds.")
        # dataset = [d for d in dataset if d is not None and sum([1 for i in d["labels"] if i>0])>0]
        df = hf_dataset["train"].to_pandas()
        df_filtered = df[df.labels.apply(lambda x: np.sum(np.array(x[::-1]) > 0) > 0)]

        dataset = Dataset.from_pandas(df_filtered)

        # split into train/val
        train_percent = 80
        train_size = int(len(dataset) * train_percent / 100)
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size]
        )

        self.dataset = train_dataset if split == "train" else val_dataset

        # keep only a fraction of the dataset
        if keep_fraction < 1.0:
            self.dataset = torch.utils.data.Subset(
                self.dataset, range(int(len(self.dataset) * keep_fraction))
            )

        self.use_2d = use_2d

    def __getitem__(self, index):
        hf_dict = self.dataset[index]

        # convert to torch tensors
        ret = {k: torch.tensor(v, dtype=dtypes[k]) for k, v in hf_dict.items()}

        # if not self.use_2d:
        #    del ret["coords"]

        return ret

    def __len__(self):
        return len(self.dataset)


if __name__ == "__main__":
    import argparse

    from ..constants import PRETRAINING_CACHE_DIR

    parser = argparse.ArgumentParser(description="Description of your script")
    # Argument 1: First argument (e.g., input file)
    parser.add_argument(
        "-C",
        "--cache_dir",
        type=str,
        default=PRETRAINING_CACHE_DIR,
        help="Cache directory",
    )
    # Argument 2: Second argument (e.g., output file)
    parser.add_argument(
        "-R",
        "--repo",
        default="supermomo668/Llama2D-Pretrain",
        type=str,
        help="Name of Repo",
    )
    # Argument 2: Second argument (e.g., output file)
    parser.add_argument(
        "-D",
        "--desc",
        default="Llama2D is a project from AGI UI/UX Hackathon. Check our main Git Repo at : https://github.com/Llama2D/llama2d/tree/main",
        type=str,
        help="Name of Repo",
    )

    args = parser.parse_args()
    ds_pt = CachedDataset(args.cache_dir)
    publish_pt_dataset(ds_pt, args)
