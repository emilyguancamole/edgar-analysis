
import json
import traceback
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging
from models import FormGEntry
from .base_parser import BaseParser
from llm.base_llm_client import BaseLLMClient
from llm.llm_cache import LLMCache
from edgar_client import EdgarClient


class Form13GParser(BaseParser):
    def __init__(self, client: EdgarClient, llm_client: BaseLLMClient):
        self.client = client
        self.llm = llm_client
        self.logger = logging.getLogger(__name__)

    def parse_primary_doc(self, acc_stripped: str) -> dict:
        # Find name of primary filing document
        primary_doc_name = self.client.get_primary_doc_name_date(acc_stripped)[0]
        if not primary_doc_name:
            return {}

        # Get the primary doc content
        html_content = self.client.fetch_file(acc_stripped, primary_doc_name)
        soup = BeautifulSoup(html_content, "lxml")
        text = soup.get_text(" ", strip=True)

        # See if doc content is cached
        cache = LLMCache() #?? where to place
        file_data = cache.get(acc_stripped)
        if not file_data:
            try:
                # LLM extraction and validation using the pydantic model
                file_data: dict = self.llm.extract_and_validate(text, entry_model=FormGEntry, max_tries=1)
                cache.set(acc_stripped, file_data) # cache llm output only
            except Exception as e:
                print(f"LLM extraction/validation failed for accession {acc_stripped}: {e}")
                traceback.print_exc() 
                return {}
        else:
            print("Cache found")

        # Add accession_number, return as a filing-level dict
        filing = {
            "accession_number": acc_stripped, 
            "cik": self.client.cik,
            "primary_doc": primary_doc_name, 
            **file_data}
        return filing
    
    def parse_all(self, acc_numbers: List[str], limit: Optional[int] = None) -> List[dict]:
        to_process = acc_numbers[:limit] if limit is not None else acc_numbers
        to_process = [a.replace('-', '') for a in to_process]
        total = len(to_process)
        print(f"Processing {total} Form 13G filings...")

        data = [] # list of dicts, one per accession
        for idx, acc in enumerate(to_process, start=1):
            print(f"[{idx}/{total}] Processing accession {acc}...")
            try:
                entry = self.parse_primary_doc(acc)
                if entry:
                    data.append(entry)
                    print(f"Success — collected {len(data)} filings.")
                else:
                    print(f"No data extracted for {acc}.")
            except Exception as e:
                print(f"Error processing {acc}: {e}")

        return data
    
    