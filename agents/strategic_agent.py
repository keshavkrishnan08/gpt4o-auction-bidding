from .base_agent import BaseAgent

class StrategicAgent(BaseAgent):
    # always bids a fixed percentage of the value (defaults to 70%)
    def __init__(self, name: str = "StrategicAgent", strategy_factor: float = 0.7):
        super().__init__(name)
        self.strategy_factor = strategy_factor

    def bid(self, true_value: float, auction_type: str) -> float:
        return true_value * self.strategy_factor
