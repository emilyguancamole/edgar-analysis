import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from model import FormGEntry
import json
from .base_parser import BaseParser

class Form13FParser(BaseParser):
    def __init__(self, client):
        self.client = client #* EdgarClient instance

    def extract_data(self, accession_number: str):
        acc_stripped = accession_number.replace("-", "")
        # get index, find infotable, parse
        idx = self.edgar.get_index(acc_stripped)
        infotable_name = next((i['name'] for i in idx['directory']['item'] if 'infotable' in i['name']), None)
        if not infotable_name:
            return []
        xml = self.edgar.fetch_file(acc_stripped, infotable_name)
        return self.parsers['13f'].parse_infotable(xml, accession_number)


    def parse(self, acc_stripped) -> List[Dict]:
        """
        For Form 13F XML file for one accession number. Parse <infoTable> entries, one per holding.

        xml_bytes: response.content from get() request for the primary doc file
        acc_number: current accession number to get info for
        url: optional, url of resource for XML file
        """
        # For 13F forms: find infotable file name
        index_json = self.client.get_index_json(acc_stripped)
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
                "report_date": root.findtext("ns1:periodOfReport", namespaces=ns),
                "issuer": info.findtext("ns1:nameOfIssuer", namespaces=ns), #* findtext: Find text for first matching element by tag name or path
                "class": info.findtext("ns1:titleOfClass", namespaces=ns),
                "cusip": info.findtext("ns1:cusip", namespaces=ns),
                "figi": info.findtext("ns1:figi", namespaces=ns),
                "value": int(info.findtext("ns1:value", default=-1, namespaces=ns)),
                "shares_owned": int(info.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamt", default=-1, namespaces=ns)), # shares or principal amount
                "share_type": info.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamtType", namespaces=ns),
                "discretion": info.findtext("ns1:investmentDiscretion", namespaces=ns),
                "voting_sole": info.findtext("ns1:votingAuthority/ns1:Sole", namespaces=ns),
                "voting_shared": info.findtext("ns1:votingAuthority/ns1:Shared", namespaces=ns),
                "voting_none": info.findtext("ns1:votingAuthority/ns1:None", namespaces=ns),
                "url": f"{self.client.filing_baseurl}/{acc_stripped.replace('-', '')}/{info_file}",
            })
        return rows