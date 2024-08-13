from abc import ABC


class BaseMetric(ABC):
    def __init__(self, dataset, **kwargs):
        self.name = ""
        self.dataset = dataset

    def compute_metric(self, results: list[dict]) -> dict:
        raise NotImplementedError("Not yet implemented for " + self.name)
