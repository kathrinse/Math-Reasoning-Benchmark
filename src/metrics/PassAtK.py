from metrics.BaseMetric import BaseMetric

import numpy as np

# Numerically stable implementation using Codex implementation (https://arxiv.org/pdf/2107.03374.pdf)

# :param n: total number of samples
# :param c: number of correct samples
# :param k: k in pass@$k$

class PassAtK(BaseMetric):
    def __init__(self, dataset, k=3, n=10, **kwargs):
        super().__init__(dataset, **kwargs)

        self.name = "pass@" + str(k)
        self.k = int(k)
        self.n = int(n)

    def pass_at_k(self, c):
        if self.n - c < self.k:
            return 1.0
        
        return 1.0 - np.prod(1.0 - self.k / np.arange(self.n - c + 1, self.n + 1))

    def compute_metric(self, results: list[dict]) -> dict:
        hitsatk = []
        for res in results:
            c = 0

            pre = res["predicted_answers"]
            truth = res["true_answer"]

            for p in pre[:self.n]:
                c += self.dataset.check_answer(p, truth)

            hitsatk.append(self.pass_at_k(c))

        hits_mean = np.mean(hitsatk)
        hits_std = np.std(hitsatk)

        return {self.name: hits_mean, self.name + "_std": hits_std}
    