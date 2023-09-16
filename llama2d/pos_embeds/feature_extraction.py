"""
feature_extraction.py
Extract features using the tokenizer, including text and image
"""

from transformers import LlamaTokenizer
from ..vision.ocr import ImageAnnotator

tokenizer = LlamaTokenizer.from_pretrained("decapoda-research/llama-7b-hf")
annotator = ImageAnnotator()

prompt = "The example uses the Hugging Face trainer and model"
page = "../../tmp/webpage2.png"

annotations = annotator(page)
# annotations.full_text






# tokenizer.tokenize("The example uses the Hugging Face trainer and model which means that the checkpoint has to be converted from its original format into the dedicated Hugging Face format. The conversion can be achieved by running the convert_llama_weights_to_hf.py script provided with the transformer package. Given that the original checkpoint resides under models/7B we can install all requirements and convert the checkpoint with:")
