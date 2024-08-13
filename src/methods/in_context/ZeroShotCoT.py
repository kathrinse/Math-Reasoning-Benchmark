from methods.BaseMethod import BaseMethod
import re


PROMPT_TEMPLATE = 'Q: {question} \nA: '
ANSWER_EXTRACTION_TEMPLATE = '\n{answer}\nTherefore, the answer (arabic number) is '


class ZeroShotCoT(BaseMethod):
    def __init__(self, dataset, zero_shot_trigger='Let\'s think step by step.', **kwargs):
        super().__init__(dataset, **kwargs)
        self.method_name = 'ZeroShotCoT'
        self.prompt_template = PROMPT_TEMPLATE + zero_shot_trigger
        self.answer_extraction_template = self.prompt_template + ANSWER_EXTRACTION_TEMPLATE

    # Cut off if additional questions were generated
    def _extract_solution_path(self, generated_text):
        return generated_text.split("\nQ:")[0]

    def run(self, record, base_model=None, **config):
        question = record['question']

        # Step 1: Get the solution by thinking step by step
        prompt = self.prompt_template.format(question=question)
        solutions = base_model.query(prompt, n=int(config["metric"]["n"]))

        solutions = [self._extract_solution_path(s) for s in solutions]

        # Step 2: Extract the answer
        prompts = [self.answer_extraction_template.format(question=question, answer=s) for s in solutions]
        answers = base_model.query_batch(prompts)

        answers = [self._extract_solution_path(a) for a in answers]

        # Step 3: Extract numeric solution
        predicted_answers = [self.dataset.extract_answer(a) for a in answers]

        # Extract correct answer
        true_answer = self.dataset.extract_answer(record['final_answer'])

        return {'solution': solutions, 'predicted_answers': predicted_answers, 'true_answer': true_answer}