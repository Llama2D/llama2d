from llama2d.datasets.cached import CachedDataset
from llama2d.constants import PRETRAINING_CACHE_DIR

def get_custom_dataset(dataset_config, tokenizer, split):

    use_2d = dataset_config.use_2d

    import gdown
    gdown.download(id="1bgbnuVQjhRku60gCLrFfqfM66bp0Z4sI")
    # unzip the dataset
    import os
    os.system("unzip -qo cached-pretrain.zip")

    return CachedDataset("cached-pretrain",use_2d=use_2d,keep_fraction=dataset_config.keep_fraction)