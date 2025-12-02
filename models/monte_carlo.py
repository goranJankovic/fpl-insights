import numpy as np
from dataclasses import dataclass

@dataclass
class PredictionDistribution:
    samples: np.ndarray
    expected: float
    median: float
    p25: float
    p75: float
    p90: float

    def summary(self) -> dict:
        return {
            "expected": self.expected,
            "median": self.median,
            "p25": self.p25,
            "p75": self.p75,
            "p90": self.p90,
        }


class MonteCarlo:
    def __init__(self, n_sims: int = 10000, random_seed: int | None = None):
        self.n_sims = n_sims
        if random_seed is not None:
            np.random.seed(random_seed)

    def simulate(self, mean: float, std: float) -> PredictionDistribution:
        """
        Simulate points distribution based on normal distribution.
        Negative values are clipped to zero (FPL can't score negative
        except cards, but we handle that later).
        """

        # Generate samples
        samples = np.random.normal(loc=mean, scale=std, size=self.n_sims)

        # Clip negative values to 0
        samples = np.clip(samples, 0, None)

        # Round to nearest 0.1 or integer? -> For now keep float for precision
        return PredictionDistribution(
            samples=samples,
            expected=float(np.mean(samples)),
            median=float(np.percentile(samples, 50)),
            p25=float(np.percentile(samples, 25)),
            p75=float(np.percentile(samples, 75)),
            p90=float(np.percentile(samples, 90)),
        )
