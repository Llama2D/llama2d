from ..constants import SCREEN_RESOLUTION

import torch
from typing import Any, Optional, Tuple
import torch.nn as nn
from transformers import LlamaForCausalLM, LlamaTokenizer

# i.e. model_id = "./models_hf/7B"
class TokenEmbedderWithCoords(nn.Module):
    def __init__(self,model_id:str):
        super().__init__()
        self.model_name = model_id
        self.tokenizer = LlamaTokenizer.from_pretrained(model_id)
    
    def 