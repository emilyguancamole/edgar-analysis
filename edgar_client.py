from bs4 import BeautifulSoup
import requests
import json
from typing import Tuple, Dict

class EdgarClient:
    def __init__(self, cik_full: str, cik_stripped: str, user_agent: str):
        self.submissions_url = f"https://data.sec.gov/submissions/{cik_full}.json"
        self.filing_baseurl = f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get_submissions_feed(self) -> Dict:
        """Get the overall EDGAR submissions json feed"""
        r = self.session.get(self.submissions_url)
        r.raise_for_status()
        return r.json()

    def get_index_json(self, acc_stripped: str) -> Dict:
        """Get index.json for one accession number"""
        r = self.session.get(f"{self.filing_baseurl}/{acc_stripped}/index.json")
        r.raise_for_status()
        return r.json()

    def get_primary_doc_name(self, acc_stripped: str) -> str:
        """Get primary doc file name. Usually "infotable" for 13f, variable for 13g"""
        items = self.get_index_json(acc_stripped)['directory']['item']
        candidates = [f for f in items if f["name"].endswith((".htm", ".html"))] # prefer htm
        if not candidates:
            candidates = [f for f in items if f["name"].endswith(".txt")]
        # Assuming largest is the primary. missing sizes = small
        candidates.sort(key=lambda x: x.get("size", 0))
        primary_doc_name = candidates[-1]["name"]
        return primary_doc_name
    
    def extract_text_from_primary_doc(content_bytes: bytes) -> str:
        """Extract text from primary doc. For Form 13g, usually html or txt
        content_bytes: response.content from get() request for the primary doc file
        """
        soup = BeautifulSoup(content_bytes, "lxml")
        all_text = soup.get_text(" ", strip=True) # extracting all the text from a page
        #todo further parse text?
        return all_text
        

    def fetch_file(self, acc_stripped: str, filename: str) -> bytes:
        """Form url and fetch the file for an accession number
        returns: (file content bytes)"""

        url = f"{self.filing_baseurl}/{acc_stripped}/{filename}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.content