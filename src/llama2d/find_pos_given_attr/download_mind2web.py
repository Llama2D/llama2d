from pprint import pprint

from datasets import load_dataset

# Load the Mind2Web dataset
dataset = load_dataset("osunlp/Mind2Web")

# Print the first sample for verification


example = dataset["train"][0]

pprint(example)
# breakpoint()

actions = example["actions"]

print(actions[0].keys())

print(example["action_reprs"])
