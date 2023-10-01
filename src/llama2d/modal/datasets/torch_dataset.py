from llama2d.datasets.synthetic.zoo_compass import Llama2dZooCompassDataset

dataset_registry = {

}

def get_custom_dataset(dataset_config, tokenizer, split):
    train_size = 5000
    val_size = 1000
    return Llama2dZooCompassDataset(
        num_screens=train_size if split == "train" else val_size,
        words_per_screen=20,
    )
