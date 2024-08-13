from dataset.BaseDataset import BaseDataset
from dataset.BaseRecord import BaseRecord

from datasets import load_dataset
import os
import re


class GSM8KRecord(BaseRecord):
    """ Record structure for GSM8K dataset. """
    def __init__(self, record_id, record_data):

        REQUIRED_KEYS = ['question', 'answer', 'split']
        assert all(key in record_data for key in REQUIRED_KEYS), "Record data is missing required keys!"

        record_data['dataset'] = 'gsm8k'
        record_data['solution'] = self._split_solution(record_data.pop('answer'))
        record_data['final_answer'] = record_data['solution'][-1].replace("Final answer: ", "")

        super().__init__(record_id, record_data)
        self.socratic_questions = [_.split("**")[0] for _ in record_data["solution"][:-1]]
        self.split = record_data['split']

    @staticmethod
    def _split_solution(solution):
        solution_lines = solution.split("\n")
        steps = [step.split("**")[1] for step in solution_lines[:-1]]
        steps.append(solution_lines[-1].replace("#### ", "Final answer: "))
        return steps

    @property
    def formatted_solution(self):
        solution = ""
        for i, step in enumerate(self.solution[:-1], start=1):
            solution += f"Step {i}:\n"
            solution += f"{step}\n\n"
        solution += self.solution[-1]
        return solution


class GSM8K(BaseDataset):
    """
    Dataset class for GSM8K benchmark. Extends the BaseDataset class to handle the GSM8K dataset.
    """
    def __init__(self, from_file="data/gsm8k.jsonl", from_huggingface=False, file_format="jsonl", **kwargs):
        super().__init__("gsm8k", **kwargs)

        # Check initialization arguments
        assert os.path.exists(from_file) or from_huggingface, "File does not exist!"

        self.file_path = from_file
        self.file_format = file_format
        self.download_dataset = from_huggingface
        self.fields += ["split"]
        self.list_fields += ["socratic_questions"]

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
                record = GSM8KRecord(sample["id"], sample)
                self.records.append(record)
        
    def _download(self):
        """ Download the dataset from huggingface."""
        dataset_name = self.name
        qid = 0
        subset = "socratic"
        splits = ["train", "test"]

        dataset = load_dataset(dataset_name, subset)
        
        for split in splits:
            for sample in dataset[split]:
                sample["split"] = split
                new_record = GSM8KRecord(qid, sample)
                self.records.append(new_record)
                qid += 1

    @staticmethod
    def extract_answer(final_answer_text):
        """
        Extract the final answer from the provided text.
        The answer is just a scalar number!
        """
        if isinstance(final_answer_text, list):
            return [GSM8K.extract_answer(fat) for fat in final_answer_text]

        if 'the answer is' in final_answer_text.lower():
            final_answer_text = final_answer_text.lower().split('the answer is')[1].strip()
        else:
            final_answer_text = final_answer_text.strip().split('\n')[-1].strip()

        final_answer_text = final_answer_text.replace(",", "")
        answer_candidates = re.findall(r'-?\d+\.?\d*', final_answer_text)
        final_answer = float(answer_candidates[0]) if answer_candidates else float('nan')
        return final_answer

    @staticmethod
    def check_answer(predicted_answer, true_answer):
        """
        Check if the provided answer is correct for the given question.

        GSM8K always has an int as final answer. But since the output of the LLM can be float, we convert both values to float.
        """
        try:
            predicted_answer = float(predicted_answer)
            true_answer = float(true_answer)
            return abs(predicted_answer - true_answer) < 1e-5
        except (ValueError, TypeError):  # if type conversion fails, continue with string comparison
            pass

        return true_answer == predicted_answer
