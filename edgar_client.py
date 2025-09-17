import random
import time
from bs4 import BeautifulSoup
import requests
import json
from typing import Tuple, Dict

# def _strip_acc(acc_number: str) -> str:
#         """Strip dashes from accession number"""
#         return acc_number.replace('-', '')

class EdgarClient:
    def __init__(self, cik_full: str, user_agent: str):
        self.submissions_url = f"https://data.sec.gov/submissions/{cik_full}.json"
        self.cik = cik_full
        cik_stripped = cik_full.replace("CIK", "").lstrip("0")
        self.filing_baseurl = f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    # TODO add exponential backoff

    def fetch_json_with_retry(self, url, max_attempts=5) -> Dict:
        """ no caching -- that is handled in parsers """
        for attempt in range(1, max_attempts+1):
            try:
                r = self.session.get(url)
            except requests.RequestException as e: # network failure
                time.sleep(min(60, (2 ** attempt) + random.random()))
                if attempt == max_attempts:
                    raise e
                continue
            
            if r.status_code == 200:
                # print("fetched json successfully")
                return r.json()
            
            if r.status_code==429 or r.status_code>=500: # rate limiting, or server error
                print(f"backoff for {url}")
                time.sleep(min(60, (2 ** attempt) + random.random()))
                if attempt == max_attempts:
                    r.raise_for_status()
                continue
            # other error -> fail immediately
            r.raise_for_status()
        
        raise RuntimeError(f"Exceeded max attempts fetching {url}")

    def get_submissions_feed(self) -> Dict:
        """Get the overall EDGAR submissions json feed"""
        return self.fetch_json_with_retry(self.submissions_url)

    def get_index_json(self, acc: str) -> Dict:
        """Get index.json for one accession number"""
        return self.fetch_json_with_retry(f"{self.filing_baseurl}/{acc}/index.json")

    def get_primary_doc_name_date(self, acc: str) -> Tuple[str, str]:
        """Get primary doc file name and last modified date. Usually "infotable" for 13f, variable for 13g"""
        items = self.get_index_json(acc)['directory']['item']
        candidates = [f for f in items if f["name"].endswith((".htm", ".html"))] # prefer htm
        if not candidates:
            candidates = [f for f in items if f["name"].endswith(".txt")]
        # Assuming largest is the primary. missing sizes = small
        candidates.sort(key=lambda x: x.get("size", 0))
        primary_doc_name = candidates[-1]["name"]
        report_date = candidates[-1].get("last-modified", "").split(" ")[0]  # just the date part, no time
        return primary_doc_name, report_date
    
    def extract_text_from_primary_doc(content_bytes: bytes) -> str:
        """Extract text from primary doc. For Form 13g, usually html or txt
        content_bytes: response.content from get() request for the primary doc file
        """
        soup = BeautifulSoup(content_bytes, "lxml")
        all_text = soup.get_text(" ", strip=True) # extracting all the text from a page
        #todo further parse text?
        return all_text
        

    def fetch_file(self, acc: str, filename: str) -> bytes:
        """Form url and fetch the file for an accession number
        returns: (file content bytes)"""

        url = f"{self.filing_baseurl}/{acc}/{filename}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.content
    
    