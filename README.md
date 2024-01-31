<p align="center">
  <img src="https://raw.githubusercontent.com/llama2d/llama2d/main/llama2d.png" height="300" alt="2D Llama line-art" />
</p>
<p align="center">
  <em>2D Positional Embeddings for Webpage Structural Understanding</em> 🦙👀
</p>

# llama2d
How can we get LLM-based agents to understand the *visual structure* of a webpage? We fine-tune Llama on OCR'd screenshots of webpages but with 2D positional embeddings, enabling it to "see" the structure of a webpage rather than just a sequence of tokens.

To construct the dataset, we:
- took each MHTML provided by Mind2Web
- rendered it in Playwright
- tagged interactable elements
- ran OCR to get (x, y) coordinates of words on the page

We then calculate 2D positional embeddings for each word and fine-tune Llama!

Note: this repo is still a bit disorganized and a work in progress, but we encourage community contributions & forks to explore this direction in LLM web interaction!

## Setup

```bash
git clone https://github.com/llama2d/llama2d.git --recursive
cd transformers && pip install -e . && cd ..
pip install -r requirements.txt
playwright install
pre-commit install
```

## Secrets

1. Create a Google Cloud Vision credential file and put it at `secrets/gcp-vision.json`.

2. Run the Modal login command in the Slack channel. It looks like this: `modal token set --token-id <secret> --token-secret <secret>`

## Datasets

Datasets are defined in the `src/llama2d/datasets/` directory.

Every row of a dataset is defined by a prompt, a 2D "screen", and an output.

However, a row is converted into pure tokens before being fed into Llama - see [this dataset]() for an example.

You can visualize a dataset on Huggingface by copying all the numbers in a row and pasting it into [this webpage]().

### Synthetic datasets

We will have lots of synthetic datasets--i.e. the Zoo Compass dataset defined in `src/llama2d/datasets/synthetic/zoo_compass.py`.

These datasets are simple. They each spit out a bunch of rows with `prompt: str`, `screen: Llama2dScreen`, and `output: str`.

It is easy to create a `Llama2dScreen`:

```py
from llama2d.vision import Llama2dScreen

screen = Llama2dScreen()

screen.push_word(word="north",xy=(0.5,0))
screen.push_word(word="south",xy=(0.5,1))
screen.push_word(word="east",xy=(1,0.5))
screen.push_word(word="west",xy=(0,0.5))
```

To create this dataset, look at it in your console, and publish it to Huggingface, run the following:

```bash
python -m llama2d.datasets.synthetic.zoo_compass
```

I recommend reading the Zoo Compass dataset code for reference.

### Pretraining dataset

This dataset contains over 600 retail websites. The task is next-token prediction.

Here, the prompt and output are empty. The website text is all in the screen.

The model is trained to predict the next token of the website text. It is NOT trained to predict the position of the next token.

This dataset is implemented in [`src/llama2d/datasets/pretraining.py`](https://github.com/Llama2D/llama2d/blob/main/src/llama2d/datasets/pretraining.py).

To collect this dataset and upload it to Huggingface, run the file:

```bash
python -m src.llama2d.datasets.pretraining
```

### Mind2Web dataset

This dataset contains ~1000 tasks from the Mind2Web dataset.

The task is to take an intention, a screenshot of a webpage, and choose the correct action to take.

To download this dataset, first download the Mind2Web `mhtml` files generated by Andrew Stelmach.

The zip with the files is [here](https://drive.google.com/file/d/1RGNcNTlQrZhF1KuGBcGenkON1u74_IYx/view). Download it and unzip it into `src/data/mind2web-mhtml`. Your `src/data/mind2web-mhtml` directory should look like this:

```
src/data/mind2web-mhtml
├── 0004f2a7-90d6-4f96-902a-b1d25d39a93d_before.mhtml
├── 00068a1e-b6a3-4c53-a60c-3ed777d4b05d_before.mhtml
├── 00146964-4b74-4e28-8292-5810a604639a_before.mhtml
├── 0018120a-8da1-4a36-a1c4-b4642c97211b_before.mhtml
```

To process and cache the Mind2Web dataset, run the following:

```bash
python -m llama2d.datasets.mind2web
```

## Modal training

To train a model with Modal, change your directory to `src/llama2d/modal/` and run i.e.

```bash
modal run train.py --dataset hf_dataset.py --repo src/llama2d/llama2d-mind2web --no-peft --num-epochs 4
```

`peft` is a synonym for LoRA. `hf_dataset` means we are using a dataset uploaded to Huggingface (thanks Matthew!). [`src/llama2d/llama2d-mind2web`](https://huggingface.co/datasets/llama2d/llama2d-mind2web/viewer/default/train?row=0) is the Huggingface repo containing the dataset.

## In the Repo

To add a requirement, add it to `requirements.in`, run `pip-compile`, and run `pip-sync`.

Run `black . --exclude '/transformers/|/venv/'` to format the code.

Pre-commit hooks are used to maintain code quality.

## Citations

```
bibtex
@misc{llama2d2024,
  title        = {Llama2D},
  author       = {Houjun Liu and Andrew Healey and Andrew Stelmach and Christopher Settles and Rohan Pandey},
  year         = {2024},
  howpublished = {GitHub},
  url          = {https://github.com/llama2d/llama2d}
}
```
