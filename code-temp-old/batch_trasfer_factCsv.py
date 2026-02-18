#!/usr/bin/env python3
"""
Batch process all CSV files in factCsv directory using trasfer.py logic.
Processes each file and replaces the original.
"""
import os
import sys
import pandas as pd

# Add current directory to path to import trasfer module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trasfer import transfer_facts


def process_all_files_in_directory(directory: str):
    """Process all CSV files in the specified directory."""
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    print(f"Found {len(csv_files)} CSV files in {directory}")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        csv_path = os.path.join(directory, csv_file)
        print(f"\n[{i}/{len(csv_files)}] Processing: {csv_file}")
        
        try:
            result = transfer_facts(csv_path)
            if result is not None:
                success_count += 1
                print(f"  [OK] Success: {len(result)} facts processed")
            else:
                error_count += 1
                print(f"  [FAIL] Failed to process")
        except Exception as e:
            error_count += 1
            print(f"  [FAIL] Error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Processing complete!")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(csv_files)}")


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
