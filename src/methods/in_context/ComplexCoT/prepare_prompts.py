import json
from collections import Counter

from dataset import get_dataset

seed = 42
demo_save_dir = "src/methods/in_context/ComplexCoT/demos"
dataset_name = "multiarith"
demo_save_path = demo_save_dir + "/" + dataset_name + ".json"

dataset_class = get_dataset(dataset_name)
dataset = dataset_class(from_file=f'data/{dataset_name}.jsonl')


dataset_train = []
questions = []
rationales = []
answers = []

for d in dataset:
    if d.split == "train":
        dataset_train.append(d)
        questions.append(d.question)
        rationales.append(d.solution)
        answers.append(d.final_answer)

print(dataset_train[0])

# Criteria to filter complex reasoning steps
NUM_SAMPLES = 8
LEN_REASONING_STEPS = 44

# The combine all steps with an index to find them corresponding question later
# tmp = list(map(list, zip(range(len(rationales)), rationales)))
tmp = list(map(list, zip(range(len(questions)), questions)))
# Here, we filter for all rationale that have exactly LEN_REASONING_STEPS steps
# complex_rationales = list(filter(lambda x: len(list(filter(lambda x: x != "", x[1]))) == LEN_REASONING_STEPS, tmp))
# complex_rationales = list(filter(lambda x: len(x[1][0].split(" ")) == LEN_REASONING_STEPS, tmp))
complex_questions = list(filter(lambda x: len(x[1].split(" ")) >= LEN_REASONING_STEPS, tmp))

selected_shots = complex_questions[:NUM_SAMPLES]
selected_idx = [s[0] for s in selected_shots]

demos = []

for idx in selected_idx:
    tmp_question = questions[idx]
    tmp_rationale = "\n".join(list(filter(lambda x: x != "", rationales[idx])))
    tmp_answers = answers[idx]

    demo_element = {
        "question": tmp_question,
        "rationale": tmp_rationale,
        "answer": tmp_answers,
    }

    demos.append(demo_element)


with open(demo_save_path, 'w', encoding="utf-8") as write_f:
    json.dump(demos, write_f, indent=4, ensure_ascii=False)






