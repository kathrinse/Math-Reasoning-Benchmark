from model.BaseModel import BaseModel

import os
import openai
import backoff
import logging
import dotenv

logging.basicConfig(level=logging.WARNING)

dotenv.load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")

COSTS = {
    "gpt-3.5-turbo-0125": {"input": 0.5, "output": 1.5},
    "gpt-4o-2024-05-13": {"input": 5, "output": 15},
}


class GPTModel(BaseModel):
    def __init__(self, model="gpt-3.5-turbo", temperature=0.7, max_tokens=1000, **kwargs):
        super().__init__(**kwargs)
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.model = model
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)

        if not API_KEY:
            logging.error("OPENAI_API_KEY is not set")

        self.client = openai.OpenAI(api_key=API_KEY)

    @backoff.on_exception(backoff.expo, openai.OpenAIError, max_tries=3)
    def completions_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    def query(self, prompt, n=1, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        return self._send_query(messages, n=n, **kwargs)
    
    def query_batch(self, prompts, **kwargs):
        messages = [[{"role": "user", "content": p}] for p in prompts]
        # TODO: add async calls
        return [self._send_query(m, n=1, **kwargs)[0] for m in messages]

    def _send_query(self, messages, n, **kwargs):
        outputs = []

        max_tokens = self.max_tokens if 'max_tokens' not in kwargs else kwargs.pop('max_tokens')
        temperature = self.temperature if 'temperature' not in kwargs else kwargs.pop('temperature')
        stop = None if 'stop' not in kwargs else kwargs.pop('stop')

        unused_keys = set(kwargs.keys()) - set(["name", 'max_tokens', 'temperature', 'stop'])
        if len(unused_keys) > 0:
            logging.warning("WARNING: the following parameters are ignored by GPT: " + str(unused_keys)) 

        res = self.completions_with_backoff(model=self.model,
                                            messages=messages,
                                            temperature=temperature,
                                            max_tokens=max_tokens,
                                            n=n,
                                            stop=stop)
        
        outputs.extend([choice.message.content for choice in res.choices])

        # log completion tokens
        self.completion_tokens += res.usage.completion_tokens
        self.prompt_tokens += res.usage.prompt_tokens

        return outputs

    def estimated_cost(self) -> dict:
        INPUT_COSTS_PER_M = COSTS[self.model]["input"]
        OUTPUT_COSTS_PER_M = COSTS[self.model]["output"]
        approx_cost = self.completion_tokens * OUTPUT_COSTS_PER_M / 10**6 + self.prompt_tokens * INPUT_COSTS_PER_M / 10**6
        return {"price": approx_cost, "in_tokens": self.prompt_tokens, "out_tokens": self.completion_tokens}
