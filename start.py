import requests

CIK_FULL = "CIK0000763212"
CIK_STRIPPED = "763212"
submissions_url = "https://data.sec.gov/submissions/${CIK_FULL}.json"
filing_baseurl = "https://www.sec.gov/Archives/edgar/data/${CIK_STRIPPED}/"

submissions = requests.get(submissions_url)

def fetchSubmissions():
    try:
        submissions = await fetch(submissions_url, {
            headers: {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35" // https://www.useragentlist.net/
            }


const data = await fetchSubmissions();

const extract13F = async (data) => {
    // if (data && Arrat.isArray(data))
    // Filter form for "13F-HR" or "SC 13G/A".
    // data.filings.recent.form == "13F-HR" 
    df.loc[df["Form"] == "13F-HR"]["accessionNUmber"]
}


// # Grab accession number for the filing
// # 

// Go to filing index.json to list all attached files.

// Pull the relevant exhibit (XML for 13F, text/HTML for 13G/A).

// Parse + extract.

