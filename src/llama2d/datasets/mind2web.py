import json
import os
from glob import glob
from random import random
from time import sleep
from typing import Dict

import torch
from datasets import load_dataset
from playwright.sync_api import sync_playwright
from torch.utils.data import Dataset

from llama2d.constants import MIND2WEB_MHTML_DIR, SCREEN_RESOLUTION
from llama2d.datasets.huggingface import DatasetInfo, publish_pt_dataset
from llama2d.tagging.add_tags_to_page import add_tags_to_webpage
from llama2d.vision.take_screenshot import take_screenshot
from llama2d.vision.url_to_llama_input import Llama2dWebsiteFeatureExtractor
from llama2d.vision.viz_pt_input import debug_dataset

should_debug = False


class Mind2webDataset(Dataset):
    def __init__(
        self, model="decapoda-research/llama-7b-hf", playwright=None, headless=False,show_errors=False
    ):
        assert playwright is not None, "Please pass in playwright"
        self.__extractor = Llama2dWebsiteFeatureExtractor(mask_out_body=True)

        self.uid_to_mhtml = self.get_uid_to_mhtml_map()

        dataset = load_dataset("osunlp/Mind2Web")
        self.dataset = dataset["train"]

        self.actions = [
            (i, j)
            for i in range(len(self.dataset))
            for j in range(len(self.dataset[i]["actions"]))
        ]

        self.browser = playwright.chromium.launch(
            headless=headless, args=["--disable-web-security"]
        )
        self.page = self.browser.new_page()

        width, height = SCREEN_RESOLUTION
        self.page.set_viewport_size({"width": width, "height": height})

        self.page.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
                "Safari/537.36"
            }
        )
        self.page.set_default_navigation_timeout(1000 * 10)
        self.show_errors = show_errors

    def __len__(self):
        return len(self.actions)

    def __getitem__(self, index):
        screenshot_path = None
        try:
            task_idx, action_idx = self.actions[index]
            task = self.dataset[task_idx]
            action = task["actions"][action_idx]

            pos_candidates = action["pos_candidates"]
            if len(pos_candidates) == 0:
                raise Exception("No positive candidates in dataset!")

            uid = action["action_uid"]
            mhtml_file = self.uid_to_mhtml[uid]

            mhtml_file_name = mhtml_file.split("/")[-1]
            mhtml_file = "http://localhost:5002/" + mhtml_file_name
            self.page.goto(mhtml_file)
            sleep(1)

            gt_tag, tags_and_boxes = add_tags_to_webpage(self.page, action)

            rand_num = random()
            screenshot_path = f"screenshot_{rand_num}.png"
            take_screenshot(self.page, None, screenshot_path)

            self.page.evaluate("window.demo()")
            take_screenshot(self.page, None, "screenshot.png")

            intention = task["confirmed_task"]

            actions_str = "\n".join(task["action_reprs"])
            prompt = f"""
    You are a bot using a website. Your goal is: "{intention}"
    {"So far, you have done the following actions: "
     +actions_str if len(actions_str) > 0 else ""}
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

            ret = self.__extractor.process(
                prompt, screenshot_path, completion, tags_and_boxes=tags_and_boxes
            )

            # delete the screenshot
            os.remove(screenshot_path)

            return ret
        except Exception as e:
            # raise e
            if self.show_errors:
                print("Error in dataset:", str(e)[:100] + "...")

            if "ImageAnnotation" in str(e):
                raise e

            if screenshot_path is not None:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            return None

    def get_uid_to_mhtml_map(self) -> Dict[str, str]:
        all_mhtmls = glob(f"{MIND2WEB_MHTML_DIR}/*_before.mhtml")
        print("mhtml count:", len(all_mhtmls))

        # extract the uid from *_before.mhtml
        def get_uid(path):
            return path.split("/")[-1].split("_")[0]

        return {get_uid(path): path for path in all_mhtmls}


mind2web_repo = "llama2d/llama2d-mind2web"

if __name__ == "__main__":
    ds_info = DatasetInfo(
        repo=mind2web_repo,
        desc="Llama2d Mind2Web dataset - SFT dataset for"
        " tag interaction on diverse websites",
    )

    with sync_playwright() as playwright:
        dataset = Mind2webDataset(playwright=playwright, headless=True)

        # debug_dataset(dataset)

        # publish a subset
        num_samples = 2_000

        if num_samples is not None:
            dataset, _ = torch.utils.data.random_split(
                dataset, [num_samples, len(dataset) - num_samples]
            )

        publish_pt_dataset(dataset, ds_info)
