"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

from transformers import LlamaTokenizer
from ..vision.ocr import ImageAnnotator

class Llama2dWebsiteFeatureExtractor(object):

    def __init__(self, model_path): 
        self.tokenizer = LlamaTokenizer.from_pretrained(model_path)
        self.__annotator = ImageAnnotator()

        self.__seperator_id = self.tokenizer.unk_token_id # this should be kept at 0 for most uses, as it is a special token

    def __process(self, prompt, page):
        # run OCR
        annotations = self.__annotator(page)

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
        input_ids = (self.tokenizer.convert_tokens_to_ids(prompt_tokens) +
                    [self.__seperator_id] + # seperating prompt with context
                    self.tokenizer.convert_tokens_to_ids([j for i in image_tokens for j in i]))
        # and we switch together the image locs
        input_coords = (prompt_tokens_locs +
                        [(-1, -1)]+ # for the seperator
                        [j for i in image_token_locs for j in i])

        # return output
        return {
            "input_ids": input_ids,
            "coords": input_coords
        }

    def __call__(self, prompt, uri):
        prompt = "The example uses the Hugging Face trainer and model"
        page = "../../tmp/webpage2.png"


# extractor = Llama2dWebsiteFeatureExtractor("decapoda-research/llama-7b-hf")
# extractor("search for silly cats", "https://www.google.com")

