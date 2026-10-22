"""
Random Valid Dispatcher Baseline.
Samples uniformly from all legal actions defined by the action mask.
"""

import numpy as np
from rl.environment import WarehouseFleetEnv


class RandomMaskedPolicy:
    """
    Selects uniformly among valid actions. Serves as empirical lower bound.
    """

    def __init__(self, name: str = "Random-Masked", seed: int = 42):
        self.name = name
        self.rng = np.random.RandomState(seed)

    def predict(self, obs: np.ndarray, env: WarehouseFleetEnv) -> int:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        return int(self.rng.choice(valid_actions))
