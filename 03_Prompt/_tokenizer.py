from transformers import AutoTokenizer
import yaml
import gc
import torch
from _config import CONFIG
config = CONFIG()

class TOKENIZER:
    def __init__(self):
        if config.debug:
            print('Loading LLM model tokenizer ...')
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_dir)

    