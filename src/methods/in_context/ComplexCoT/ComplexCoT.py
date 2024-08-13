from methods.BaseMethod import BaseMethod
from collections import Counter
import os.path as osp
import json


SHOT_TEMPLATE = "Q: {question}\nA: Let's think step by step. {rationale}"
TEMPLATE = "Q: {question}\nA: Let's think step by step. "

# From the original paper (Fu et al., 2022. Complexity-based prompting for multi-step reasoning. ICLR 2023)
# 1. SELECTING COMPLEX SAMPLES AS PROMPTS
# - Our method is to simply choose complex prompts over simple ones.
# - We define complex instances as instances with more reasoning step.
# - 8 samples with 9 reasoning steps
# 2. COMPLEXITY-BASED CONSISTENCY
# - Our method follows the self-consistency practice.
# - We only vote among top K (K ≤ N ) complex (more steps) reasoning chains.
# - In our experiments, we set N to 50, and observe that the optimal K is always smaller than N (typically 30-40).


class ComplexCoT(BaseMethod):

    def __init__(self, dataset, n_runs=5, best_of=3, **kwargs):
        super().__init__(dataset, **kwargs)
        self.method_name = 'ComplexCoT'
        self.runs = int(n_runs)
        self.best_of = int(best_of)

        if 'method' in kwargs and 'demo_file_path' in kwargs['method']:
            self.demo_file_path = kwargs['method']['demo_file_path']
        else:
            self.demo_file_path = "src/methods/in_context/ComplexCoT/demos/"

    def get_few_shots(self):
        demo_file = osp.join(self.demo_file_path, self.dataset.name + ".json")
        with open(demo_file, "r") as f:
            shots = json.load(f)

        shots_str = [SHOT_TEMPLATE.format(question=s["question"], 
                                          rationale=s["rationale"])
                     for s in shots]
        shots_str = "\n\n".join(shots_str)
        return shots_str
    
    def _extract_solution(self, generated_text):
        # First try
        answer_splits = generated_text.split("Final answer:")

        if len(answer_splits) > 1:
            return answer_splits[-1]
        
        # Second try
        answer_splits = generated_text.split("Answer:")
        if len(answer_splits) > 1:
            return answer_splits[-1]
        
        # Third try
        answer_splits = generated_text.split("he answer is")
        if len(answer_splits) > 1:
            return answer_splits[-1]
        
        # Fourth try
        answer_splits = generated_text.split("Answer ")
        if len(answer_splits) > 1:
            return answer_splits[-1]

        # Return last line
        return generated_text.split("\n")[-1]

    def run(self, record, base_model, **config):
        # Step 1: Generate multiple reasoning steps
        samples = self.get_few_shots()
        prompt = samples + "\n\n" + TEMPLATE.format(question=record['question'])


        all_predicted_answers = []
        solution_list = []

        for _ in range(int(config["metric"]["n"])):
            solutions = base_model.query(prompt, n=self.runs)

            # Cut off the generated next questions
            solutions = [s.split("\nQ:")[0] for s in solutions]

            sorted_solutions = sorted(solutions, key=lambda x: len(x.split("\n")), reverse=True)
            best_of_solutions = sorted_solutions[:self.best_of]

            # Step 2: Extract the answer
            predicted_answers = [self._extract_solution(sol) for sol in best_of_solutions]
            predicted_answers = [self.dataset.extract_answer(pred) for pred in predicted_answers]
          
            model_answers_count = Counter(predicted_answers)
            answer, _ = model_answers_count.most_common(1)[0]

            all_predicted_answers.append(answer)
            solution_list.append(best_of_solutions)

        # Extract correct answer
        true_answer = self.dataset.extract_answer(record['final_answer'])  

        return {'solution': solution_list, 'predicted_answers': all_predicted_answers, 'true_answer': true_answer}
