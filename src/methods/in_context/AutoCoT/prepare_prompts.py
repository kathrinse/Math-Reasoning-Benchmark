from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import json

from dataset import get_dataset

# Code adapted from: https://github.com/amazon-science/auto-cot/blob/main/run_demo.py

seed = 42
demo_save_dir = "src/methods/in_context/AutoCoT/demos"
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


if dataset_name == "aqua":
    num_clusters = 4
else:
    num_clusters = 8

encoder = SentenceTransformer("all-MiniLM-L6-v2")
print(encoder)

corpus_embeddings = encoder.encode(questions)

print(corpus_embeddings)

# Perform kmean clustering
clustering_model = KMeans(n_clusters=num_clusters, random_state=seed)
clustering_model.fit(corpus_embeddings)
cluster_assignment = clustering_model.labels_

print(cluster_assignment)

# Get for each embedding the distance to all cluster centers
dist = clustering_model.transform(corpus_embeddings)


clustered_sentences = [[] for i in range(num_clusters)]
clustered_dists = [[] for i in range(num_clusters)]
clustered_idx = [[] for i in range(num_clusters)]

# For each cluster collect the corresponding sentences, the distance to the center and the sentence id
for sentence_id, cluster_id in enumerate(cluster_assignment):
    clustered_sentences[cluster_id].append(questions[sentence_id])
    clustered_dists[cluster_id].append(dist[sentence_id][cluster_id])
    clustered_idx[cluster_id].append(sentence_id)


# Criteria to filter the best representative of the cluster
MAX_QUESTION_LENGTH = 60
MAX_RATIONALE_LENGTH = 5

demos = []

# Iterate through all clusters to find the best reprentative for the cluster
for c_idx in range(num_clusters):
    print("Cluster ", c_idx+1)

    # Numerate all distances from the center of the cluster
    tmp = list(map(list, zip(range(len(clustered_dists[c_idx])), clustered_dists[c_idx])))
    # Sort the distances
    top_min_dist = sorted(tmp, key=lambda x: x[1], reverse=False)

    # Find the clostest sample that passes the constaints
    for element in top_min_dist:
        # Get the index of the current element
        min_idx = element[0]

        # Get the corresponing question, rational and answer
        tmp_question = questions[clustered_idx[c_idx][min_idx]].strip()
        tmp_rationale = list(filter(lambda x: x != "", rationales[clustered_idx[c_idx][min_idx]])) # this is a list!
        tmp_answers = answers[clustered_idx[c_idx][min_idx]] # .strip()

        # Check for the constraints    
        if len(tmp_question.split()) > MAX_QUESTION_LENGTH or len(tmp_rationale) > MAX_RATIONALE_LENGTH:
            continue

        # Verify that answer is part of the rationale and not already told in the first step
        if dataset_name in ["gsm8k", "multiarith", "singleeq", "addsub"]:
            if not tmp_answers in tmp_rationale[-1] or tmp_answers in tmp_rationale[0]:
                continue

        # Kick out too complicated examples in math
        if dataset_name in ["math"]:
            if len(" ".join(tmp_rationale).split("\n")) > 5:
                continue

        tmp_rationale = " ".join(tmp_rationale)
        
        demo_element = {
            "question": tmp_question,
            "rationale": tmp_rationale,
            "answer": tmp_answers,
        }

        demos.append(demo_element)
        break
        

with open(demo_save_path, 'w', encoding="utf-8") as write_f:
    json.dump(demos, write_f, indent=4, ensure_ascii=False)






