import json
import os
import subprocess
from typing import Dict, List, Tuple

import torch
from datasets import load_dataset
from playwright.sync_api import sync_playwright
from tqdm import tqdm
from llama2d.vision.take_screenshot import take_screenshot

from llama2d.vision.url_to_llama_input import Llama2dWebsiteFeatureExtractor

from ..constants import MIND2WEB_IN_DIR, MIND2WEB_MHTML_DIR, MIND2WEB_OUT_DIR
from ..tagging.add_tags_to_page import add_tags_to_webpage


def get_uid(path):
    """Extract the uid from a file path."""
    return path.split("/")[-1].split("_")[0]


def get_uid_to_mhtml_map() -> Dict[str, str]:
    """Get a mapping from uid to mhtml file path.

    Returns:
        Dict[str, str]: A mapping from uid to mhtml file path.
    """
    # all files in the MIN2WEB_MHTML_DIR are mhtml files
    all_mhtmls = [
        os.path.join(MIND2WEB_MHTML_DIR, f)
        for f in os.listdir(MIND2WEB_MHTML_DIR)
        if os.path.isfile(os.path.join(MIND2WEB_MHTML_DIR, f))
    ]
    return {get_uid(path): path for path in all_mhtmls}


def save_inputs_from_task(
    page,
    task: Dict,
    extractor: Llama2dWebsiteFeatureExtractor,
    uid_to_mhtml: Dict[str, str],
) -> List[Tuple[str, str, str]]:
    intention = task["confirmed_task"]

    try:
        for action in task["actions"]:
            uid = action["action_uid"]

            action_dir = MIND2WEB_OUT_DIR / uid

            # make the directory if it doesn't exist
            os.makedirs(action_dir, exist_ok=True)

            mhtml_file = uid_to_mhtml[uid]

            pos_candidates = action["pos_candidates"]
            assert (
                len(pos_candidates) == 1
            ), f"Num of positive candidates is {len(pos_candidates)}!"

            mhtml_file = "file://" + mhtml_file

            try:
                page.goto(mhtml_file)
            except Exception as e:
                print(f"Error going to {mhtml_file}!")
                print(e)
                continue
            gt_tag = add_tags_to_webpage(page, action)

            screenshot_path = action_dir / "screenshot.png"

            # we set url=None because we have already gone to the url
            take_screenshot(page, None, screenshot_path)

            prompt = f"""
    You are a real estate agent using a website. Your goal is: "{intention}"
    The website looks like so:"""

            operation = action["operation"]
            op = operation["op"]
            value = operation["value"]

            completion = None
            if op == "CLICK":
                completion = f"CLICK [{gt_tag}]"
            elif op == "TYPE":
                completion = f"TYPE [{gt_tag}] {json.dumps(value)}"
            elif op == "SELECT":
                completion = f"SELECT [{gt_tag}]"
            else:
                raise NotImplementedError(f"Don't understand operation {op}")

            llama_train_input = extractor.process(prompt, screenshot_path, completion)

            torch.save(llama_train_input, action_dir / "input.pt")

            json_vals = {
                "prompt": prompt,
                "completion": completion,
            }
            with open(action_dir / "input.json", "w") as f:
                json.dump(json_vals, f)

    except Exception as e:
        print("Error processing task!")
        print(e)
        return

    print("Successfully processed task!")


def load_all_tasks():
    print(f"Loading data from {MIND2WEB_IN_DIR}...")
    subprocess.run(["rm", "-rf", f"{MIND2WEB_OUT_DIR}/*"])

    dataset = load_dataset("osunlp/Mind2Web")
    print("Done loading data!")
    train = dataset["train"]

    extractor = Llama2dWebsiteFeatureExtractor(
        model_path="decapoda-research/llama-7b-hf"
    )

    uid_to_mhtml = get_uid_to_mhtml_map()

    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
                "Safari/537.36"
            }
        )

        for task in tqdm(train):
            save_inputs_from_task(page, task, extractor, uid_to_mhtml)

    print(f"Done loading input training data! Data is saved in {MIND2WEB_OUT_DIR}.")


if __name__ == "__main__":
    load_all_tasks()
