import numpy as np
from typing import List

from models.player_model import predict_player_points
from models.monte_carlo import MonteCarlo, PredictionDistribution


def predict_team_points(player_ids: List[int], gw: int, n_sims: int = 10000) -> PredictionDistribution:
    """
    Basic team prediction:
    - No captain multiplier
    - No DGW support
    - No bench logic
    - Just sum player distributions

    Returns full PredictionDistribution for the TEAM.
    """

    mc = MonteCarlo(n_sims=n_sims)

    # Collect samples for all players
    team_samples = np.zeros(n_sims)

    for pid in player_ids:
        mean, std = predict_player_points(pid, gw)
        dist = mc.simulate(mean, std)
        team_samples += dist.samples  # elementwise summation

    # Now compute team distribution summary
    return PredictionDistribution(
        samples=team_samples,
        expected=float(np.mean(team_samples)),
        median=float(np.percentile(team_samples, 50)),
        p25=float(np.percentile(team_samples, 25)),
        p75=float(np.percentile(team_samples, 75)),
        p90=float(np.percentile(team_samples, 90)),
    )
