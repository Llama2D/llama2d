from llama_recipes.datasets.utils import Concatenator

from llama2d.llama2d.datasets.pretraining import Llama2dPretrainingDataset
from llama2d.llama2d.datasets.pretraining_urls import urls


def format_text(row, tokenizer):
    return tokenizer(row)


def get_custom_dataset(dataset_config, tokenizer, split):
    urls = [
            "https://github.com/OSU-NLP-Group/Mind2Web",
            "https://stackoverflow.com/questions/60352003/how-to-download-webpage-as-mhtml"
        ]
    dataset = Llama2dPretrainingDataset(model="decapoda-research/llama-7b-hf",
                                        urls=urls)

    return dataset
