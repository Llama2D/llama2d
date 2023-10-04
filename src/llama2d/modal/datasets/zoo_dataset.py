from llama2d.datasets.synthetic.zoo_compass import Llama2dZooCompassDataset

dataset_registry = {}


def get_custom_dataset(dataset_config, tokenizer, split):
    keep_fraction = dataset_config.keep_fraction
    train_size = int(5000 * keep_fraction)
    val_size = int(200 * keep_fraction) # make val_size very small - we're short on GPU time
    return Llama2dZooCompassDataset(
        num_screens=train_size if split == "train" else val_size,
        words_per_screen=20,
    )
