
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json

from models import FormGEntry
from .base_parser import BaseParser
from llm.llm_client import LLMClient
from edgar_client import EdgarClient

class Form13GParser(BaseParser):
    def __init__(self, client: EdgarClient, llm: LLMClient):
        self.client = client
        self.llm = llm

    def parse_primary_doc(self, acc_stripped: str) -> dict:
        # Find name of primary filing document
        primary_doc_name = self.client.get_primary_doc_name_date(acc_stripped)[0]
        if not primary_doc_name:
            return {}

        # Get the primary doc content
        html_content = self.client.fetch_file(acc_stripped, primary_doc_name)
        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text(" ", strip=True)
        
        try:
            # LLM extraction and validation using the pydantic model
            file_data: dict = self.llm.extract_and_validate(text, entry_model=FormGEntry, max_retries=1)

        except Exception as e:
            print(f"LLM extraction/validation failed for accession {acc_stripped}: {e}")
            return {}

        # Add accession_number, return as a filing-level dict
        filing = {
            "accession_number": acc_stripped, 
            "primary_doc": primary_doc_name, 
            **file_data}
        return filing
    
    def parse_all(self, acc_numbers: List[str], limit: Optional[int] = None) -> List[dict]:
        to_process = acc_numbers[:limit] if limit is not None else acc_numbers
        to_process = [a.replace('-', '') for a in to_process]

        data = [] # list of dicts, one per accession
        for acc in to_process:
            try:
                entry = self.parse_primary_doc(acc)
                if entry:
                    data.append(entry)
            except Exception as e:
                print(f"Error processing {acc}: {e}")

        return data
    
    