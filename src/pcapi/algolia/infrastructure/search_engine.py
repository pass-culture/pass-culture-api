from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import List


class SearchEngine(ABC):
    @abstractmethod
    def add_objects(self, objects: List[Dict]) -> None:
        pass

    @abstractmethod
    def delete_objects(self, objects: List[Dict]) -> None:
        pass

    def clear_index(self) -> None:
        pass
