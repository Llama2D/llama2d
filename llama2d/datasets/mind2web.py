from typing import Dict, List, Tuple
import json
import os
import torch
from tqdm import tqdm

from playwright.sync_api import sync_playwright
from datasets import load_dataset

from ..tagging.add_tags_to_page import add_tags_to_webpage
from ..vision.url_to_image import take_screenshot
from ..pos_embeds.feature_extraction import Llama2dWebsiteFeatureExtractor
from ..constants import MIND2WEB_IN_DIR, MIND2WEB_OUT_DIR
from .huggingface import DatasetInfo, publish_pt_dataset

from glob import glob

from torch.utils.data import Dataset
class Mind2webDataset(Dataset):
    def __init__(
            self, model="decapoda-research/llama-7b-hf", split="train"
    ):
        self.__extractor = Llama2dWebsiteFeatureExtractor(model, mask_out_body=False)

        self.dataset = load_dataset("osunlp/Mind2Web")
        self.actions = [(i, j) for i in range(len(self.dataset)) for j in range(len(self.dataset[i]["actions"]))]

        self.playwright = sync_playwright()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

        self.page.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            }
        )

        self.uid_to_mhtml = self.get_uid_to_mhtml_map()
    
    def __len__(self):
        return len(self.actions)
    
    def __getitem__(self, index):

        try:

            task_idx, action_idx = self.actions[index]
            task = self.dataset[task_idx]
            action = task["actions"][action_idx]

            uid = action["action_uid"]
            mhtml_file = self.uid_to_mhtml[uid]
            self.page.goto(mhtml_file)

            gt_tag = add_tags_to_webpage(self.page, action)

            screenshot_path = f"screenshot.png"
            take_screenshot(self.page, None, screenshot_path)

            intention = task["confirmed_task"]

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

            return self.__extractor.__process(prompt, screenshot_path, completion)

        except Exception as e:
            print(f"Exception while processing {index}: {e}")
            return None


    def get_uid_to_mhtml_map(self) -> Dict[str, str]:
        all_mhtmls = glob(f"{MIND2WEB_IN_DIR}/task/*/processed/snapshots/*_before.mhtml")

        # extract the uid from *_before.mhtml
        get_uid = lambda path: path.split("/")[-1].split("_")[0]
        return {get_uid(path): path for path in all_mhtmls}


mind2web_repo = "llama2d/llama2d-mind2web"

if __name__ == "__main__":

    ds_info = DatasetInfo(
        repo=mind2web_repo,
        desc="Llama2d Mind2Web dataset - SFT dataset for tag interaction on real estate websites",
    )

    dataset = Mind2webDataset()
    publish_pt_dataset(dataset, ds_info)
