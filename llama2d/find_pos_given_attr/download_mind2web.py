from datasets import load_dataset

# Load the Mind2Web dataset
dataset = load_dataset("osunlp/Mind2Web")

# Print the first sample for verification

from pprint import pprint

example = dataset['train'][0]

pprint(example)
# breakpoint()

actions = example['actions']

print(actions[0].keys())

print(example['action_reprs'])