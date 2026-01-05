import os
import shutil
import sys
from pathlib import Path

def extract_cik_files(cik_file, source_dir, target_folder):
    # Create target folder if it doesn't exist
    os.makedirs(target_folder, exist_ok=True)
    
    # Read CIK values
    with open(cik_file, 'r') as f:
        cik_values = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(cik_values)} CIK values to match from {cik_file}")
    
    # Search for matching files
    matched_files = []
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.startswith("CIK") and file.endswith(".json"):
                # Extract CIK number from filename
                # Format: CIK0000356676.json or CIK0000356682-submissions-001.json
                cik_part = file[3:]  # Remove "CIK" prefix
                cik_number = cik_part.split("-")[0]  # Get part before any dash
                cik_number = cik_number.split(".")[0]  # Remove .json if no dash
                cik_number = cik_number.lstrip('0')  # Remove leading zeros
                
                if cik_number in cik_values:
                    source_path = os.path.join(root, file)
                    matched_files.append((source_path, file))
                    print(f"Matched: {file} (CIK: {cik_number})")
    
    print(f"\nFound {len(matched_files)} matching files")
    
    # Copy matched files to target folder
    for source_path, filename in matched_files:
        target_path = os.path.join(target_folder, filename)
        shutil.copy2(source_path, target_path)
        print(f"Copied: {filename} -> {target_folder}")
    
    print(f"\nExtraction complete. {len(matched_files)} files copied to '{target_folder}' folder.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_cik_files.py <cik_list_file> <source_folder> <target_folder>")
        print("Example: python extract_cik_files.py cik_values.txt . extracted_cik_files")
        sys.exit(1)
    
    cik_file = sys.argv[1]
    source_dir = sys.argv[2]
    target_folder = sys.argv[3]
    
    # Check if cik file exists
    if not os.path.exists(cik_file):
        print(f"Error: CIK file '{cik_file}' not found")
        sys.exit(1)
    
    # Check if source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' not found")
        sys.exit(1)
    
    extract_cik_files(cik_file, source_dir, target_folder)
