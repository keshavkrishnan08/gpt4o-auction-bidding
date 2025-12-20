import random
from .base_agent import BaseAgent

class RandomAgent(BaseAgent):
    # this guy just bids a random amount up to his true value
    def __init__(self, name: str = "RandomAgent"):
        super().__init__(name)

    def bid(self, true_value: float, auction_type: str) -> float:
        return random.uniform(0, true_value)
