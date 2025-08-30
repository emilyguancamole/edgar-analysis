from edgar_client import EdgarClient
from parsers.f13_parser import Form13FParser
from parsers.g13_parser import Form13GParser
from llm_client import LLMClient
from db.savers import save_to_csv
from config import MODEL_NAME

if __name__ == "__main__":
    CIK_FULL = "CIK0000763212"
    # CIK_STRIPPED = "763212"
    # SEC requires a descriptive User-Agent header (name and contact)
    user_agent = "Emily Guan emily@example.com"
    client = EdgarClient(CIK_FULL, user_agent)
    submissions = client.get_submissions_feed()
    
    recent = submissions['filings']['recent']
    accessions_13f = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f == "13F-HR"]
    accessions_13g = [a for a, f in zip(recent['accessionNumber'], recent['form']) if f.startswith("SC 13G")]

    f13_parser = Form13FParser(client)
    f13_data = [f13_parser.parse_primary_doc(acc) for acc in accessions_13f[:5]]
    save_to_csv(f13_data, "extracted_13f.csv")
    # save_to_csv(sum(f13_data, []), "extracted_13f.csv")?

    # llm = LLMClient(MODEL_NAME)
    # g13_parser = Form13GParser(client, llm)
    # g13_data = [g13_parser.parse_primary_doc(acc) for acc in accessions_13g[:5]]
    # save_to_csv(g13_data, "extracted_13g.csv")
