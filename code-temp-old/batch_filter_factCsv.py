#!/usr/bin/env python3
"""
Batch process all CSV files in factCsv directory using filter_fact_units.py logic.
Filters out fact_units that haven't been reported in the last 4 quarters.
"""

import csv
import os
import sys
from datetime import datetime, timedelta

# Current time as specified
CURRENT_DATE = datetime(2026, 1, 10)

# Last 4 quarters threshold (approximately 1 year back)
THRESHOLD_DATE = CURRENT_DATE - timedelta(days=365)


def is_stale(data_value):
    """Check if a data value is empty/blank."""
    return data_value == '' or data_value is None


def filter_csv_file(csv_path: str):
    """Filter a single CSV file to remove stale fact_units."""
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            rows = list(reader)
        
        if not rows:
            print(f"  [SKIP] File is empty: {csv_path}")
            return 0, 0
        
        # Header row contains dates
        header = rows[0]
        dates = header[1:]  # Skip the 'fact_unit' column
        
        # Find the indices of the last 4 quarters (columns)
        last_4_quarter_indices = list(range(len(dates) - 4, len(dates)))
        
        # Process data rows
        cleaned_rows = [header]  # Keep header
        removed_count = 0
        kept_count = 0
        
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
                kept_count += 1
            else:
                removed_count += 1
        
        # Write the cleaned data back to the original file
        with open(csv_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(cleaned_rows)
        
        return kept_count, removed_count
        
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 0, 0


def process_all_files_in_directory(directory: str):
    """Process all CSV files in the specified directory."""
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    print(f"Found {len(csv_files)} CSV files in {directory}")
    print("-" * 50)
    
    total_kept = 0
    total_removed = 0
    error_count = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        csv_path = os.path.join(directory, csv_file)
        print(f"[{i}/{len(csv_files)}] Processing: {csv_file}")
        
        kept, removed = filter_csv_file(csv_path)
        
        if kept > 0 or removed > 0:
            total_kept += kept
            total_removed += removed
            print(f"  [OK] Kept: {kept}, Removed: {removed}")
        else:
            error_count += 1
    
    print("\n" + "=" * 50)
    print(f"Processing complete!")
    print(f"  Total kept: {total_kept}")
    print(f"  Total removed: {total_removed}")
    print(f"  Errors: {error_count}")
    print(f"  Total files: {len(csv_files)}")


def main():
    # Default to factCsv directory
    directory = "factCsv"
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)
    
    process_all_files_in_directory(directory)


if __name__ == "__main__":
    main()
