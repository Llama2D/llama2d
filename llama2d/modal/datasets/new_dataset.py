import os
print(os.getcwd())

from llama2d.datasets.pretraining import Llama2dPretrainingDataset
from llama2d.datasets.pretraining_urls import urls

from llama_recipes.datasets.utils import Concatenator


def format_text(row, tokenizer):
    return tokenizer(row)


def get_custom_dataset(dataset_config, tokenizer, split):
    urls = [
            "https://github.com/OSU-NLP-Group/Mind2Web",
            "https://stackoverflow.com/questions/60352003/how-to-download-webpage-as-mhtml"
        ]
    dataset = Llama2dPretrainingDataset(model="decapoda-research/llama-7b-hf",
                                        urls=urls)
    full_dataset = dataset

    # Since the dataset has no train/test split, we create one and select it
    dataset = full_dataset.train_test_split(
        train_size=10000,
        test_size=200,
        seed=42,
    )["train" if split == dataset_config.train_split else "test"]

    dataset = dataset.map(Concatenator(), batched=True, batch_size=None)

    return dataset
