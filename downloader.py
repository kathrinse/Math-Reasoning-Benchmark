from datasets import load_dataset
import logging
import sys

logging.basicConfig(level=logging.INFO)

# Download and prepare datasets

if __name__ == "__main__":
    splits = ["train", "test"]

    dataset_name = sys.argv[1]

    if dataset_name == "gsm8k":
        subset = "socratic"

        dataset = load_dataset(dataset_name, subset)
        logging.info(f"Loaded {dataset_name} dataset with splits {splits}")

    elif dataset_name == "math":
        dataset = load_dataset("lighteval/MATH")
        logging.info(f"Loaded {dataset_name} dataset with splits {splits}")

    elif dataset_name == "svamp":
        dataset = load_dataset("ChilleD/SVAMP")
        logging.info(f"Loaded {dataset_name} dataset with splits {splits}")

    elif dataset_name == "aqua":
        dataset = load_dataset("aqua_rat")
        logging.info(f"Loaded {dataset_name} dataset with splits {splits}")

    elif dataset_name == "multiarith":
        dataset = load_dataset("ChilleD/MultiArith")
        logging.info(f"Loaded {dataset_name} dataset with splits {splits}")

    else:
        logging.error(f"Dataset {dataset_name} not found.")
        sys.exit(1)
    samples = []
    qid = 0

    for split in splits:
        for sample in dataset[split]:
            sample["split"] = split
            sample["id"] = qid
            samples.append(sample)
            qid += 1

    # save file as jsonl
    with open(f"data/{dataset_name}.jsonl", "w") as f:
        for sample in samples:
            f.write(str(sample) + "\n")

    logging.info(f"Saved {len(samples)} samples to data/{dataset_name}.jsonl")
