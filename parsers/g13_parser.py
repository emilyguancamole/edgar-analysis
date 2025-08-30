
from bs4 import BeautifulSoup
import json
from .base_parser import BaseParser
from ..llm.llm_client import LLMClient

class Form13GParser(BaseParser):
    def __init__(self, client, llm: LLMClient):
        self.client = client
        self.llm = llm

    def parse(self, accession: str) -> dict:
        index_json = self.client.get_index(accession)
        items_json = json.loads(index_json.text)['directory']['item']

        # Find name of primary filing document
        get_primary_doc_name

        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text(" ", strip=True)
        
        response = self.llm.extract(text)
        return json.loads(response)