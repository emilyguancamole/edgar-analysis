CIK 0000763212
forms: 13F-HR, SC 13G/A
- Form 13F: quarterly equity holdings of institutional investment managers with $100M+
- Schedule 13D?: beneficial ownership exceeding 5% of a company’s voting shares

SEC has JSON feeds for EDGAR. 
Submissions feed for PRIMECAP: https://data.sec.gov/submissions/CIK0000763212.json

Each filing has a unique accession number.

URL pattern for filing JSON: https://www.sec.gov/Archives/edgar/data/763212/{accession_number_no_dashes}/index.json
                                                                        /{filename}
- The index.json for a filing gives you all the exhibits, including the XML info table.
- Pull the relevant exhibit (infotable.xml for 13F, text/HTML for 13G/A).

filings.
    recent.
        accessionNumber
        act
        form
        fileNumber

13G/A files:
- 0001085146-24-005545-index-headers.html → EDGAR-generated header table (meta info)
- 0001085146-24-005545-index.html → Filing documents index page (the one you see in browser)
- 0001085146-24-005545.txt → The raw complete filing text 
- nxt_111124.htm → The actual filing documen