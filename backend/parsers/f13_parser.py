from itertools import chain
import json
from pathlib import Path
import time
import traceback
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from .base_parser import BaseParser
from edgar_client import EdgarClient

class Form13FParser(BaseParser):
    PARSER_VER = 1 # bump if change parser logic

    def __init__(self, client: "EdgarClient"):
        self.client = client #* EdgarClient instance

    def parse_primary_doc(self, acc_stripped) -> List[Dict]:
        """
        For Form 13F XML file for one accession number. Parse <infoTable> entries, one per holding.
        """
        # For 13F forms: find infotable xml file name
        index_json = self.client.get_index_json(acc_stripped)
        report_date = self.client.get_primary_doc_name_date(acc_stripped)[1]
        info_file = next((i["name"] for i in index_json["directory"]["item"] if "infotable" in i["name"]), None)
        if not info_file:
            # TODO process txt files like https://www.sec.gov/Archives/edgar/data/763212/000104746912006030/a2209625z13f-hr.txt
            print(f"Info table xml/txt file not found for {acc_stripped}")
            return []
        # else: # true fail
        #     print(f"Info table xml/txt file not found for {acc_stripped}")
        #     traceback.print_exc()
        #     return []
        # Get infotable XML file and parse
        xml_content = self.client.fetch_file(acc_stripped, info_file)
        root = ET.fromstring(xml_content)
        ns = {}
        if root.tag.startswith('{'):
            ns_uri = root.tag.split("}")[0].strip("{")
            ns = {"ns1": ns_uri}
        infotables = root.findall(".//ns1:infoTable", ns)

        rows = []
        for info in infotables:
            rows.append({
                "accession_number": acc_stripped,
                "report_date": report_date,
                "cik": self.client.cik,
                "issuer": info.findtext("ns1:nameOfIssuer", namespaces=ns), #* findtext: Find text for first matching element by tag name or path
                "class": info.findtext("ns1:titleOfClass", namespaces=ns),
                "cusip": info.findtext("ns1:cusip", namespaces=ns),
                "figi": info.findtext("ns1:figi", namespaces=ns),
                "value_dollar": int(info.findtext("ns1:value", default=-1, namespaces=ns)),
                "shares_owned": int(info.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamt", default=-1, namespaces=ns)), # shares or principal amount
                "share_type": info.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamtType", namespaces=ns),
                "discretion": info.findtext("ns1:investmentDiscretion", namespaces=ns),
                "voting_sole": info.findtext("ns1:votingAuthority/ns1:Sole", namespaces=ns),
                "voting_shared": info.findtext("ns1:votingAuthority/ns1:Shared", namespaces=ns),
                "voting_none": info.findtext("ns1:votingAuthority/ns1:None", namespaces=ns),
                "primary_doc_url": f"{self.client.filing_baseurl}/{acc_stripped.replace('-', '')}/{info_file}",
            })
        return rows
    
    def parse_all(self, acc_numbers: List[str], limit: Optional[int] = None, use_cache=True) -> List[Dict]:
        """
        Parse multiple accession numbers and return a flat list of dict rows. Checks cache for already-processed accessions.
        - acc_numbers: list of accession number strings
        - limit: optional max number of accessions to process

        Returns:
        - List[Dict]: flattened list where each dict is one infoTable row.
        """
        
        to_process = acc_numbers[:limit] if limit is not None else acc_numbers
        print(f"Processing {len(to_process)} accession numbers")
        to_process = [a.replace('-', '') for a in to_process] # strip dashes
        per_file_rows: List[List[dict]] = [] # list of lists of dicts. each sublist=rows of holding dicts for one accession number
        for acc in to_process:
            try:
                if use_cache: # Check cache for already-processed accessions
                    cached = self._load_cache(acc)
                    if cached is not None:
                        print(f"Loaded {len(cached)} cached rows for {acc}")
                        per_file_rows.append(cached)
                        continue
                # Not found in cache
                file_rows = self.parse_primary_doc(acc)
                if file_rows:
                    per_file_rows.append(file_rows)
                    self._save_to_cache(acc, file_rows)
            except Exception as e:
                print(f"Error parsing {acc}: {e}")
                traceback.print_exc()
        # Flatten into single list-of-dicts, each dict=one holding row
        return list(chain.from_iterable(per_file_rows))
    

    
    def _load_cache(self, acc):
        path = Path("cache/f13").joinpath(f"{acc}.json")
        if not path.exists():
            return None
        try:
            data = json.load(path.open("r", encoding="utf-8"))
            # metadata checks
            if data.get("parser_version") < self.PARSER_VER:
                return None
            # later: time invalidate
            return data.get("rows")
                
        except Exception as e:
            print(f"Error loading cache for {acc}: {e}")
            path.unlink(missing_ok=True) # delete corrupted cache file
            return None
    
    def _save_to_cache(self, acc, rows: List[Dict]):
        path = Path("cache/f13").joinpath(f"{acc}.json")
        tmp = path.with_suffix(".json.tmp")
        # Write data + metadata to a temp file to keep update atomic
        payload = {"cache_time": time.time(), "parser_version": self.PARSER_VER, "rows": rows}
        try:
            tmp.write_text(json.dumps(payload), encoding="utf-8") #* dumps produces a string, dump writes to a file
            tmp.replace(path) # overwrite the target path
        except Exception:
            tmp.unlink(missing_ok=True)
