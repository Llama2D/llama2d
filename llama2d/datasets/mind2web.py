import json
import os
from glob import glob
from typing import Dict, List, Tuple

import torch
from datasets import load_dataset
from playwright.sync_api import sync_playwright
from tqdm import tqdm

from ..constants import MIND2WEB_IN_DIR, MIND2WEB_OUT_DIR
from ..pos_embeds.feature_extraction import Llama2dWebsiteFeatureExtractor
from ..tagging.add_tags_to_page import add_tags_to_webpage
from ..vision.url_to_image import take_screenshot


def get_uid_to_mhtml_map() -> Dict[str, str]:
    all_mhtmls = glob(f"{MIND2WEB_IN_DIR}/task/*/processed/snapshots/*_before.mhtml")

    # extract the uid from *_before.mhtml
    get_uid = lambda path: path.split("/")[-1].split("_")[0]
    return {get_uid(path): path for path in all_mhtmls}


def save_inputs_from_task(
    page,
    task: Dict,
    extractor: Llama2dWebsiteFeatureExtractor,
    uid_to_mhtml: Dict[str, str],
) -> List[Tuple[str, str, str]]:
    intention = task["confirmed_task"]

    for action in task["actions"]:
        uid = action["action_uid"]

        action_dir = f"{MIND2WEB_OUT_DIR}/{uid}"
        os.mkdir(action_dir)

        mhtml_file = uid_to_mhtml[uid]

        pos_candidates = action["pos_candidates"]
        assert (
            len(pos_candidates) == 1
        ), f"Num of positive candidates is {len(pos_candidates)}!"

        page.goto(mhtml_file)
        gt_tag = add_tags_to_webpage(page, action)

        screenshot_path = f"{action_dir}/screenshot.png"

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

        llama_train_input = extractor.__process(prompt, screenshot_path, completion)

        torch.save(llama_train_input, f"{action_dir}/input.pt")

        json_vals = {
            "prompt": prompt,
            "completion": completion,
        }
        with open(f"{action_dir}/input.json", "w") as f:
            json.dump(json_vals, f)


def load_all_tasks():
    print(f"Loading data from {MIND2WEB_IN_DIR}...")
    os.run(f"rm -rf {MIND2WEB_OUT_DIR}/*")

    dataset = load_dataset("osunlp/Mind2Web")
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
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            }
        )

        for task in tqdm(train):
            save_inputs_from_task(page, task, extractor, uid_to_mhtml)

    print(f"Done loading input training data! Data is saved in {MIND2WEB_OUT_DIR}.")


if __name__ == "__main__":
    load_all_tasks()
