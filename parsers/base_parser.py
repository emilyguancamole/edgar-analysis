from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, accession: str) -> list[dict]:
        """Parse the filing into structured data"""