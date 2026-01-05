import csv
import re

def extract_cik_values(csv_file_path):
    """
    Extract all CIK values from a CSV file.
    
    Args:
        csv_file_path (str): Path to the CSV file
        
    Returns:
        list: List of CIK values
    """
    cik_values = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if 'CIK' in row:
                    cik_value = row['CIK']
                    # Clean the CIK value (remove quotes, spaces, etc.)
                    cik_value = cik_value.strip().strip('"\'')
                    
                    # Only add if it's not empty and is numeric
                    if cik_value and cik_value.isdigit():
                        cik_values.append(cik_value)
                        
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    return cik_values

def main():
    csv_file = '20260105.csv'
    
    print(f"Extracting CIK values from {csv_file}...")
    cik_values = extract_cik_values(csv_file)
    
    if cik_values:
        print(f"\nFound {len(cik_values)} CIK values:")
        for i, cik in enumerate(cik_values, 1):
            print(f"{i:3d}. {cik}")
        
        # Save to output file
        output_file = 'cik_values.txt'
        with open(output_file, 'w') as f:
            for cik in cik_values:
                f.write(f"{cik}\n")
        
        print(f"\nCIK values saved to '{output_file}'")
        print(f"Total CIK values extracted: {len(cik_values)}")
    else:
        print("No CIK values found or error occurred.")

if __name__ == "__main__":
    main()
