from dataset.BaseDataset import BaseDataset
from dataset.BaseRecord import BaseRecord

from datasets import load_dataset
import os
import re


class MultiArithRecord(BaseRecord):
    """ Record structure for MultiArith dataset. """
    def __init__(self, record_id, record_data):

        REQUIRED_KEYS = ['question', 'final_ans', 'split']
        assert all(key in record_data for key in REQUIRED_KEYS), "Record data is missing required keys!" 

        record_data['dataset'] = 'multiarith'
        record_data['question'] = record_data['question'] 
        record_data['final_answer'] = record_data['final_ans']    
        record_data['solution'] = [record_data['final_ans']]   # no solution steps, only final answer

        super().__init__(record_id, record_data)
        self.split = record_data['split']

    @property
    def formatted_solution(self):
        solution = ""
        for i, step in enumerate(self.solution[:-1], start=1):
            solution += f"Step {i}:\n"
            solution += f"{step}\n\n"
        solution += self.solution[-1]
        return solution


class MultiArith(BaseDataset):
    """
    Dataset class for MultiArith benchmark. Extends the BaseDataset class to handle the MultiArith dataset.
    """
    def __init__(self, from_file="data/multiarith.jsonl", from_huggingface=False, file_format="json"):
        super().__init__("multiarith")

        # Check initialization arguments
        assert os.path.exists(from_file) or from_huggingface, "File does not exist!"

        self.file_path = from_file
        self.file_format = file_format
        self.download_dataset = from_huggingface
        self.fields += ["split"]

        if self.download_dataset:
            self._download()  # load the dataset from huggingface
        else:
            self._read()  # load the dataset from file

        self._pad_list_fields()  # for pytorch compatibility, make list elements equal length

    def _read(self):
        """ Read the dataset from file. """
        if self.file_format == "json":
            self._read_json()
        else:
            raise NotImplementedError("File format not supported!")

    def _read_json(self):
        """ Read the dataset from a json file."""
        with open(self.file_path, "r") as f:
            for line in f:
                sample = eval(line)
                record = MultiArithRecord(sample["id"], sample)
                self.records.append(record)

    def _download(self):
        """ Download the dataset from huggingface."""
        dataset_name = 'ChilleD/MultiArith'
        qid = 0
        splits = ["train", "test"]

        dataset = load_dataset(dataset_name)

        for split in splits:
            for sample in dataset[split]:
                sample["split"] = split
                new_record = MultiArithRecord(qid, sample)
                self.records.append(new_record)
                qid += 1 

    @staticmethod
    def extract_answer(final_answer_text):
        """
        Extract the final answer from the provided text. For MultiArith, the final answer is an integer.
        """
        if isinstance(final_answer_text, list):
            return [MultiArith.extract_answer(fat) for fat in final_answer_text]

        if isinstance(final_answer_text, float) or isinstance(final_answer_text, int):
            return final_answer_text

        answer = None
        integers_regex = r"[-+]?\d+"

        if final_answer_text.isnumeric():  # if answer is convertible to integer
            answer = int(final_answer_text)

        elif 'answer is' in final_answer_text:  # if answer is in the format "The answer is 123 apples."
            answer = final_answer_text.split('answer is')[-1]
            all_integers = re.findall(integers_regex, answer)
            if all_integers:
                answer = int(all_integers[0])
        else: # backup scenario, extract the first integer from the text
            all_integers = re.findall(integers_regex, final_answer_text)
            if all_integers:
                answer = int(all_integers[0])

        return answer

    @staticmethod
    def check_answer(predicted_answer, true_answer):
        """
        Check if the provided answer is correct for the given question.
        """
        try:
            predicted_answer = float(predicted_answer)
            true_answer = float(true_answer)
            return abs(predicted_answer - true_answer) < 1e-5
        except (ValueError, TypeError):  # if type conversion fails, continue with string comparison
            pass

        return true_answer == predicted_answer
