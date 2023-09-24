from llama2d.datasets.cached import CachedDataset
from llama2d.constants import PRETRAINING_CACHE_DIR

import torch

def get_custom_dataset(dataset_config, tokenizer, split):

    use_2d = dataset_config.use_2d

    import gdown
    gdown.download(id="1bgbnuVQjhRku60gCLrFfqfM66bp0Z4sI")
    # unzip the dataset
    import os
    os.system("unzip -qo cached-pretrain.zip")

    train_percent = 80

    full_dataset = CachedDataset("cached-pretrain",use_2d=use_2d,keep_fraction=dataset_config.keep_fraction)

    train_size = int(len(full_dataset)*train_percent/100)
    val_size = len(full_dataset)-train_size

    train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    return train_dataset if split == "train" else val_dataset