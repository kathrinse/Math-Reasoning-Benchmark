from collections import Counter

from methods.BaseMethod import BaseMethod
from methods.in_context.PoT.prompts import DATASET_MAPPING
from methods.in_context.PoT.tool import synthesize_program, safe_execute, floatify_ans, simplify_ans, split_svamp_question, split_aqua_question

# TODO: add the constants to the config
TEMPERATURE_GREEDY_DECODING = 0.0
TEMPERATURE_SAMPLING = 0.4
SELF_CONSISTENCY_RUNS = 40  # different value is defined for each dataset in the original code (GSM8K: 40, SVAMP: 30, AQuA: 30)
MAX_TOKENS = 512  # different value is defined for each dataset in the original code (GSM8K: 256, SVAMP: 256, AQuA: 256)


class PoT(BaseMethod):
    def __init__(self, dataset, prompting='cot', greedy=True, runs=SELF_CONSISTENCY_RUNS, **kwargs):
        super().__init__(dataset)
        self.method_name = 'PoT'

        self.prompt_template = self.get_prompt_template(dataset.name, prompting)
        self.greedy = greedy
        self.runs = 1 if self.greedy else runs
        self.prompting = prompting.lower()

        self.temperature = TEMPERATURE_GREEDY_DECODING if self.greedy else TEMPERATURE_SAMPLING

    def get_prompt_template(self, name, prompting):
        key = (name + '_' + prompting).lower()

        # check implementation
        if key not in DATASET_MAPPING:
            raise NotImplementedError(f'Invalid dataset and prompting combination: {key}')
        elif not DATASET_MAPPING[key]:
            raise NotImplementedError(f'Prompting method not implemented for {name} dataset')

        return DATASET_MAPPING[key]
    

    def _extract_program(self, program):

        splits = program.split("```")
        if len(splits) > 2:
            p = splits[1]
            
            if p.startswith("python"):
                p = p.split("python")[1]

            return p

        return program.split("Question")[0]
    
    def _finalize_program(self, program):
        if self.prompting == 'zs':
            program = program + '\nans = solver()'
            if "def solver()" not in program:
                program = "def solver():\n" + program

            program = "import math\nimport numpy as np\n" + program
        return program

    def run(self, record, base_model, **config):

        if not self.greedy:
            # n=self.runs
            raise NotImplementedError(f'Non greedy strategie is not yet implemented!')

        if self.dataset.name == "svamp":
            body, question = split_svamp_question(record['question'])
            prompt = self.prompt_template.format(body=body, question=question)
        elif self.dataset.name == "aqua":
            question, answer_choices = split_aqua_question(record["question"])
            prompt = self.prompt_template.format(question=question, answer_options=answer_choices)
        else:
            prompt = self.prompt_template.format(question=record['question'])

        solutions = base_model.query(prompt, n=int(config["metric"]["n"]), max_tokens=MAX_TOKENS, temperature=self.temperature)

        # Extract predicted answer
        predicted_answers = []
        processed_solutions = []

        for sol in solutions:
            print("\n\n-------------------------------------------------------\n\n")
            # program = synthesize_program(sol, prompt) if self.prompting == 'zs' else sol
            program = self._extract_program(sol)
            program = self._finalize_program(program)
            ans = safe_execute(program)
            print(ans)
            ans = simplify_ans(ans, False)
            print(ans)

            if self.dataset.name == "aqua":
                if ans:
                    # Result to choice
                    prompt = DATASET_MAPPING["prompt_choice"].format(question=question, options=answer_choices, prediction=ans)
                    prediction = base_model.query(prompt, n=1, max_tokens=3, temperature=0)
                    print(prediction)
                    # prediction = self.dataset.extract_answer(prediction)[0]
                    prediction = prediction[0][0]
                else:
                    prediction = ""
            else:
                prediction = floatify_ans(ans)
            predicted_answers.append(prediction)
            processed_solutions.append(program)

        # if not self.greedy and len(predicted_answers) != 0:  # self-consistency decoding
        #     model_answers_count = Counter(predicted_answers)
        #     predicted_answer, count = model_answers_count.most_common(1)[0]
        #     predicted_answers = [predicted_answer]

        # Extract correct answer
        true_answer = self.dataset.extract_answer(record['final_answer'])

        return {'solution': processed_solutions, 'predicted_answers': predicted_answers, 'true_answer': true_answer}

    