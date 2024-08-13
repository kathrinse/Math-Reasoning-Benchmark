from model.BaseModel import BaseModel
import logging
logging.basicConfig(level=logging.INFO)

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1,2"

import dotenv

dotenv.load_dotenv()
LLAMA3_MODEL_PATH = os.getenv("LLAMA3_MODEL_PATH", "")

import torch

cuda_available = torch.cuda.is_available()
logging.info(f"Is CUDA available? {cuda_available}")

import ast

import transformers
from datasets import Dataset
from transformers.pipelines.pt_utils import KeyDataset


def load_llama3_8B(device='cuda:0'):
    model_id = LLAMA3_MODEL_PATH + 'Meta-Llama-3-8B'

    pipeline = transformers.pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device=device,
    )

    pipeline.tokenizer.padding_side = "left"
    pipeline.tokenizer.pad_token_id = pipeline.tokenizer.eos_token_id

    return pipeline

def load_llama3_70B():
    model_id = LLAMA3_MODEL_PATH + 'Meta-Llama-3-70B'

    pipeline = transformers.pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto"
    )

    pipeline.tokenizer.padding_side = "left"
    pipeline.tokenizer.pad_token_id = pipeline.tokenizer.eos_token_id

    return pipeline


# LLaMA-3 Model Class

class LLaMA3Model(BaseModel):
    def __init__(self, model="llama-3-8B", temperature=0.7, max_new_tokens=500, topk=50, **model_config):
        super().__init__(**model_config)

        self.gpu_ids = ast.literal_eval(model_config["gpu_ids"]) if "gpu_ids" in model_config.keys() else [0]
        self.device = "cuda:" + str(self.gpu_ids[0]) if cuda_available else "cpu"

        if model in "llama-3-8B":
            self.pipe = load_llama3_8B(self.device)
        elif model in "llama-3-70B":
            self.pipe = load_llama3_70B()
        else:
            logging.error(f"{model} not implemented!")

        logging.info(f"LLaMA model {model} loaded.")

        self.gpu_usage = []
        self.input_tokens = 0
        self.output_tokens = 0

        self.temperature = float(temperature)
        self.max_new_tokens  = int(max_new_tokens)
        self.topk = int(topk)

    # Submit one prompt n times
    def query(self, prompt, n=1, **config):
        max_new_tokens = self.max_new_tokens if 'max_tokens' not in config else config.pop('max_tokens')
        temperature = self.temperature if 'temperature' not in config else config.pop('temperature')
        do_sample = False if temperature == 0.0 else True

        prompt_dataset = Dataset.from_list([{"text": prompt}] * n)

        in_len = len(self.pipe.tokenizer(prompt).input_ids)
        self.input_tokens += in_len

        self.gpu_usage.append(torch.cuda.memory_allocated(self.gpu_ids[0]))

        # Call pipeline
        results = self.pipe(KeyDataset(prompt_dataset, "text"),
                            batch_size=n,
                            min_length=5, 
                            max_new_tokens=max_new_tokens, 
                            do_sample=do_sample,
                            temperature=temperature,
                            top_k=self.topk,
                            return_full_text=False,
                            pad_token_id=self.pipe.tokenizer.eos_token_id)
        
        self.gpu_usage.append(torch.cuda.memory_allocated(self.gpu_ids[0]))

        predictions = [r[0]["generated_text"] for r in results]

        self.output_tokens += len(self.pipe.tokenizer(predictions[0]).input_ids) * len(predictions)

        return predictions

    # Submit multiple prompts at once
    def query_batch(self, prompts: list[str], **config):
        max_new_tokens = self.max_new_tokens if 'max_tokens' not in config else config.pop('max_tokens')
        temperature = self.temperature if 'temperature' not in config else config.pop('temperature')
        do_sample = False if temperature == 0.0 else True

        prompt_dataset = Dataset.from_list([{"text": p} for p in prompts])

        in_len = len(self.pipe.tokenizer(prompts[0]).input_ids) * len(prompts)
        self.input_tokens += in_len

        self.gpu_usage.append(torch.cuda.memory_allocated(self.gpu_ids[0]))

        # Call pipeline
        results = self.pipe(KeyDataset(prompt_dataset, "text"),
                            batch_size=len(prompts),
                            min_length=5, 
                            max_new_tokens=max_new_tokens, 
                            do_sample=do_sample,
                            temperature=temperature,
                            top_k=self.topk,
                            return_full_text=False,
                            pad_token_id=self.pipe.tokenizer.eos_token_id,
                            )
        
        self.gpu_usage.append(torch.cuda.memory_allocated(self.gpu_ids[0]))

        predictions = [r[0]["generated_text"] for r in results]

        self.output_tokens += len(self.pipe.tokenizer(predictions[0]).input_ids) * len(predictions)

        return predictions
    
    
    def estimated_cost(self) -> dict:
        return {"price": self.gpu_usage, "in_tokens": self.input_tokens, "out_tokens": self.output_tokens}
    