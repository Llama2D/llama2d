"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import torch

from llama2d.constants import MAX_TAGS_LEN
from llama2d.tagging.add_tags_to_page import TagAndBox
from llama2d.vision.ocr import ImageAnnotator, Llama2dScreen
from llama2d.vision.take_screenshot import extract_domain, take_screenshot
from transformers import LlamaTokenizer


class Llama2dTokenizer(object):
    def __init__(
        self,
        max_seq_len:int=None,
        model_path: str = "decapoda-research/llama-7b-hf",
        separator_id=None,
        label_mask_id=-100,
        mask_out_body=True,
    ):
        self.tokenizer = LlamaTokenizer.from_pretrained(model_path)

        if not separator_id:
            self.__separator_id = (
                self.tokenizer.unk_token_id
            )  # this should be kept at 0 for most uses, as it is a special token
        else:
            self.__separator_id = separator_id

        self.__label_mask_id = label_mask_id
        self.__mask_out_body = mask_out_body
        self.max_seq_len = max_seq_len

    def process(
        self, prompt: str, screen: Llama2dScreen, output: str
    ) -> Dict[str, torch.Tensor]:
        # output tokens
        output_tokens = self.tokenizer.tokenize(output)
        # and use (-1,-1) for the 2d embeddings for the prompt
        output_tokens_locs = [(-1, -1) for _ in range(len(output_tokens))]

        # extract tokens
        image_tokens = [self.tokenizer.tokenize(i.text) for i in screen.words]
        # and, correspondingly, get their midpoints. If a word is broken up into
        # multiple pieces by the BPE, we return multiple of the word's location
        image_token_locs = [
            [annot.midpoint_normalized for j in range(len(i))]
            for i, annot in zip(image_tokens, screen.words)
        ]

        # filter image token locs 

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

        assert (
            len(input_ids) == len(label_ids) == len(input_coords) == len(attention_mask)
        ), (
            f"len(input_ids) = {len(input_ids)}, len(label_ids) = {len(label_ids)},"
            f" len(input_coords) = {len(input_coords)},"
            f" len(attention_mask) = {len(attention_mask)}"
        )

        # pad or truncate
        if self.max_seq_len is not None:
            if len(input_ids) > self.max_seq_len:
                input_ids = input_ids[:self.max_seq_len]
                label_ids = label_ids[:self.max_seq_len]
                input_coords = input_coords[:self.max_seq_len]
                attention_mask = attention_mask[:self.max_seq_len]
            elif len(input_ids) < self.max_seq_len:
                # right-pad label_ids with -100,
                # input_coords with (-1,-1), and input_ids with 0
                input_ids = torch.cat(
                    [input_ids, torch.zeros(self.max_seq_len - len(input_ids), dtype=torch.long)]
                )
                label_ids = torch.cat(
                    [
                        label_ids,
                        torch.ones(self.max_seq_len - len(label_ids), dtype=torch.long)
                        * self.__label_mask_id,
                    ]
                )
                input_coords = torch.cat(
                    [input_coords, torch.ones(self.max_seq_len - len(input_coords), 2) * -1]
                ).to(torch.float16)
                attention_mask = torch.cat(
                    [
                        attention_mask,
                        torch.zeros(self.max_seq_len - len(attention_mask), dtype=torch.long),
                    ]
                )

        # assert all tensors are the desired length
        assert len(input_ids) == self.max_seq_len, f"len(input_ids) = {len(input_ids)}"
        assert len(label_ids) == self.max_seq_len, f"len(label_ids) = {len(label_ids)}"
        assert (
            len(input_coords) == self.max_seq_len
        ), f"len(input_coords) = {len(input_coords)}"
        assert (
            len(attention_mask) == self.max_seq_len
        ), f"len(attention_mask) = {len(attention_mask)}"

        # return output
        return {
            "input_ids": input_ids.to(torch.long),
            "coords": input_coords.to(torch.float16),
            "labels": label_ids.to(torch.long),
            "attention_mask": attention_mask.to(torch.long),
        }


class Llama2dWebsiteFeatureExtractor(object):
    def __init__(
        self,
        **kwargs,
    ):  # -100 is default
        self.tokenizer = Llama2dTokenizer(**kwargs)
        self.__annotator = ImageAnnotator()

    def process(
        self, prompt, page, output, tags_and_boxes: Optional[List[TagAndBox]] = None
    ):
        # run OCR
        annotations = self.__annotator(page)
        annotations = annotations

        if tags_and_boxes is not None:
            for tag in tags_and_boxes[:MAX_TAGS_LEN]:
                annotations = annotations.concat_word(word=tag.word, xy=tag.coords)

        return self.tokenizer.process(prompt, annotations, output)

    def create_inference_data(self, page, prompt, uri):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / extract_domain(uri) + ".png"
            # html = os.path.join(tmpdir, extract_domain(uri)+".mhtml")

            # driver = webdriver.Chrome()
            # driver.get(uri)

            # # Execute Chrome dev tool command to obtain the mhtml file
            # res = driver.execute_cdp_cmd('Page.captureSnapshot', {})

            take_screenshot(page=page, url=uri, save_path=path)
            return self.__process(prompt, path, "")

    def from_training_data(self, page, html, uri):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / extract_domain(uri) + ".png"
            prompt, label = take_screenshot(page=page, url=html, save_path=path)
            return self.__process(prompt, path, label)
