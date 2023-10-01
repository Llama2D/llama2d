from llama2d.datasets.huggingface import HuggingFaceDataset


def get_custom_dataset(dataset_config, tokenizer, split):
    repo = dataset_config.repo
    use_2d = dataset_config.use_2d
    print("get_custom_dataset, use_2d:", use_2d)
    return HuggingFaceDataset(repo, split,cache_dir="/hf_cache", keep_fraction=dataset_config.keep_fraction,use_2d=use_2d)
