from methods.BaseMethod import BaseMethod
import os.path as osp
import json

SHOT_TEMPLATE = "Q: {question}\nA: Let's think step by step. {rationale} The answer is {answer}."
TEMPLATE = "Q: {question}\nA: Let's think step by step."


class AutoCoT(BaseMethod):

    def __init__(self, dataset, **method_config):
        super().__init__(dataset, **method_config)
        self.method_name = 'AutoCoT'

        if 'method' in method_config and 'demo_file_path' in method_config['method']:
            self.demo_file_path = method_config['method']['demo_file_path']
        else:
            self.demo_file_path = "src/methods/in_context/AutoCoT/demos/"

    def get_few_shots(self):
        demo_file = osp.join(self.demo_file_path, self.dataset.name + ".json")
        with open(demo_file, "r") as f:
            shots = json.load(f)

        shots_str = [SHOT_TEMPLATE.format(question=s["question"], 
                                         rationale=s["rationale"],
                                         answer=s["answer"])
                     for s in shots]
        shots_str = "\n\n".join(shots_str)
        return shots_str
    
    def extract_solution(self, return_text):
        # Cut off if too much was generated!
        return_text = return_text.split("\nQ:")[0]

        splits = return_text.split("The answer is ")
        if len(splits) > 1:
            return splits[-1]
        
        # If it did not work, check if there is a "final answer"
        splits = return_text.split("Final answer:")
        if len(splits) > 1:
            return splits[-1]
        
        # If it did not work, check if there is a "Answer:"
        splits = return_text.split("Answer:")
        if len(splits) > 1:
            return splits[-1]
                
        # If both did not work, return everything
        return return_text

    def run(self, record, base_model, **config):
        samples = self.get_few_shots()
        prompt = samples + "\n\n" + TEMPLATE.format(question=record['question'])

        solutions = base_model.query(prompt, n=int(config["metric"]["n"]))

        predicted_answers = [self.extract_solution(s) for s in solutions]
        predicted_answers = self.dataset.extract_answer(predicted_answers)

        true_answer = self.dataset.extract_answer(record['final_answer'])  

        return {'solution': solutions, 'predicted_answers': predicted_answers, 'true_answer': true_answer}
    