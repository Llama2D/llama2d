# use headless
import matplotlib
from matplotlib import pyplot as plt
from playwright.sync_api import sync_playwright

from transformers import LlamaTokenizer

matplotlib.use("Agg")

# noqa
"""
pytorch input is a dictionary of the form
{
    "input_ids": [ids of the tokens, from 0 to vocab_size-1],
    "attention_mask": [0 for padding, 1 for non-padding],
    "coords": [x,y] for each token - normalized to [0,1] for tokens with coords, and (-1,-1) for tokens without coords
    "labels": [ids of the tokens, from 0 to vocab_size-1] - same as input_ids, but with -100 for tokens that should not be predicted # noqa
}
"""


model_path = "decapoda-research/llama-7b-hf"
tokenizer = LlamaTokenizer.from_pretrained(model_path)

# print(tokenizer.convert_ids_to_tokens([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]))


def viz_pt_input(pt_input):
    input_ids = pt_input["input_ids"]
    attention_mask = pt_input["attention_mask"]
    coords = pt_input["coords"]
    # labels = pt_input["labels"]

    # graph tokens with coords in a matplotlib figure
    # print the tokens without coords

    # every word has a few tokens with the same coord.
    # we should generate the word, turn it into a string, then plot it at the coord

    without_coords = [
        input_ids[i]
        for i in range(len(input_ids))
        if coords[i][0] == -1 and attention_mask[i] == 1
    ]

    with_coords = [
        (input_ids[i], coords[i])
        for i in range(len(input_ids))
        if coords[i][0] != -1 and attention_mask[i] == 1
    ]
    # split with_coords into words -
    # where a word is a list of tokens with the same coord
    words = []
    current_word = []
    current_coord = None
    for token in with_coords:
        if current_coord is None or (token[1] != current_coord).any():
            if len(current_word) > 0:
                words.append(current_word)
            current_word = []
            current_coord = token[1]
        current_word.append(token)
    if len(current_word) > 0:
        words.append(current_word)

    # plot with_coords as text on a matplotlib figure

    fig = plt.figure()
    # make fig very big
    fig.set_size_inches(20, 20)

    ax = fig.add_subplot(111)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_aspect("equal")

    for word in words:
        word_str = "".join(tokenizer.convert_ids_to_tokens([i[0] for i in word]))
        word_coord = word[0][1]
        # very small text
        ax.text(
            word_coord[0],
            1 - word_coord[1],
            word_str,
            fontsize=10,
            horizontalalignment="center",
            verticalalignment="center",
        )

    # save the figure
    fig.savefig("tokens_with_coords.png")

    normal_str = "".join(tokenizer.convert_ids_to_tokens(input_ids))
    print(normal_str)
    print()

    # as a str:
    without_coords_str = "".join(tokenizer.convert_ids_to_tokens(without_coords))
    print(without_coords_str)

    print("<Open token_with_coords.png to see the screen>")


from torch.utils.data import Dataset


def debug_dataset(dataset: Dataset):
    pt_input = None

    action = None
    i = 0
    while i < len(dataset):
        pt_input = dataset[i]
        if pt_input is not None:
            viz_pt_input(pt_input)
            action = input("Continue? [y/n/debug/<int skip>]")
            if action == "n":
                break
            if action.startswith("d"):
                import pdb

                pdb.set_trace()
            # check if action is an integer - then skip that many
            if action.isdigit():
                print(f"Skipping {action}...")
                i += int(action)
                continue
        i += 1

    assert pt_input is not None, "Didn't find any valid dataset entries!"
    if action != "n":
        input("Dataset has ended. Press enter to continue program.")


if __name__ == "__main__":
    from llama2d.datasets.mind2web import Mind2webDataset

    with sync_playwright() as playwright:
        dataset = HuggingFaceDataset("llama2d/llama2d-mind2web", split="train")
        for entry in dataset:
            assert (
                entry["labels"] > 0
            ).any(), f"No labels in entry! {entry['labels'].tolist()}"

        dataset = Mind2webDataset(playwright=playwright, headless=False)

        debug_dataset(dataset)
