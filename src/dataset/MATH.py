from dataset.BaseDataset import BaseDataset
from dataset.BaseRecord import BaseRecord

from datasets import load_dataset
import copy
import os


class MATHRecord(BaseRecord):
    """ Record structure for MATH dataset. """
    def __init__(self, record_id, record_data):

        self.REQUIRED_KEYS = ['problem', 'level', 'type', 'solution', 'split']
        assert all(key in record_data for key in self.REQUIRED_KEYS), "Record data is missing required keys!"

        record_data['dataset'] = 'MATH'
        record_data['question'] = record_data.pop('problem')
        dataset_solution_text = record_data['solution']
        record_data['final_answer'] = self.get_final_answer(dataset_solution_text)
        record_data['solution'] = self._split_solution(dataset_solution_text, record_data['final_answer'])

        super().__init__(record_id, record_data)
        self.split = record_data['split']
        self.type = record_data['type']
        self.level = record_data['level']


    @staticmethod
    def _split_solution(solution, final_answer):
        steps = [step + '.' if not step.endswith('.') else step for step in solution.split(". ")]
        steps.append("Final answer: " + final_answer)
        return steps

    @staticmethod
    def get_final_answer(solution):
        # Finds final answer from string using //boxed highlight in LaTeX.
        start = solution.rfind("boxed") + 6
        end = start + 1
        bracket_counter = 0

        # Find the end of //boxed{} area
        while end < len(solution) and (solution[end] != '}' or bracket_counter != 0):
            if solution[end] == '{':
                bracket_counter += 1
            if solution[end] == '}':
                bracket_counter -= 1
            end += 1
            # Fail-safe for misused boxed at the end
        if end == len(solution):
            return "ERROR"
        return solution[start:end]

    @property
    def formatted_solution(self):
        solution = ""
        for i, step in enumerate(self.solution[:-1], start=1):
            solution += f"Step {i}:\n"
            solution += f"{step}\n\n"
        solution += self.solution[-1]
        return solution


class MATH(BaseDataset):
    """
    Dataset class for MATH benchmark. Extends the BaseDataset class to handle the MATH dataset.
    """
    def __init__(self, from_file="data/math.jsonl", from_huggingface=False, file_format="jsonl"):
        super().__init__("math")

        # Check initialization arguments
        assert os.path.exists(from_file) or from_huggingface, "File does not exist!"

        self.file_path = from_file
        self.file_format = file_format
        self.download_dataset = from_huggingface
        self.fields += ["split"]
        self.categories = ['Counting & Probability', 'Prealgebra', 'Number Theory', 'Algebra', 'Intermediate Algebra',
                           'Geometry', 'Precalculus']

        if self.download_dataset:
            self._download()  # load the dataset from huggingface
        else:
            self._read()  # load the dataset from file

        self._pad_list_fields()  # for pytorch compatibility, make list elements equal length

    def _read(self):
        """ Read the dataset from file. """
        if self.file_format == "jsonl":
            self._read_jsonl()
        else:
            raise NotImplementedError("File format not supported!")

    def _read_jsonl(self):
        """ Read the dataset from a jsonl file."""
        with open(self.file_path, "r") as f:
            for line in f:
                sample = eval(line)
                record = MATHRecord(sample["id"], sample)
                self.records.append(record)

    def _download(self):
        """ Download the dataset from huggingface."""
        dataset_name = 'lighteval/MATH'
        qid = 0
        splits = ["train", "test"]

        dataset = load_dataset(dataset_name)

        for split in splits:
            for sample in dataset[split]:
                sample["split"] = split
                new_record = MATHRecord(qid, sample)
                self.records.append(new_record)
                qid += 1

    @staticmethod
    def extract_answer(final_answer_text, **kwargs):
        """
        Extract the final answer from the provided text.
        """
        if isinstance(final_answer_text, list):
            return [MATH.extract_answer(fat) for fat in final_answer_text]
        
        if not final_answer_text:
            return ""

        if '\\boxed' in final_answer_text:
            final_answer = MATHRecord.get_final_answer(final_answer_text)
        else:
            final_answer = final_answer_text
        return final_answer
    
    @staticmethod
    def check_answer(predicted_answer, true_answer, **kwargs):
        """
        Check if the provided answer is correct for the given question.

        MATH returns a string - how to handle best?
        """
        return true_answer == predicted_answer

    def filter(self, category=None, level=None, split=None):
        assert category in self.categories or category is None, "Invalid category!"
        assert level in range(1, 6) or level is None, "Invalid level!"
        assert split in ["train", "test"] or split is None, "Invalid split!"

        new_ds = copy.deepcopy(self)
        new_ds.records = [record for record in self.records if (category is None or record.type == category) and
                          (level is None or record.level == str(level)) and
                          (split is None or record.split == split)]
        return new_ds
