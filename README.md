# llama2d


# transformers

At the beginning of the hackathon, I said 2D position embeddings could be added in `main.py` without modifying Llama's source code.

This was wrong.

You should clone this repo with `git clone https://github.com/llama2d/llama2d.git --recursive` to get the transformers submodule.
Then `cd transformers && pip install -e .`