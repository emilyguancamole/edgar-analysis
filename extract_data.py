import requests
import json
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "9"


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
                    "report_date": root.findtext("ns1:periodOfReport", namespaces=ns),
                    "issuer": infotable.findtext("ns1:nameOfIssuer", namespaces=ns), #* findtext: Find text for first matching element by tag name or path
                    "class": infotable.findtext("ns1:titleOfClass", namespaces=ns),
                    "cusip": infotable.findtext("ns1:cusip", namespaces=ns),
                    "figi": infotable.findtext("ns1:figi", namespaces=ns),
                    "value": int(infotable.findtext("ns1:value", default=-1, namespaces=ns)),
                    "shares_owned": int(infotable.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamt", default=-1, namespaces=ns)), # shares or principal amount
                    "share_type": infotable.findtext("ns1:shrsOrPrnAmt/ns1:sshPrnamtType", namespaces=ns),
                    "discretion": infotable.findtext("ns1:investmentDiscretion", namespaces=ns),
                    "voting_sole": infotable.findtext("ns1:votingAuthority/ns1:Sole", namespaces=ns),
                    "voting_shared": infotable.findtext("ns1:votingAuthority/ns1:Shared", namespaces=ns),
                    "voting_none": infotable.findtext("ns1:votingAuthority/ns1:None", namespaces=ns),
                    "url": f"{filing_baseurl}/{acc_stripped}/{info_file}",
                }
                data.append(entry)
    
    except Exception as e:
        print("Error:", e)
    
    return data


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
    

def get_formg_text(acc_number):
    acc_stripped = acc_number.replace('-', '')
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
    messages = construct_messages(file_text)
    print("MESSAGES", messages)
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    print("\nGenerating...\n")
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
    llm_response = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

    print("thinking content:", thinking_content)
    print("content:", llm_response)
    return llm_response


def extract_all_data_llm(acc_numbers, num_of_filings) -> list:
    ''' Loop through each filing and extract data using LLM. 
    Save results to a list of dicts.'''
    all_data = []
    for i in range(num_of_filings):
        file_text = get_formg_text(acc_numbers[i])
        llm_response = extract_data_llm(file_text)

        # using built-in json validation 
        # # todo pydantic validation, then pass invalid json + correction prompt to llm again. Write tests for this
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            print("LLM response was not valid JSON.")

        print("Extracted data:", data)
        all_data.append(data)
    return all_data

def save_llm_data(data: list, save_path="extracted_13g_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(save_path, index=False)
    print("Data saved to ", save_path)


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
    

    ### F13 XML parsing
    thirteen_f = recent_filings_df.loc[recent_filings_df["form"] == "13F-HR"]
    acc_f = list(thirteen_f["accessionNumber"])
    data_f = get_f_data(acc_f)
    df_f = pd.DataFrame(data_f)
    # write to csv for now
    df_f.to_csv("extracted_13f_data.csv", index=False)


    ### 13 G    
    model_name = "Qwen/Qwen3-14B"
    # load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )

    thirteen_g = recent_filings_df.loc[recent_filings_df["form"].isin(["SC 13G/A", "SC 13G"])]
    acc_numbers = list(thirteen_g["accessionNumber"])

    llm_response = extract_all_data_llm(acc_numbers, 5)
    save_llm_data(llm_response, "extracted_13g_data.csv")


'''
https://www.crummy.com/software/BeautifulSoup/bs4/doc/
https://huggingface.co/Qwen/Qwen3-14B
'''