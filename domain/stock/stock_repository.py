from abc import ABC, abstractmethod

from domain.stock.stock import Stock


class StockRepository(ABC):
    @abstractmethod
    def find_stock_by_id(self, stock_id: int) -> Stock:
        pass
