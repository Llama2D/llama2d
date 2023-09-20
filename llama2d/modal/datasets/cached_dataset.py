from llama2d.datasets.cached import CachedDataset
from llama2d.constants import PRETRAINING_CACHE_DIR

def get_custom_dataset(dataset_config, tokenizer, split):

    import gdown
    gdown.download(id="1bgbnuVQjhRku60gCLrFfqfM66bp0Z4sI")
    # unzip the dataset
    import os
    os.system("unzip -qo cached-pretrain.zip")

    return CachedDataset("cached-pretrain")