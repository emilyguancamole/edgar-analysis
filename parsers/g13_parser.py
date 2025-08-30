
from bs4 import BeautifulSoup
import json
from .base_parser import BaseParser
from llm_client import LLMClient
from edgar_client import EdgarClient

class Form13GParser(BaseParser):
    def __init__(self, client: EdgarClient, llm: LLMClient):
        self.client = client
        self.llm = llm

    def parse_primary_doc(self, acc_stripped: str) -> dict:
        # Find name of primary filing document
        primary_doc_name = self.client.get_primary_doc_name(acc_stripped)
        if not primary_doc_name:
            return {}

        # Get the primary doc content
        html_content = self.client.fetch_file(acc_stripped, primary_doc_name)

        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text(" ", strip=True)
        
        response = self.llm.extract(text)
        return json.loads(response)
    