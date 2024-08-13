from dataset.BaseDataset import BaseDataset
from dataset.BaseRecord import BaseRecord

from datasets import load_dataset
import os


class AQUARecord(BaseRecord):
    """ Record structure for AQUA-RAT dataset. """
    def __init__(self, record_id, record_data):

        self.REQUIRED_KEYS = ['question', 'options', 'rationale', 'correct', 'split']
        assert all(key in record_data for key in self.REQUIRED_KEYS), "Record data is missing required keys!"

        self.question_raw = record_data['question']
        self.options = record_data['options']

        record_data['dataset'] = 'aqua'
        record_data['final_answer'] = record_data.pop('correct')
        record_data['question'] = record_data['question']  + '\n'.join(map(str, record_data['options']))
        record_data['solution'] = record_data['rationale'].split('\n')

        super().__init__(record_id, record_data) 
        self.split = record_data['split'] 

    @property
    def formatted_solution(self):
        solution = ""
        for step in self.solution:
            if not step:
                continue
            solution += f"{step}\n"
        return solution.strip('\n')

class AQUA(BaseDataset):
    """
    Dataset class for AQUA-RAT benchmark. Extends the BaseDataset class to handle the AQUA-RAT dataset.
    """
    def __init__(self, from_file="data/aqua.jsonl", from_huggingface=False, file_format="json"):
        super().__init__("aqua")

        # Check initialization arguments
        assert os.path.exists(from_file) or from_huggingface, "File does not exist!"

        self.file_path = from_file
        self.file_format = file_format
        self.download_dataset = from_huggingface
        self.fields += ["split", "options"]

        if self.download_dataset:
            self._download()  # load the dataset from huggingface
        else:
            self._read()  # load the dataset from file

        self._pad_list_fields()  # for pytorch compatibility, make list elements equal length

    def _read(self):
        """ Read the dataset from file. """

        if self.file_format == "json":
            self._read_jsonl()
        else:
            raise NotImplementedError("File format not supported!")
        
    def _read_jsonl(self):
        """ Read the dataset from a json file."""
        with open(self.file_path, "r") as f:
            for line in f:
                sample = eval(line)  # TODO: fix reading with eval, use json or jsonlines instead
                record = AQUARecord(sample["id"], sample)
                self.records.append(record)

    def _download(self):
        """ Download the dataset from huggingface."""
        dataset_name = 'aqua_rat'   
        qid = 0
        splits = ["train", "validation", "test"]

        dataset = load_dataset(dataset_name)

        for split in splits:
            for sample in dataset[split]:
                sample["split"] = split
                new_record = AQUARecord(qid, sample)
                self.records.append(new_record)
                qid += 1

    @staticmethod
    def extract_answer(answer_text, **kwargs):
        """
        Extract the final answer from the provided text.
        """
        if not answer_text:
            print("No answer text given!")
            return ""
        
        if isinstance(answer_text, list):
            return [AQUA.extract_answer(at) for at in answer_text]
       
        # Define valid answer formats can be found in the answer_text
        valid_formats = [' a.', ' b.', ' c.', ' d.', ' e.',  # initial space is to escape sentence endings. like 'Good.'
                         'a)', 'b)', 'c)', 'd)', 'e)',
                         'a:', 'b:', 'c:', 'd:', 'e:',
                         '(a)', '(b)', '(c)', '(d)', '(e)',
                         # 'a ', 'b ', 'c ', 'd ', 'e ',
                         ]

        answer_text = answer_text.strip().strip("()").lower()  # Remove leading/trailing whitespaces and convert to lowercase

        # the answer is explicitly mentioned, standard output format from dataset
        if 'the answer is' in answer_text:

            # Extract the character immediately following 'the answer is'
            try:
                final_answer = answer_text.split('the answer is')[1].strip(' .').strip("()")[0] # Answer is one character
            except IndexError:
                final_answer = None

            # Validate that the final answer is one of the expected options
            if final_answer in ['a', 'b', 'd', 'd', 'e']:
                final_answer = final_answer.upper()
            else:
                final_answer = None

        # Check if answer_text contains any of the valid formats
        elif any([answer_text.find(option) != -1 for option in valid_formats]):
            final_answer = None
            for option in valid_formats:
                if option in answer_text:
                    # Find the location of the option and extract the corresponding character
                    loc = answer_text.find(option)
                    final_answer = answer_text[loc: loc+2].strip(':). ').upper()
                    break

        # Check if answer_text is a single character
        elif answer_text in ['a', 'b', 'c', 'd', 'e']:
            final_answer = answer_text.upper()

        # Check if the answer_text matches any of the provided options in kwargs (full text match)
        elif 'options' in kwargs and ([answer_text in option.strip().lower() for option in kwargs['options']]):
            final_answer = next(filter(lambda x: answer_text in x, kwargs['options'])).upper()

        # Check if answer_text is a single character with point
        elif answer_text in ['a.', 'b.', 'c.', 'd.', 'e.']:
            final_answer = answer_text[0].upper()

        # Check if answer_text starts with a single character with point
        elif any([answer_text.startswith(option) for option in ['a.', 'b.', 'c.', 'd.', 'e.']]):
            final_answer = answer_text[0].upper()

        # Not found
        else:
            final_answer = None

        return final_answer
    
    @staticmethod
    def check_answer(predicted_answer, true_answer, **kwargs):
        """
        Check if the provided answer is correct for the given question.
        """
        return true_answer == predicted_answer
