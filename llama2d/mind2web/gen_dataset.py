from ..tagging.tagify import tagify_webpage
from ..vision.url_to_image import take_screenshot
from ..pos_embeds.feature_extraction import Llama2dWebsiteFeatureExtractor

from playwright.sync_api import sync_playwright

import os

curr_dir = os.path.dirname(os.path.realpath(__file__))
mind2web_in_dir = f"{curr_dir}/../../mind2web-data"
mind2web_out_dir = f"{curr_dir}/../../mind2web-output"

from typing import Dict,List,Tuple
import json
import os
import torch
def save_inputs_from_task(page,task:Dict,extractor:Llama2dWebsiteFeatureExtractor)->List[Tuple[str,str,str]]:
    
    intention = task["confirmed_task"]

    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        })


        os.run(f"rm -rf {mind2web_out_dir}/*")

        for action in task["actions"]:
            uid = action["action_uid"]

            action_dir = f"{mind2web_out_dir}/{uid}"
            os.mkdir(action_dir)

            mhtml_file = f"{mind2web_in_dir}/task/{uid}/page.mhtml"

            pos_candidates = action["pos_candidates"]
            assert len(pos_candidates) == 1,f"Num of positive candidates is {len(pos_candidates)}!"

            cand = pos_candidates[0]

            page.goto(mhtml_file)
            gt_tag = tagify_webpage(page,action)

            screenshot_path = f"{action_dir}/screenshot.png"

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

from datasets import load_dataset

from tqdm import tqdm
def load_all_tasks():

    print(f"Loading data from {mind2web_in_dir}...")

    dataset = load_dataset("osunlp/Mind2Web")
    train = dataset["train"]

    extractor = Llama2dWebsiteFeatureExtractor(model_path="decapoda-research/llama-7b-hf")

    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        for task in tqdm(train):
            save_inputs_from_task(page,task,extractor)
    
    print(f"Done loading input training data! Data is saved in {mind2web_out_dir}.")


if __name__=="__main__":
    load_all_tasks()