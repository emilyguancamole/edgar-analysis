import json
import os

class LLMCache:
    def __init__(self, cache_file="llm/llm_cache.json"):
        self.cache_file = cache_file
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}
    
    def get(self, accession) -> dict:
        """Return cached data (llm output as json) for an accession number."""
        return self.cache.get(accession)

    def set(self, accession, data) -> None:
        self.cache[accession] = data
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)