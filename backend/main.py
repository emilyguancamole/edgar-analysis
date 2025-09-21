from itertools import chain
import os
from typing import List
from edgar_client import EdgarClient
from parsers.f13_parser import Form13FParser
from parsers.g13_parser import Form13GParser
from llm.base_llm_client import BaseLLMClient
from llm.helpers import get_llm_client
from db.savers import save_13f_to_db, save_13g_to_db, save_to_csv
import argparse
import json

if __name__ == "__main__":
    """
    Example run: cd backend; CUDA_VISIBLE_DEVICES=0 python main.py --form_type all --dest both 
    """

    parse = argparse.ArgumentParser(description="EDGAR 13F and 13G Data Extractor")
    parse.add_argument("--cik", type=str, default="CIK0000763212", help="Full CIK with leading zeros, e.g. CIK0000763212")
    parse.add_argument("--form_type", type=str, choices=["13f", "13g", "all"], required=True, help="Form type to extract: 13f, 13g, all")
    parse.add_argument("--limit", type=int, required=False, help="Max number of filings to process per form type, defaults to None")
    parse.add_argument("--dest", type=str, choices=["csv", "db", "both"], default="csv", help="Destination for parsed data: csv (default), db, or both")
    parse.add_argument("--config_file", type=str, default="config_hf.json", help="Name of config json file in config folder, for 13G LLM processing")
    parse.add_argument("--debug", action="store_true", help="Enable debug logging for LLM client")
    # todo clean up what's stored in debug log
    args = parse.parse_args()
    
    user_agent = "My Name myname@gmail.com"
    config = json.load(open(os.path.join("config", args.config_file)))
    client = EdgarClient(args.cik, user_agent=user_agent)
    submissions = client.get_submissions_feed()
    
    recent = submissions['filings']['recent']
    accessions_13f = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f == "13F-HR"]
    accessions_13g = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f.startswith("SC 13G")]

    if args.form_type == "13f" or args.form_type == "all":
        print("Processing 13F filings...")
        f13_parser = Form13FParser(client)
        f13_data: List[dict] = f13_parser.parse_all(accessions_13f, limit=args.limit)
        if args.dest in ("csv", "both"):
            save_to_csv(f13_data, "data/extracted_13f.csv")
        if args.dest in ("db", "both"):
            save_13f_to_db(f13_data)
        
    if args.form_type == "13g" or args.form_type == "all":
        print("Processing 13G filings...")
        llm_client = get_llm_client(config, debug=args.debug)
        g13_parser = Form13GParser(client, llm_client)
        g13_data: List[dict] = g13_parser.parse_all(accessions_13g, limit=args.limit)
        if args.dest in ("csv", "both"):
            save_to_csv(g13_data, "data/extracted_13g.csv")
        if args.dest in ("db", "both"):
            save_13g_to_db(g13_data)
