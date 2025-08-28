import requests
import json
import pprint
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

CIK_FULL = "CIK0000763212"
CIK_STRIPPED = "763212"
submissions_url = f"https://data.sec.gov/submissions/{CIK_FULL}.json"
filing_baseurl = f"https://www.sec.gov/Archives/edgar/data/{CIK_STRIPPED}"


def get_f_data(acc_numbers: list):
    data = []
    num_of_filings = 5
    try:
        for i in range(num_of_filings):
            acc_stripped = acc_numbers[i].replace('-', '')
            # Get index.json - items table to list the files available in the filing
            index_response = requests.get(f"{filing_baseurl}/{acc_stripped}/index.json", headers=headers)
            items_json = json.loads(index_response.text)['directory']['item']

            # For 13F forms: find infotable file name
            info_file = ""
            for item in items_json:
                if "infotable" in item["name"]:
                    info_file = item["name"]
                    print("Info table file:", info_file)
                    break
            if not info_file:
                print("Info table not found")
            # Get infotable XML file 
            xml_response = requests.get(f"{filing_baseurl}/{acc_stripped}/{info_file}", headers=headers) # xml
            root = ET.fromstring(xml_response.content)
            # extract namespace
            if root.tag.startswith('{'):
                ns_uri = root.tag.split("}")[0].strip("{")
                ns = {"ns1": ns_uri}  # namespace prefix is ns1:
                infotables = root.findall(".//ns1:infoTable", ns)

            # one <infoTable> entry per holding
            for infotable in infotables: # .// XPath expression “search anywhere under the current node, recursively.”
                entry = {
                    "accession_number": acc_numbers[i],
                    "issuer": infotable.findtext("ns1:nameOfIssuer", namespaces=ns), #* findtext: Find text for first matching element by tag name or path.
                    "class": infotable.findtext("ns1:titleOfClass", namespaces=ns),
                    "cusip": infotable.findtext("ns1:cusip", namespaces=ns),
                    "value": int(infotable.findtext("ns1:value", default=-1, namespaces=ns)),
                    "shares": int(infotable.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamt", default=-1, namespaces=ns)),
                    "share_type": infotable.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamtType", namespaces=ns),
                    "discretion": infotable.findtext("ns1:investmentDiscretion", namespaces=ns),
                    "voting_sole": infotable.findtext("ns1:votingAuthority/ns1:Sole", namespaces=ns),
                    "voting_shared": infotable.findtext("ns1:votingAuthority/ns1:Shared", namespaces=ns),
                    "voting_none": infotable.findtext("ns1:votingAuthority/ns1:None", namespaces=ns),
                }
                data.append(entry)
        return data
    
    except Exception as e:
        print("Error:", e)


def get_primary_doc_url(acc_stripped):
    # Get index.json - items table to list the files available in the filing
    url = f"{filing_baseurl}/{acc_stripped}/index.json"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    items_json = json.loads(response.text)['directory']['item']

    # Find name of primary filing document
    candidates = [f for f in items_json if f["name"].endswith((".htm", ".html"))] # prefer html
    if not candidates:
        candidates = [f for f in items_json if f["name"].endswith(".txt")]
    # Assuming largest is the primary. missing sizes = small
    candidates.sort(key=lambda x: x.get("size", 0))
    doc_name = candidates[-1]["name"]
    print("Primary doc name:", doc_name)
    return doc_name
    

def get_formg_data(acc_numbers, num_of_filings=5):
    for i in range(num_of_filings):
        acc_stripped = acc_numbers[i].replace('-', '')
        primary_doc_name = get_primary_doc_url(acc_stripped)

        # Get the primary doc content
        url = f"{filing_baseurl}/{acc_stripped}/{primary_doc_name}"
        print("primary doc url", url)
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        text = soup.get_text(" ", strip=True) # extracting all the text from a page
        # print("file text", text) 
        #todo parse text

    return text


def construct_messages(file_text):
    # prepare the model input
    prompt_file = f"prompt.txt"
    folder = '.'
    with open(os.path.join(folder, prompt_file), "r") as f:
        system_prompt = f.read().strip()


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": file_text}
    ]
    return messages

def extract_data_llm(file_text):
    model_name = "Qwen/Qwen3-14B"

    # load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )

    messages = construct_messages(file_text)
    print("MESSAGES", messages)
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # conduct text completion
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=32768 # recommended output len for most queries
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

    # parsing thinking content
    try:
        # rindex finding 151668 (</think>)
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

    print("thinking content:", thinking_content)
    print("content:", content)
    return content


if __name__=="__main__":
    headers = {
        "User-Agent": "My Name my.email@gmail.com"
    }

    # Get the overall EDGAR json feed
    response = requests.get(submissions_url, headers=headers)
    if response.status_code == 200:
        submissions_json = json.loads(response.text)
        # pprint.pprint(submissions_json)
    else:
        print("Error:", response.status_code)

    recent_filings_df = pd.DataFrame(submissions_json['filings']['recent'])
    

    ## F13 XML parsing
    # thirteen_f = recent_filings_df.loc[recent_filings_df["form"] == "13F-HR"]
    # acc_f = list(thirteen_f["accessionNumber"])
    # data_f = get_f_data(acc_f)
    # df_f = pd.DataFrame(data_f)


    ### 13 G    
    thirteen_g = recent_filings_df.loc[recent_filings_df["form"].isin(["SC 13G/A", "SC 13G"])]
    acc_numbers = list(thirteen_g["accessionNumber"])

    file_text = get_formg_data(acc_numbers, 1)
    #todo make sure file_text was retrieved and valid -- error raising??

    extract_data_llm(file_text) # todo loop to do each separately


'''
https://www.crummy.com/software/BeautifulSoup/bs4/doc/
https://huggingface.co/Qwen/Qwen3-14B
'''