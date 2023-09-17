from typing import Dict,List,Tuple
import json
import os
import torch
from tqdm import tqdm

from playwright.sync_api import sync_playwright
from datasets import load_dataset

from ..tagging.tagify import tagify_webpage
from ..vision.url_to_image import take_screenshot
from ..pos_embeds.feature_extraction import Llama2dWebsiteFeatureExtractor
from ..constants import MIND2WEB_IN_DIR,MIND2WEB_OUT_DIR

def save_inputs_from_task(page,task:Dict,extractor:Llama2dWebsiteFeatureExtractor)->List[Tuple[str,str,str]]:
    
    intention = task["confirmed_task"]

    for action in task["actions"]:
        uid = action["action_uid"]

        action_dir = f"{MIND2WEB_OUT_DIR}/{uid}"
        os.mkdir(action_dir)

        mhtml_file = f"{MIND2WEB_IN_DIR}/task/{uid}/page.mhtml"

        pos_candidates = action["pos_candidates"]
        assert len(pos_candidates) == 1,f"Num of positive candidates is {len(pos_candidates)}!"

        page.goto(mhtml_file)
        gt_tag = tagify_webpage(page,action)

        screenshot_path = f"{action_dir}/screenshot.png"

        # we set url=None because we have already gone to the url
        take_screenshot(page,None,screenshot_path)

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
        
        llama_train_input = extractor.__process(prompt,screenshot_path,completion)

        torch.save(llama_train_input,f"{action_dir}/input.pt")
        
        json_vals = {
            "prompt":prompt,
            "completion":completion,

        }
        with open(f"{action_dir}/input.json","w") as f:
            json.dump(json_vals,f)

def load_all_tasks():

    print(f"Loading data from {MIND2WEB_IN_DIR}...")
    os.run(f"rm -rf {MIND2WEB_OUT_DIR}/*")

    dataset = load_dataset("osunlp/Mind2Web")
    train = dataset["train"]

    extractor = Llama2dWebsiteFeatureExtractor(model_path="decapoda-research/llama-7b-hf")

    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        })

        for task in tqdm(train):
            save_inputs_from_task(page,task,extractor)
    
    print(f"Done loading input training data! Data is saved in {MIND2WEB_OUT_DIR}.")


if __name__=="__main__":
    load_all_tasks()