from abc import ABC


class BaseModel(ABC):
    def __init__(self, **kwargs):
        pass

    def query(self, prompt: str, **kwargs):
        pass

    def query_batch(self, prompts: list[str], **kwargs):
        pass

    def estimated_cost(self) -> dict:
        pass
