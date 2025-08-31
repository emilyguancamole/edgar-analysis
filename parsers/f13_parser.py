from itertools import chain
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from models import FormGEntry
from .base_parser import BaseParser

class Form13FParser(BaseParser):
    def __init__(self, client):
        self.client = client #* EdgarClient instance

    def parse_primary_doc(self, acc_stripped) -> List[Dict]:
        """
        For Form 13F XML file for one accession number. Parse <infoTable> entries, one per holding.

        xml_bytes: response.content from get() request for the primary doc file
        acc_number: current accession number to get info for
        url: optional, url of resource for XML file
        """
        # For 13F forms: find infotable xml file name
        index_json = self.client.get_index_json(acc_stripped)
        report_date = self.client.get_primary_doc_name_date(acc_stripped)[1]
        info_file = next((i["name"] for i in index_json["directory"]["item"] if "infotable" in i["name"]), None)
        if not info_file:
            print("Info table not found")
            return []
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
                "url": f"{self.client.filing_baseurl}/{acc_stripped.replace('-', '')}/{info_file}",
            })
        return rows
    
    def parse_all(self, acc_numbers: List[str], limit: Optional[int] = None) -> List[Dict]:
        """Parse multiple accession numbers and return a flat list of dict rows.
        - acc_numbers: list of accession number strings
        - limit: optional max number of accessions to process

        Returns:
        - List[Dict]: flattened list where each dict is one infoTable row.
        """
        to_process = acc_numbers[:limit] if limit is not None else acc_numbers
        to_process = [a.replace('-', '') for a in to_process] # strip dashes
        per_file_rows: List[List[dict]] = [] # list of lists of dicts. each sublist=rows of holding dicts for one accession number
        for acc in to_process:
            try:
                file_rows = self.parse_primary_doc(acc)
                if file_rows:
                    per_file_rows.append(file_rows)
            except Exception as e:
                print(f"error parsing {acc}: {e}")
        # Flatten into single list-of-dicts
        return list(chain.from_iterable(per_file_rows))
    
