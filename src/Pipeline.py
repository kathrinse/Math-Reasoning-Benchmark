from dataset import get_dataset
from model import get_model
from metrics import get_metric
from methods import get_method

from config_parser import load_config

import os

from tqdm import tqdm
from datetime import datetime
import time
import json
import pandas as pd


class Pipeline:
    def __init__(self, dataset_name: str, model_name: str, method_name: str, metric_name: str, **config):
        self.config = {**config}
        # Todo: validate config / add default values

        self.dataset_config = self.config["dataset"] if "dataset" in self.config.keys() else {}
        self.method_config = self.config["method"] if "method" in self.config.keys() else {}
        self.metric_config = self.config["metric"] if "metric" in self.config.keys() else {}
        self.model_config = self.config["model"] if "model" in self.config.keys() else {}

        self.dataset = self.__load_dataset(dataset_name, **self.dataset_config)
        self.method = get_method(method_name, dataset=self.dataset, **self.method_config)
        self.metric = get_metric(metric_name, dataset=self.dataset, **self.metric_config)
        self.model = get_model(model_name, **self.model_config) if model_name else ""

    def update_config(self, new_values: dict):

        for k, v in new_values.items():
            if k == "dataset":
                self.dataset_config.update(v)
                self.dataset = self.__load_dataset(self.dataset_config["name"], **self.dataset_config)
            elif k == "method":
                self.method_config.update(v)
                self.method = get_method(self.method_config["name"], dataset=self.dataset, **self.method_config)
            elif k == "metric":
                self.metric_config.update(v)
                self.metric = get_metric(self.metric_config["name"], dataset=self.dataset, **self.metric_config)
            elif k == "model":
                self.model_config.update(v)
                self.model = get_model(self.model_config["name"], **self.model_config)
        

    @classmethod
    def load_pipeline_from_config_file(cls, config_file: str) -> "Pipeline":
        config = load_config(config_file)

        dataset_name = config.get("dataset", "name")
        method_name = config.get("method", "name")
        metric_name = config.get("metric", "name")
        model_name = config.get("model", "name")

        return cls(dataset_name, model_name, method_name, metric_name, **config._to_dict())


    @staticmethod
    def __load_dataset(dataset_name: str, **dataset_args):
        dataset_class = get_dataset(dataset_name, **dataset_args)
        if os.path.exists(f'data/{dataset_name}.jsonl'):
            return dataset_class(from_file=f'data/{dataset_name}.jsonl')
        else:
            return dataset_class(from_huggingface=True)
    
    def save_experiment(self, predictions: list[dict], metrics: dict):
        try:
            exp_name = self.config["general"]["exp_name"] 
        except KeyError:
            exp_name = "exp_" + datetime.now().strftime("%m.%d-%H:%M")
        print(f"Saving experiment {exp_name}...")

        save_path = f"experiments/{exp_name}/"

        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        else:
            print("\n\n***** WARNING: Experiment does already existing! Overwriting old results... ******")

        # 1. Save configuration of the run
        with open(save_path + "config.json", "w") as f:
            json.dump(self.config, f, indent=4, sort_keys=True, default=str)

        # 2. Save performance data
        if metrics:
            with open(save_path + "metrics.json", "w") as f:
                json.dump(metrics, f, indent=4, sort_keys=True, default=str)

        # 3. Save raw result data
        pd.DataFrame(predictions).to_csv(save_path + "results.csv", sep=";")


    # Execute the Pipeline, run Method based on Model for Dataset, evaluate on Metric
    def run(self, indices:list = None):
        print("Running pipeline with the following configuration")
        print(self.config)

        # If no indices are given, test on the whole dataset
        records = [self.dataset[i] for i in indices] if indices else self.dataset.get_splits(["test"])

        print("Start running inference...")

        # Start measuring wall and CPU time
        start = datetime.now()
        start_cpu = time.process_time()

        # Predict the result for all data points
        outputs = []
        for i, record in enumerate(tqdm(records, total=len(records))):

            # Run Method
            outputs.append(self.method.run(record, self.model, **self.config))

            # Saving regulary
            if (i+1)%10 == 0:
                print(f"In step {i+1}")
                self.save_experiment(outputs, None)

        # End measuring wall and CPU time
        end_cpu = time.process_time()
        end = datetime.now()

        wall_time = end - start
        cpu_time = end_cpu - start_cpu

        print("Calculate metrics...")

        # Calculate the given metric
        metric_results = self.metric.compute_metric(outputs)

        # Estimate costs
        if self.model:
            costs = self.model.estimated_cost()
        else:
            costs = self.method.estimated_cost()

        performance_dict = {
            "wall_time": wall_time,
            "cpu_time": cpu_time,
            "performance": metric_results,
            "costs": costs
        }

        print("Save results...")

        # Saving results
        self.save_experiment(outputs, performance_dict)

        return performance_dict


if __name__ == "__main__":

    pipeline = Pipeline.load_pipeline_from_config_file("config/gsm8k/gsm8k_cot_gpt.yml") 
    performance_dict = pipeline.run(indices=[0, 1, 2] )

    print("\n-------------------------------")
    print("STATISTICS")
    print("Needed wall time: " + str(performance_dict["wall_time"]))
    print("Needed cpu time: " + str(performance_dict["cpu_time"]))
    print(performance_dict["performance"])
    print(performance_dict["costs"])
    print("-------------------------------")
