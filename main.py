from itertools import chain
from typing import List
from edgar_client import EdgarClient
from parsers.f13_parser import Form13FParser
from parsers.g13_parser import Form13GParser
from llm.llm_client import LLMClient
from db.savers import save_to_csv
from config import MODEL_NAME
import argparse
import os

if __name__ == "__main__":
    """
    Example run: CUDA_VISIBLE_DEVICES=0 python main.py --form_type all
    """

    parse = argparse.ArgumentParser(description="EDGAR 13F and 13G Data Extractor")
    parse.add_argument("--cik", type=str, default="CIK0000763212", help="Full CIK with leading zeros, e.g. CIK0000763212")
    parse.add_argument("--form_type", type=str, choices=["13f", "13g", "all"], required=True, help="Form type to extract: 13f, 13g, all")
    parse.add_argument("--limit", type=int, default=5, help="Max number of filings to process per form type")
    args = parse.parse_args()
    
    user_agent = "My Name myname@gmail.com"
    client = EdgarClient(args.cik, user_agent)
    submissions = client.get_submissions_feed()
    
    recent = submissions['filings']['recent']
    accessions_13f = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f == "13F-HR"]
    accessions_13g = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f.startswith("SC 13G")]

    if args.form_type == "13f" or args.form_type == "all":
        f13_parser = Form13FParser(client)
        f13_data: List[dict] = f13_parser.parse_all(accessions_13f, limit=args.limit)
        save_to_csv(f13_data, "extracted_13f.csv")
    if args.form_type == "13g" or args.form_type == "all":
        llm = LLMClient(MODEL_NAME)
        g13_parser = Form13GParser(client, llm)
        g13_data: List[dict] = g13_parser.parse_all(accessions_13g, limit=args.limit)
        save_to_csv(g13_data, "extracted_13g.csv")
