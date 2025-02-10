from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, df, current_candle, backcandles):
        """
        This method should return:
        - 1 for a Buy signal
        - -1 for a Sell signal
        - 0 for no action
        """
        pass
