"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

import os
import tempfile
from transformers import LlamaTokenizer
from ..vision.ocr import ImageAnnotator
from ..vision.url_to_image.url_to_image import take_screenshot

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
            self.tokenizer.convert_tokens_to_ids(output_tokens) + 
            [self.tokenizer.eos_token_id] # eos token
        )

        # mask out the prompt
        label_ids = (
            [self.tokenizer.bos_token_id]+ # bos token
            [-100 for _ in range(len(prompt_tokens))] + # we don not want to predict the prompt
            [-100] + # seperating prompt with context
            [-100 if self.__mask_out_body else k
             for k in self.tokenizer.convert_tokens_to_ids([j for i in image_tokens for j in i])] + 
            [-100] + # seperating context with answer
            self.tokenizer.convert_tokens_to_ids(output_tokens) + 
            [self.tokenizer.eos_token_id] # eos token
        )

        # and we switch together the image locs
        input_coords = (
            [(-1, -1)]+ # bos token
            prompt_tokens_locs +
            [(-1, -1)]+ # for the seperator
            [j for i in image_token_locs for j in i] +
            [(-1, -1)]+ # for the seperator
            output_tokens_locs + 
            [(-1, -1)] # eos token
        )
        # return output
        return {
            "input_ids": input_ids,
            "coords": input_coords,
            "labels": label_ids
        }

    def __call__(self, prompt, uri, output):

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, extract_domain(uri)+".png")
            take_screenshot(url=uri, save_path=path)
            return self.__process(prompt, path, output)

        # prompt = "The example uses the Hugging Face trainer and model"
        # page = "../../tmp/webpage2.png"


# tokenizer("")
# tokenizer.tokenize(tokenizer.bos_token)
# tokenizer.bos_token_id
# tokenizer.eos_token_id

if __name__=="__main__":
    extractor = Llama2dWebsiteFeatureExtractor("decapoda-research/llama-7b-hf", mask_out_body=False)
    oup = extractor("search for silly cats", "https://www.google.com", "click [5]")

    assert len(oup["input_ids"]) == len(oup["coords"]) 
    assert len(oup["input_ids"]) == len(oup["labels"]) 
