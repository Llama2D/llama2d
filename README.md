# llama2d

## Setup

```bash
git clone https://github.com/llama2d/llama2d.git --recursive
cd transformers && pip install -e . && cd ..
pip install -r requirements.txt
playwright install
pre-commit install
```

## Secrets

Secrets are posted in [this Slack thread](https://agihouse.slack.com/archives/C05SR8PR4KE/p1695104312522089).

1. Download the `gcp-vision.json` credential file from our Slack channel and put it in `secrets/`.

2. Run the Modal login command in the Slack channel. It looks like this: `modal token set --token-id <secret> --token-secret <secret>`

## Datasets

Currently, each dataset needs to be downloaded locally using Playwright.

In the near future, we will be able to download the cached datasets from Huggingface. (Matt Mo is working on this.)

### Pretraining dataset

This dataset contains over 600 retail websites. The task is next-token prediction.

Specifically, the entire page is converted into tokens, and every token is given a coordinate position.

The model is trained to predict the next token. It is NOT trained to predict the next token's position.

This dataset is implemented in [`src/llama2d/datasets/pretraining.py`](https://github.com/Llama2D/llama2d/blob/main/src/llama2d/datasets/pretraining.py).

To download and cache this dataset, run the pretraining file:

```bash
python -m src.llama2d.datasets.pretraining
```

This will download all 600 websites from their URLs and save them to `src/data/pretraining-cache/`.

### Mind2Web dataset

This dataset contains ~1000 tasks from the Mind2Web dataset.

The task is to take an intention, a current webpage, and choose the correct action to take.

This dataset is mostly implemented but not tested.

To download this dataset, first download the Mind2Web `mhtml` files generated by Andrew Stelmach.

The zip with the files is [here](https://drive.google.com/file/d/1RGNcNTlQrZhF1KuGBcGenkON1u74_IYx/view). Download it and unzip it into `src/data/mind2web-mhtml`. Your `src/data/mind2web-mhtml` directory should look like this:

```
src/data/mind2web-mhtml
├── 0004f2a7-90d6-4f96-902a-b1d25d39a93d_before.mhtml
├── 00068a1e-b6a3-4c53-a60c-3ed777d4b05d_before.mhtml
├── 00146964-4b74-4e28-8292-5810a604639a_before.mhtml
├── 0018120a-8da1-4a36-a1c4-b4642c97211b_before.mhtml
```

In the near future, you will be able to download and cache the Mind2Web dataset like so:

```bash
python -m llama2d.datasets.mind2web
```

### Cached datasets

You can load a cached dataset with the `CachedDataset` class in `src/llama2d/datasets/cached.py`.

You can cache a dataset with the `save_dataset` function in `src/llama2d/datasets/cached.py`.

## Training

### Local training

> Note from Andrew Healey: I will get rid of local training once we get Llama2D pretraining/training on Modal. This is very temporary.

First, follow the [`facebookresearch/llama-recipes`](https://github.com/facebookresearch/llama-recipes/blob/main/examples/quickstart.ipynb) quickstart instructions to download the Llama weights.

This should result in a directory structure like so:
```
src/
...
llama2d/
...
llama/
...
llama-recipes/
├── models_hf
│   ├── 13B
│   │   ├── config.json
│   │   ├── generation_config.json
│   │   ├── pytorch_model-00001-of-00003.bin
│   │   ├── pytorch_model-00002-of-00003.bin
│   │   ├── pytorch_model-00003-of-00003.bin
│   │   ├── pytorch_model.bin.index.json
│   │   ├── special_tokens_map.json
│   │   ├── tokenizer.json
│   │   ├── tokenizer.model
│   │   └── tokenizer_config.json
│   └── 7B
│       ├── config.json
│       ├── generation_config.json
│       ├── pytorch_model-00001-of-00002.bin
│       ├── pytorch_model-00002-of-00002.bin
│       ├── pytorch_model.bin.index.json
│       ├── special_tokens_map.json
│       ├── tokenizer.json
│       ├── tokenizer.model
│       └── tokenizer_config.json
```

Then go to the `llama2d` directory and run the following command:

```bash
python -m src.llama2d.local.train
```

This will train a model on the cached pretraining dataset.

If you like, you can modify the config variables at the top of `src/llama2d/local/train.py` to change the training parameters.

These allow you to swap between the Llama2D model and the Llama model, use a cached or uncached dataset, change the # of epochs, choose your model size, etc.

This script only trains with QLoRa.

The best way to run this is on a Lambda Labs A10G instance for $0.60/hr.

### Modal training

To train a model with Modal, change your directory to `src/llama2d/modal/` and run i.e.

```bash
modal run train.py --dataset hf_dataset.py --repo src/llama2d/llama2d-mind2web --no-peft --num-epochs 4
```

`peft` is a synonym for LoRA. `hf_dataset` means we are using a dataset uploaded to Huggingface (thanks Matthew!). [`src/llama2d/llama2d-mind2web`](https://huggingface.co/datasets/llama2d/llama2d-mind2web/viewer/default/train?row=0) is the Huggingface repo containing the dataset.


## In the Repo

To add a requirement, add it to `requirements.in`, run `pip-compile`, and run `pip-sync`.

Run `black . --exclude '/transformers/|/venv/'` to format the code.

Pre-commit hooks are used to maintain code quality.
