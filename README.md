# EDGAR Analysis

This ongoing project parses and analyzes data from SEC EDGAR filings. It specifically focuses on Form 13F and Form 13G/A filings, with modules for fetching filings from EDGAR. It parses the filings, either with XML parsing OR using an LLM (currently Qwen 14B). LLM-extracted data is validated against predefined data models. The data are loaded into PostgreSQL database tables for further analysis.

Next steps: 
- Incorporate stock prices into time-series analysis of institutional holdings. 
- Add dashboard visualizations and analysis of institutional investment trends.
- Optimize LLM inference speed and accuracy.