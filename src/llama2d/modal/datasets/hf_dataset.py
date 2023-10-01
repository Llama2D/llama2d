from llama2d.datasets.huggingface import HuggingFaceDataset


def get_custom_dataset(dataset_config, tokenizer, split):
    repo = dataset_config.repo
    return HuggingFaceDataset(repo, split,cache_dir="/hf_cache")
