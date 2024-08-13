from methods.in_context.CoT import CoT, TASK
from collections import Counter


# From the original paper: 
# In particular, for [...] LaMDA-137B we applied temperature sampling with T = 0.5 and truncated at the 
# top-k (k = 40) tokens with the highest probability, [...] and for GPT-3 we use T = 0.7 without top-k truncation


class SelfConsistencyCoT(CoT):
    def __init__(self, dataset, strategy='fixed', shots=8, seed=42, **method_config):
        super().__init__(dataset, strategy, shots, seed, **method_config)
        self.method_name = 'SelfConsistencyCoT'
        self.runs = int(method_config["n_runs"]) if "n_runs" in method_config.keys() else 10

    def run(self, record, base_model, **config):
        # Step 1: Get the solution by thinking step by step
        prompt = self.prompt_template + TASK.format(question=record['question'])

        predicted_answers = []
        solution_list = []

        for _ in range(int(config["metric"]["n"])):
            solutions = base_model.query(prompt, n=self.runs)

            # Step 2: Extract the answer
            preds = self.dataset.extract_answer(solutions)

            # Step 3: Get the most common answer
            try:
                predicted_answer, _ = Counter(filter(None, preds)).most_common(1)[0]
            except IndexError:
                predicted_answer = None

            predicted_answers.append(predicted_answer)
            solution_list.append(solutions)

        # Extract correct answer
        true_answer = record['final_answer']

        return {'solution': solution_list, 'predicted_answers': predicted_answers, 'true_answer': true_answer}
    