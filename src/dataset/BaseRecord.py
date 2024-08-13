from abc import ABC, abstractmethod


class BaseRecord(ABC):
    """
    Abstract base class representing a record in a dataset.

    Attributes:
        id (str): Identifier for the record.
        dataset_name (str): Name of the dataset the record belongs to.
        question (str): Question associated with the record.
        solution (str): Solution associated with the record.
        final_answer (str): Final answer associated with the record.
    """
    def __init__(self, record_id, record_data):
        self.id = record_id
        self.dataset_name = record_data['dataset']
        self.question = record_data['question']
        self.solution = record_data['solution']  # TODO: naming is misleading, it is a list of solution steps
        self.final_answer = record_data['final_answer']

    def __repr__(self):
        return f"""{self.dataset_name} | Record: {self.id} \t Question: {self.question}"""

    def __copy__(self):
        return self.__class__(self.id, self.__dict__.copy())

    def __str__(self):
        return str(self.__dict__)

    @property
    @abstractmethod
    def formatted_solution(self):
        """
        Abstract property representing the formatted solution for the record.

        Subclasses must implement this property and return the solution in the common format.
        """
        pass
