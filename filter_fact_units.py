#!/usr/bin/env python3
"""
Script to remove fact_units from Apple_Inc_t.csv that haven't been reported 
in the last 4 quarters (approximately 1 year back from now).
"""

import csv
from datetime import datetime, timedelta

# Current time as specified
CURRENT_DATE = datetime(2026, 1, 10)

# Last 4 quarters threshold (approximately 1 year back)
# The dates in the CSV are quarterly, so we look at the last 4 columns
THRESHOLD_DATE = CURRENT_DATE - timedelta(days=365)

INPUT_FILE = 'code-temp/Apple_Inc_t.csv'

def is_stale(data_value):
    """Check if a data value is empty/blank."""
    return data_value == '' or data_value is None

def main():
    with open(INPUT_FILE, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        rows = list(reader)
    
    if not rows:
        print("File is empty")
        return
    
    # Header row contains dates
    header = rows[0]
    dates = header[1:]  # Skip the 'fact_unit' column
    
    # Find the indices of the last 4 quarters (columns)
    # We'll use the last 4 columns that contain dates
    last_4_quarter_indices = list(range(len(dates) - 4, len(dates)))
    print(f"Last 4 quarters columns: {last_4_quarter_indices}")
    print(f"Dates: {[dates[i] for i in last_4_quarter_indices]}")
    
    # Process data rows
    cleaned_rows = [header]  # Keep header
    removed_count = 0
    
    for row in rows[1:]:
        fact_unit = row[0]
        
        # Check values in the last 4 quarters
        has_data_in_last_4_quarters = False
        for idx in last_4_quarter_indices:
            if idx < len(row):
                value = row[idx]
                if not is_stale(value):
                    has_data_in_last_4_quarters = True
                    break
        
        if has_data_in_last_4_quarters:
            cleaned_rows.append(row)
        else:
            print(f"Removing fact_unit with no data in last 4 quarters: {fact_unit}")
            removed_count += 1
    
    print(f"\nRemoved {removed_count} fact_units with no data in the last 4 quarters")
    
    # Write the cleaned data back to the original file
    with open(INPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(cleaned_rows)
    
    print(f"Output written to {INPUT_FILE}")

if __name__ == '__main__':
    main()
