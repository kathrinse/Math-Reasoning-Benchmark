from methods.BaseMethod import BaseMethod

from methods.utils import get_8_shot_gao_dense, execute_code, get_4_shot_gao_aqua
import re


## temperature: float =0.0, top_p: float =1.0,  max_tokens: int =512,

## Add majority voting?


class PAL(BaseMethod):

    def __init__(self, dataset, **kwargs):
        super().__init__(dataset, **kwargs)
        self.method_name = 'PAL'

    def extract_multiple_choice(self, question, answer):
        # Regular expression to find the pattern "Letter)Number"
        pattern = re.compile(r'([A-E])\)(\d+(\.\d+)?)')

        # Find all matches in the text
        matches = pattern.findall(question)
        conversion_dict = {float(number): letter for letter, number, _ in matches}

        try:
            choice = conversion_dict.get(float(answer))
            if choice is None: return ""
            return choice
        except ValueError:
            return ""
    
    # Splits the question in question and answer options
    def split_aqua_question(self, question: str):
        splits = question.split("A)")

        if len(splits) != 2:
            print("*** WARNING: Question could not be split correctly ***")
            return "", question
    
        answers = "A)" + splits[1]
        answers = answers.split("\n")

        answers = "\n".join(answers)

        return splits[0], answers

    def run(self, record, base_model, **config):
        # Step 1: Load few-shots
        if self.dataset.name == "aqua":
            examples, template, _ = get_4_shot_gao_aqua()
            question, options = self.split_aqua_question(record['question'])
            prompt = examples + template.format(question=question, answer_choices=options)
        else:
            examples, template, _ = get_8_shot_gao_dense()
            prompt = examples + template.format(question=record['question'])

        # Step 2: Run LLM
        solutions = base_model.query(prompt, n=int(config["metric"]["n"]))

        # Step 3: Extract code
        # code_snippets = [s.split(answer_key)[-1] for s in solutions]

        # Step 4: Execute code
        results = []
        for code in solutions:
            first_code_part = code.split("#Q")[0]
            first_code_part = first_code_part.split("\nQuestion:")[0]
            first_code_part = first_code_part.strip("</s>")

            if self.dataset.name == "aqua": first_code_part += "\n\nprint(solution())"
            # print("-------------------")
            # print(first_code_part[0])
            # print("-------------------")
            try:
                exec_result = execute_code(first_code_part)
                print("*** Ran suceessfully")
            except TimeoutError as e:
                print("Timeout!")
                results.append("")
                continue

            if self.dataset.name == "aqua":
                choice = self.extract_multiple_choice(options, exec_result["result"])
                results.append(choice)
            else:
                results.append(exec_result["result"])

        

        # Step 5: Extract answer
        predicted_answers = self.dataset.extract_answer(results)

        # Extract correct answer
        true_answer = self.dataset.extract_answer(record['final_answer'])


        # counter = Counter(results)
        # return counter.most_common(1)[0][0]

        return {'solution': solutions, 'predicted_answers': predicted_answers, 'true_answer': true_answer}

