from abc import ABC, abstractmethod


class BaseMethod(ABC):
    """ Base method interface. """
    def __init__(self, dataset, **kwargs):
        self.method_name = ""
        self.dataset = dataset

    # Should return a dict with:
    #   - solutions: All solution paths
    #   - predicted answers: n predicted answers
    #   - true answer: the correct answer
    @abstractmethod
    def run(self, record, base_model=None, **config) -> dict:
        pass
