from .base_agent import BaseAgent

class TruthfulAgent(BaseAgent):
    # simple agent that just bids exactly what it's worth
    def __init__(self, name: str = "TruthfulAgent"):
        super().__init__(name)

    def bid(self, true_value: float, auction_type: str) -> float:
        return true_value
