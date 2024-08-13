from abc import ABC, abstractmethod
from torch.utils.data import Dataset


class BaseDataset(ABC, Dataset):
    """
    Base abstract class for custom mathematical reasoning benchmarking datasets.

    Attributes:
        name (str): Name of the dataset.
        records (list): List of records in the dataset.
        fields (list): List of required fields for each record.
        list_fields (list): List of fields that need to be padded for PyTorch compatibility.
    """
    @abstractmethod
    def __init__(self, name, **kwargs):
        self.name = name
        self.records = list()
        self.fields = ['id', 'question', 'solution', 'final_answer']  # Required fields
        self.list_fields = ['solution']  # These fields need to be padded for pytorch compatibility

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self.records[i].__dict__ for i in range(*idx.indices(len(self.records)))]
        return self.records[idx].__dict__

    def __iter__(self):
        return iter(self.records)

    @abstractmethod
    def _read(self):
        """
        Abstract method to read the dataset from file.
        """
        pass

    @abstractmethod
    def _download(self):
        """
        Abstract method to download the dataset.
        """
        pass

    @staticmethod
    @abstractmethod
    def extract_answer(answer_text, **kwargs):
        """
        Abstract method to extract answers from the dataset. Overwritten in the child classes to specifically match the
        output format of the dataset.

        Args:
            **kwargs: Additional keyword arguments for extraction.
        """
        pass

    @staticmethod
    @abstractmethod
    def check_answer(predicted_answer, true_answer, **kwargs) -> bool:
        """
        Abstract method to check the correctness of answers for a dataset.

        Args:
            predicted_answer: Predicted answer to evaluate
            true_answer: Correct answer
            **kwargs: Additional keyword arguments for checking answers.

        Returns:
            bool: True if the predicted and correct answer are the same, False otherwise.
        """
        pass

    def get_splits(self, splits) -> list:
        """
        Get the dataset splits.

        Args:
            splits (list): List of dataset splits to return.

        Returns:
            list: List of records for the requested splits.
        """
        return [record.__dict__ for record in self.records if record.split in splits]

    def _pad_list_fields(self):
        """
        Pad all iterable elements in the records to match the maximum length found among them. Required for pytorch
        compatibility.
        """
        for field in self.list_fields:
            max_len = max([len(getattr(record, field)) for record in self.records])  # maximum length across all records
            for record in self.records:
                record_length = len(getattr(record, field))
                if record_length < max_len:
                    padding = [""] * (max_len - record_length)
                    setattr(record, field, getattr(record, field) + padding)  # update the record with the padded field
