from metrics.BaseMetric import BaseMetric

class Accuracy(BaseMetric):
    def __init__(self, dataset, **kwargs):
        super().__init__(dataset, **kwargs)

        self.name = "accuracy"

    def compute_metric(self, results: list[dict]) -> dict:
        correct_samples = 0
        for res in results:
            pre = res["predicted_answers"][0]
            truth = res["true_answer"]

            correct_samples += self.dataset.check_answer(pre, truth)

        acc = correct_samples / len(results)

        return {self.name: acc}
    