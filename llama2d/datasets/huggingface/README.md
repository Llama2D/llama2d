# Publish Datset to HF

### Requirements
* Huggingface CLI

Set-up via
```
pip install -r reqs.txt
```

* [Login to Hugginface](https://huggingface.co/docs/huggingface_hub/guides/upload)
```
huggingface-cli login --token $HUGGINGFACE_TOKEN
```

### Publish!

Publish dataset to repo via:
```
python -m llama2d.datasets.huggingface.publish -C [CACHE_DIR] -R [REPO]
```

### Use

As instructed [officially](https://huggingface.co/docs/datasets/load_hub):

```
from datasets import load_dataset_builder
ds_builder = load_dataset_builder("supermomo668/Llama2D-Pretrain")
```
Optionally, push cached Pytorch dataset files as well. Set REPO to your desired repo.
```
$Llama2d/
huggingface-cli upload [REPO] data/pretraining-cache pretraining-cache
```