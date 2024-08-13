from methods.BaseMethod import BaseMethod
import random

from methods.utils import get_8_shot_wei, get_4_shot_wei_aqua


SHOT_TEMPLATE = "Q: {question}\nA: {solution}\n\n"
TASK = "\n\nQ: {question}\nA: "


class CoT(BaseMethod):

    def __init__(self, dataset, strategy='fixed', shots=8, seed=42, **kwargs):
        super().__init__(dataset, **kwargs)
        self.method_name = 'CoT'

        assert strategy in ['fixed', 'first', 'random'], 'Invalid strategy'

        shots = int(shots)

        self.prompt_template = ''

        if strategy == "fixed":
            if self.dataset.name == "aqua":
                self.prompt_template, _, _ = get_4_shot_wei_aqua()
            else:
                self.prompt_template, _, _ = get_8_shot_wei()

        else:
            if strategy == 'first':  # select first n samples as few-shot examples
                selected_shots = dataset[:shots]
            else:  # strategy == 'random', select randomly n samples as few-shot examples
                random.seed(seed)
                selected_shots = random.sample(dataset, shots)

            # Add examples to the prompt template
            for i, record in enumerate(selected_shots):
                solution = '\n'.join(step for step in record['solution'] if step != '')
                self.prompt_template += SHOT_TEMPLATE.format(
                    question=record['question'], solution=solution, answer=record['final_answer']
                )
        

    def _extract_solution(self, generated_text):
        # Cut off if too much was generated!
        generated_text = generated_text.split("\nQ:")[0]

        if self.dataset.name == "math":
            return generated_text

        # First try
        answer_splits = generated_text.split("Final answer:")

        if len(answer_splits) > 1:
            return answer_splits[-1]
        
        # Second try
        answer_splits = generated_text.split("he answer is")
        if len(answer_splits) > 1:
            return answer_splits[-1]

        # Return last line
        return generated_text.split("\n")[-1]
      

    def run(self, record, base_model, **config):
        prompt = self.prompt_template + TASK.format(question=record['question'])
        solutions = base_model.query(prompt, n=int(config["metric"]["n"]))

        # print(solutions[0])

        # Extract correct answer
        true_answer = self.dataset.extract_answer(record['final_answer'])

        # Extract predicted answer
        predicted_answers = [self._extract_solution(s) for s in solutions]
        predicted_answers = self.dataset.extract_answer(predicted_answers)

        return {'solution': solutions, 'predicted_answers': predicted_answers, 'true_answer': true_answer}
  