# llama2d


# transformers

At the beginning of the hackathon, I said 2D position embeddings could be added in `main.py` without modifying Llama's source code.

This was wrong.

You should clone this repo with `git clone https://github.com/llama2d/llama2d.git --recursive` to get the transformers submodule.
Then `cd transformers && pip install -e .`


# LlamaForCausalLM

This is my modified Llama class.

It can be trained and inferenced.

To inference with coords, run `model.generate(..., coords=coords)`, where `coords` is a list of 2D coordinates.

To train with coords, return a dictionary like so:

```python
class MyDataset(Dataset):
    def __getitem__(self, idx):
        ...
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "coords": coords,
        }
```
