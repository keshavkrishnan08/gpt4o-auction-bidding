from abc import ABC, abstractmethod

class BaseAgent(ABC):
    # just a base class so all agents have a name and a bid method
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def bid(self, true_value: float, auction_type: str) -> float:
        # figure out what to bid based on the value and the auction rules
        pass
