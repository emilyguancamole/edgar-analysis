from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse_primary_doc(self, acc_stripped: str) -> list[dict]:
        """Parse the filing for an acc number into structured data"""
