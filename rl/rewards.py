"""
Reward function formulation for multi-robot warehouse fleet learning.
Encourages high throughput, swift deliveries, low travel cost, and zero deadlocks.
"""

from typing import Dict, Any


class RewardCalculator:
    """
    Computes dense, interpretable rewards and logs individual components.
    """

    def __init__(
        self,
        delivery_reward: float = 20.0,
        pickup_reward: float = 5.0,
        step_cost: float = 0.04,
        idle_penalty: float = 0.05,
        blocked_penalty: float = 0.20,
        deadlock_penalty: float = 1.0,
        depletion_penalty: float = 10.0
    ):
        self.delivery_reward = delivery_reward
        self.pickup_reward = pickup_reward
        self.step_cost = step_cost
        self.idle_penalty = idle_penalty
        self.blocked_penalty = blocked_penalty
        self.deadlock_penalty = deadlock_penalty
        self.depletion_penalty = depletion_penalty

    def calculate_reward(
        self,
        engine,
        step_result: Dict[str, Any],
        action_executed: bool
    ) -> float:
        """
        Calculates total reward for the current step and tracks components.
        """
        reward = 0.0

        # 1. Delivery completion reward (scaled by priority)
        completed = step_result.get("step_completions", 0)
        if completed > 0:
            reward += self.delivery_reward * completed

        # 2. Pickup progress reward
        pickups = step_result.get("step_pickups", 0)
        if pickups > 0:
            reward += self.pickup_reward * pickups

        # 3. Movement travel cost (discourage unnecessary circling)
        moving_robots = step_result.get("step_moves", 0)
        reward -= self.step_cost * moving_robots

        # 4. Congestion / blocked penalty
        blocked_count = sum(1 for r in engine.robots if r.blocked_steps > 0)
        reward -= self.blocked_penalty * blocked_count

        # 5. Idle penalty if waiting tasks exist
        if len(engine.waiting_tasks) > 0:
            idle_count = sum(1 for r in engine.robots if r.current_task is None and not r.is_charging and not r.is_faulty)
            reward -= self.idle_penalty * idle_count

        # 6. Deadlock penalty
        deadlocks = step_result.get("step_deadlocks", 0)
        if deadlocks > 0:
            reward -= self.deadlock_penalty * deadlocks

        # 7. Battery depletion penalty
        depletions = step_result.get("step_depletions", 0)
        if depletions > 0:
            reward -= self.depletion_penalty * depletions

        return float(reward)
