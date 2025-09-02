
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging


from models import FormGEntry
from .base_parser import BaseParser
from llm.llm_client import LLMClient
from edgar_client import EdgarClient

class Form13GParser(BaseParser):
    def __init__(self, client: EdgarClient, llm: LLMClient):
        self.client = client
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    def parse_primary_doc(self, acc_stripped: str) -> dict:
        # Find name of primary filing document
        primary_doc_name = self.client.get_primary_doc_name_date(acc_stripped)[0]
        if not primary_doc_name:
            return {}

        #? Get the primary doc content and prefilter - CHECK
        filing_content = self.client.fetch_file(acc_stripped, primary_doc_name)
        text = self.prefilter_13g_sections(filing_content)

        try:
            # LLM extraction and validation using the pydantic model
            file_data: dict = self.llm.extract_and_validate(text, entry_model=FormGEntry, max_retries=1)

        except Exception as e:
            print(f"LLM extraction/validation failed for accession {acc_stripped}: {e}")
            return {}

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
                    print(f"[{idx}/{total}] Success — collected {len(data)} filings so far.")
                else:
                    print(f"[{idx}/{total}] No data extracted for {acc}.")
            except Exception as e:
                print(f"[{idx}/{total}] Error processing {acc}: {e}")

        return data
    
    
    def prefilter_13g_sections(self, filing_text):
        """
        Prefilter 13G/13G-A text to extract section from html or txt.

        TODO: super simple for now - keeps all text between Form 13G and signature. the tables made the text much longer......
        """

        if "<html" in filing_text.lower():
            soup = BeautifulSoup(filing_text, "html.parser") #? lxml
            main_text = soup.get_text(" ", strip=True)
            #! Tables giving me issues bc it appends table text onto existing text... if just getting the original text isn't an issue then skip tables.
            # tables = ["\n" + table.get_text(" ", strip=True) for table in soup.find_all("table")]
            body_text = main_text
        else:
            body_text = filing_text
        
        # Regex
        schedule_match = re.search(r'(Schedule\s+13G[^\n]*)', body_text, re.IGNORECASE)
        signature_match = re.search(r'(Signature|Certification)', body_text, re.IGNORECASE)
        if schedule_match and signature_match:
            block = body_text[schedule_match.start():signature_match.end()]
        else:
            block = body_text # fallback

        return block
        

        #todo something wrong with below or how I'm unit testing it. also worried it'll cut out info -- keeping more text is safer for now
        # # Find Item sections
        # item_pattern = re.compile(r'(Item\s+[0-9A-Za-z\.]+[\s\S]*?)(?=(Item\s+[0-9A-Za-z\.]+|Exhibit|Signature|Certification|$))', re.IGNORECASE)
        # items = item_pattern.findall(block) # find all item sections in the block
        # kept_sections.extend([item[0] for item in items])
                
        # # Get all Exhibit blocks
        # exhibit_pattern = re.compile(r'(Exhibit[\s\S]*?)(?=(Item\s+[0-9A-Za-z\.]+|Signature|Certification|$))', re.IGNORECASE)
        # exhibits = exhibit_pattern.findall(block)
        # kept_sections += exhibits

        # # Keyword-driven lines for older files - slow??
        # relevant_lines = []
        # keywords = ["beneficial ownership", "voting power", "dispositive power", "percent of class", "cusip", "issuer", "reporting person"]
        # for line in block.splitlines():
        #     print(line)
        #     if any(kw in line.lower() for kw in keywords):
        #         relevant_lines.append(line)

        