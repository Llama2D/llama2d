"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

import os
import tempfile
# from selenium import webdriver
from transformers import LlamaTokenizer
from ..vision.ocr import ImageAnnotator
from ..vision.url_to_image.url_to_image import take_screenshot,extract_domain
from ..constants import MAX_SEQ_LEN, MAX_PAGE_LEN
print("extract_domain",extract_domain)

from glob import glob
from torch.utils.data import Dataset

from tqdm import tqdm

import torch
class Llama2dWebsiteFeatureExtractor(object):

    def __init__(self, model_path, seperator_id=None, label_mask_id=-100, mask_out_body = True): # -100 is default
        self.tokenizer = LlamaTokenizer.from_pretrained(model_path)
        self.__annotator = ImageAnnotator()

        if not seperator_id:
            self.__seperator_id = self.tokenizer.unk_token_id # this should be kept at 0 for most uses, as it is a special token
        else:
            self.__seperator_id = seperator_id

        self.__label_mask_id = label_mask_id
        self.__mask_out_body = mask_out_body

    def __process(self, prompt, page, output):
        # run OCR
        annotations = self.__annotator(page)

        # output tokens
        output_tokens = self.tokenizer.tokenize(output)
        # and use (-1,-1) for the 2d embeddings for the prompt
        output_tokens_locs = [(-1, -1) for _ in range(len(output_tokens))]

        # extract tokens
        image_tokens = [self.tokenizer.tokenize(i.text) for i in annotations.words]
        # and, correspondingly, get their midpoints. If a word is broken up into
        # multiple pieces by the BPE, we return multiple of the word's location
        image_token_locs = [[annot.midpoint_normalized
                            for j in range(len(i))]
                            for i, annot in zip(image_tokens, annotations.words)]

        image_tokens = image_tokens[:MAX_PAGE_LEN]
        image_token_locs = image_token_locs[:MAX_PAGE_LEN]

        # extract tokens from the prompt
        prompt_tokens = self.tokenizer.tokenize(prompt)
        # and use (-1,-1) for the 2d embeddings for the prompt
        prompt_tokens_locs = [(-1, -1) for _ in range(len(prompt_tokens))]

        # and now we stich it together
        input_ids = (
            [self.tokenizer.bos_token_id]+ # bos token
            self.tokenizer.convert_tokens_to_ids(prompt_tokens) +
            [self.__seperator_id] + # seperating prompt with context
            self.tokenizer.convert_tokens_to_ids([j for i in image_tokens for j in i]) + 
            [self.__seperator_id] + # seperating context with answer
            self.tokenizer.convert_tokens_to_ids(output_tokens)
        )

        # mask out the prompt
        label_ids = (
            [self.tokenizer.bos_token_id]+ # bos token
            [-100 for _ in range(len(prompt_tokens))] + # we don not want to predict the prompt
            [-100] + # seperating prompt with context
            [-100 if self.__mask_out_body else k
             for k in self.tokenizer.convert_tokens_to_ids([j for i in image_tokens for j in i])] + 
            [-100] + # seperating context with answer
            self.tokenizer.convert_tokens_to_ids(output_tokens)
        )

        # and we switch together the image locs
        input_coords = (
            [(-1, -1)]+ # bos token
            prompt_tokens_locs +
            [(-1, -1)]+ # for the seperator
            [j for i in image_token_locs for j in i] +
            [(-1, -1)]+ # for the seperator
            output_tokens_locs
        )
        input_coords = torch.tensor(input_coords)
        input_ids = torch.tensor(input_ids)
        label_ids = torch.tensor(label_ids)

        attention_mask = torch.ones_like(input_ids)

        # pad or truncate
        if len(input_ids) > MAX_SEQ_LEN:
            input_ids = input_ids[:MAX_SEQ_LEN]
            label_ids = label_ids[:MAX_SEQ_LEN]
            input_coords = input_coords[:MAX_SEQ_LEN]
            attention_mask = attention_mask[:MAX_SEQ_LEN]
        elif len(input_ids) < MAX_SEQ_LEN:
            # right-pad label_ids with -100, input_coords with (-1,-1), and input_ids with 0
            input_ids = torch.cat([input_ids, torch.zeros(MAX_SEQ_LEN-len(input_ids), dtype=torch.long)])
            label_ids = torch.cat([label_ids, torch.ones(MAX_SEQ_LEN-len(label_ids), dtype=torch.long)*self.__label_mask_id])
            input_coords = torch.cat([input_coords, torch.ones(MAX_SEQ_LEN-len(input_coords), 2)*-1])
            attention_mask = torch.cat([attention_mask, torch.zeros(MAX_SEQ_LEN-len(attention_mask), dtype=torch.long)])

        # return output
        return {
            "input_ids": input_ids,
            "coords": input_coords,
            "labels": label_ids
        }
        

    def create_inference_data(self, page, prompt, uri):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, extract_domain(uri)+".png")
            # html = os.path.join(tmpdir, extract_domain(uri)+".mhtml")

            # driver = webdriver.Chrome()
            # driver.get(uri)

            # # Execute Chrome dev tool command to obtain the mhtml file
            # res = driver.execute_cdp_cmd('Page.captureSnapshot', {})

            take_screenshot(page=page,url=uri, save_path=path)
            return self.__process(prompt, path, "")

    def from_training_data(self, page, html):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, extract_domain(uri)+".png")
            prompt, label = take_screenshot(page=page,url=html, save_path=path)
            return self.__process(prompt, path, label)

# class Llama2dDataset(Dataset):

#     def __init__(self, input_mhtml_dir=None, input_urls=None, tasks=None):
#         """Creates PyTorch Dataset from EITHER a folder of mhtml or input urls

#         THIS OBJECT ASSUMES THAT YOU HAVE THE HF DATASET DOWNLADED

#         Parameters
#         ----------
#         tasks : List[str]
#             A list of prompts for the input task.
#         input_mhtml_dir : List[str]
#             A folder in which lives a bunch of .mhtmls.
#         input_urls : List[str]
#             A list of URLS, used for inference.
#         """

#         print("creating dataset...")

#         if input_mhtml_dir:
#             print("using local .mhtmls assumes that you are training and that the files are named correctly")


#     def __getitem__(self, index):
#         pass

#     def __len__(self):
#         pass 

from playwright.sync_api import sync_playwright
class Llama2dPretrainingDataset(Dataset):

    def __init__(self, model="decapoda-research/llama-7b-hf", urls = [], include_coords=True):
        self.__extractor = Llama2dWebsiteFeatureExtractor(model, mask_out_body=False)
        self.__urls = urls
        
        self.__include_coords = include_coords

        with sync_playwright() as p:
            # Using the Chromium browser but you can also use 'firefox' or 'webkit'
            browser = p.chromium.launch()
            page = browser.new_page()

            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
            })
            self.extractions = [self.__extractor.create_inference_data(page,"", i) for i in self.__urls]

    def __getitem__(self, index):
        ret = self.extractions[index]
        if not self.__include_coords:
            return {k:v for k,v in ret.items() if k != "coords"}
        return ret

    def __len__(self):
        return len(self.__urls)


# driver.quit()

# from selenium import webdriver

# driver = webdriver.Firefox()
# driver.get("http://www.python.org")
# dom_snapshot = driver.execute_script('return document.documentElement.outerHTML;')
# driver.quit()
# # dom_snapshot

# from datasets import load_dataset
# dataset = load_dataset("osunlp/Mind2Web")


# tokenizer("")
# tokenizer.tokenize(tokenizer.bos_token)
# tokenizer.bos_token_id
# tokenizer.eos_token_id

if __name__=="__main__":
    dataset = Llama2dPretrainingDataset(model="decapoda-research/llama-7b-hf",
                                        urls=["https://github.com/OSU-NLP-Group/Mind2Web",
                                            "https://stackoverflow.com/questions/60352003/how-to-download-webpage-as-mhtml"])

    sample = dataset[0]


# extractor = Llama2dWebsiteFeatureExtractor("decapoda-research/llama-7b-hf", mask_out_body=True)
# tmp = extractor.create_inference_data("", "https://arxiv.org/pdf/1706.03762.pdf")

    # oup = extractor("search for silly cats", "https://www.google.com", "click [5]")

    # assert len(oup["input_ids"]) == len(oup["coords"]) 
    # assert len(oup["input_ids"]) == len(oup["labels"]) 
