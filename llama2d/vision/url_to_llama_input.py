"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

import os
import tempfile
from glob import glob

import torch
from torch.utils.data import Dataset

from transformers import LlamaTokenizer

from ..constants import MAX_PAGE_LEN, MAX_SEQ_LEN
from .ocr import ImageAnnotator
from .take_screenshot import extract_domain, take_screenshot


class Llama2dWebsiteFeatureExtractor(object):
    def __init__(
        self, model_path, separator_id=None, label_mask_id=-100, mask_out_body=True
    ):  # -100 is default
        self.tokenizer = LlamaTokenizer.from_pretrained(model_path)
        self.__annotator = ImageAnnotator()

        if not separator_id:
            self.__separator_id = (
                self.tokenizer.unk_token_id
            )  # this should be kept at 0 for most uses, as it is a special token
        else:
            self.__separator_id = separator_id

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
        image_token_locs = [
            [annot.midpoint_normalized for j in range(len(i))]
            for i, annot in zip(image_tokens, annotations.words)
        ]

        image_tokens = image_tokens[:MAX_PAGE_LEN]
        image_token_locs = image_token_locs[:MAX_PAGE_LEN]

        # extract tokens from the prompt
        prompt_tokens = self.tokenizer.tokenize(prompt)
        # and use (-1,-1) for the 2d embeddings for the prompt
        prompt_tokens_locs = [(-1, -1) for _ in range(len(prompt_tokens))]

        # and now we stich it together
        input_ids = (
            [self.tokenizer.bos_token_id]
            + self.tokenizer.convert_tokens_to_ids(prompt_tokens)  # bos token
            + [self.__separator_id]
            + self.tokenizer.convert_tokens_to_ids(  # seperating prompt with context
                [j for i in image_tokens for j in i]
            )
            + [self.__separator_id]
            + self.tokenizer.convert_tokens_to_ids(  # seperating context with answer
                output_tokens
            )
        )

        # mask out the prompt
        label_ids = (
            [self.tokenizer.bos_token_id]
            + [-100 for _ in range(len(prompt_tokens))]  # bos token
            + [-100]  # we don not want to predict the prompt
            + [  # seperating prompt with context
                -100 if self.__mask_out_body else k
                for k in self.tokenizer.convert_tokens_to_ids(
                    [j for i in image_tokens for j in i]
                )
            ]
            + [-100]
            + self.tokenizer.convert_tokens_to_ids(  # seperating context with answer
                output_tokens
            )
        )

        # and we switch together the image locs
        input_coords = (
            [(-1, -1)]
            + prompt_tokens_locs  # bos token
            + [(-1, -1)]
            + [j for i in image_token_locs for j in i]  # for the separator
            + [(-1, -1)]
            + output_tokens_locs  # for the separator
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
            input_ids = torch.cat(
                [input_ids, torch.zeros(MAX_SEQ_LEN - len(input_ids), dtype=torch.long)]
            )
            label_ids = torch.cat(
                [
                    label_ids,
                    torch.ones(MAX_SEQ_LEN - len(label_ids), dtype=torch.long)
                    * self.__label_mask_id,
                ]
            )
            input_coords = torch.cat(
                [input_coords, torch.ones(MAX_SEQ_LEN - len(input_coords), 2) * -1]
            ).to(torch.float16)
            attention_mask = torch.cat(
                [
                    attention_mask,
                    torch.zeros(MAX_SEQ_LEN - len(attention_mask), dtype=torch.long),
                ]
            )

        # return output
        return {
            "input_ids": input_ids.to(torch.long),
            "coords": input_coords.to(torch.float16),
            "labels": label_ids.to(torch.long),
            "attention_mask": attention_mask.to(torch.long),
        }

    def create_inference_data(self, page, prompt, uri):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, extract_domain(uri) + ".png")
            # html = os.path.join(tmpdir, extract_domain(uri)+".mhtml")

            # driver = webdriver.Chrome()
            # driver.get(uri)

            # # Execute Chrome dev tool command to obtain the mhtml file
            # res = driver.execute_cdp_cmd('Page.captureSnapshot', {})

            take_screenshot(page=page, url=uri, save_path=path)
            return self.__process(prompt, path, "")

    def from_training_data(self, page, html):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, extract_domain(uri) + ".png")
            prompt, label = take_screenshot(page=page, url=html, save_path=path)
            return self.__process(prompt, path, label)
