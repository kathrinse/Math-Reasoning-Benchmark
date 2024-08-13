from dataset.BaseDataset import BaseDataset
from dataset.BaseRecord import BaseRecord

from datasets import load_dataset
import os
import re

class SVAMPRecord(BaseRecord):
    """ Record structure for SVAMP dataset. """ 
    def __init__(self, record_id, record_data):

        self.REQUIRED_KEYS = ['ID','Body','Question','Equation','Answer','Type','split']
        assert all(key in record_data for key in self.REQUIRED_KEYS), "Record data is missing required keys!"

        record_data['dataset'] = 'svamp'
        record_data['question'] = record_data['Body'].strip() + ' ' + record_data['Question'].strip()
        record_data['solution'] = self.extract(record_data['Equation'])
        record_data['final_answer'] = record_data.pop('Answer')

        super().__init__(record_id, record_data)
        self.split = record_data['split']

    @staticmethod
    def extract(Equation):
        pattern = r'\((.*?)\)'
        matches = re.findall(pattern, Equation)
        return matches
    
    @property
    def formatted_solution(self):
        solution = ""
        for i, step in enumerate(self.solution[:-1], start=1):
            solution += f"Step {i}:\n"
            solution += f"{step}\n\n"
        solution += self.solution[-1]
        return solution
    
class SVAMP(BaseDataset):
    """
    Dataset class for SVAMP benchmark. Extends the BaseDataset class to handle the SVAMP dataset.
    """
    def __init__(self, from_file="data/svamp.jsonl", from_huggingface=False, file_format="jsonl"):
        super().__init__("svamp")

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
        if self.file_format == "jsonl":
            self._read_jsonl()
        else:
            raise NotImplementedError("File format not supported!")
        
    def _read_jsonl(self):
        """ Read the dataset from a jsonl file."""
        with open(self.file_path, "r") as f:
            for line in f:
                sample = eval(line)
                record = SVAMPRecord(sample["id"], sample)
                self.records.append(record)

    def _download(self):
        """ Download the dataset from huggingface."""
        dataset_name = 'ChilleD/SVAMP'
        qid = 0
        splits = ["train", "test"]

        dataset = load_dataset(dataset_name)

        for split in splits:
            for sample in dataset[split]:
                sample["split"] = split
                new_record = SVAMPRecord(qid, sample)
                self.records.append(new_record)
                qid += 1 
    
    @staticmethod
    def extract_answer(final_answer_text):
        """
        Extract the final answer from the provided text.
        The answer is just a float number!
        """
        if isinstance(final_answer_text, list):
            return [SVAMP.extract_answer(fat) for fat in final_answer_text]
        
        if isinstance(final_answer_text, float):
            return final_answer_text

        final_answer_text = final_answer_text.strip(' \n')

        if 'the answer is' in final_answer_text.lower():
            final_answer_text = final_answer_text.lower().split('the answer is')[1].strip()
        elif '=' in final_answer_text.lower():
            final_answer_text = final_answer_text.lower().split('=')[1].strip()
        else:
            final_answer_text = final_answer_text.split('\n')[-1].strip()

        final_answer_text = final_answer_text.replace(",", "")
        answer_candidates = re.findall(r'-?\d+\.?\d*', final_answer_text)
        final_answer = float(answer_candidates[0]) if answer_candidates else float('nan')
        return final_answer
    
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
