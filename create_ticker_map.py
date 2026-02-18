import pandas as pd
import os
import re
import json

def normalize(name):
    # Remove extension if present
    if name.endswith('.csv'):
        name = name[:-4]

    # Remove special characters and spaces, convert to lower
    return re.sub(r'[^a-z0-9]', '', name.lower())

def main():
    csv_path = 'code-temp-old/20260105.csv'
    fact_dir = 'factCsv'
    output_file = 'ticker_map.json'

    if not os.path.exists(csv_path) or not os.path.exists(fact_dir):
        print("Files not found")
        return

    # Load fact files
    fact_files = os.listdir(fact_dir)
    fact_map = {} # normalized -> original_filename
    for f in fact_files:
        if f.endswith('.csv'):
            norm = normalize(f)
            fact_map[norm] = f

    # Load tickers
    df = pd.read_csv(csv_path)

    ticker_to_file = {}

    matched_count = 0
    total_count = 0

    for index, row in df.iterrows():
        ticker = row['Symbol']
        company = row['Security']
        total_count += 1

        norm_company = normalize(company)

        # Strategy 1: Exact match of normalized names
        if norm_company in fact_map:
            ticker_to_file[ticker] = fact_map[norm_company]
            matched_count += 1
            continue

        # Strategy 2: Filename starts with company name (e.g. 3M vs 3m_Company)
        # or Company name starts with filename
        match = None
        for fact_norm, fact_file in fact_map.items():
            if norm_company.startswith(fact_norm) or fact_norm.startswith(norm_company):
                 match = fact_file
                 break

        if match:
            ticker_to_file[ticker] = match
            matched_count += 1
            continue

        # Strategy 3: Match first word
        first_word = normalize(company.split(' ')[0])
        match = None
        for fact_norm, fact_file in fact_map.items():
             if fact_norm.startswith(first_word):
                 match = fact_file
                 break

        if match:
            # print(f"Weak match: {ticker} ({company}) -> {match}")
            ticker_to_file[ticker] = match
            matched_count += 1
            continue

        # print(f"No match for {ticker} ({company})")

    print(f"Mapped {matched_count}/{total_count} tickers.")

    with open(output_file, 'w') as f:
        json.dump(ticker_to_file, f, indent=4)

    print(f"Saved mapping to {output_file}")

if __name__ == '__main__':
    main()
