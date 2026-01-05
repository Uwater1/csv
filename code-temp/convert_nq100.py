import re
import csv

def convert_nq100_to_csv(input_file, output_file):
    """
    Convert nq100.txt to nq100.csv format.
    
    Args:
        input_file (str): Path to input text file
        output_file (str): Path to output CSV file
    """
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            csv_writer = csv.writer(outfile)
            
            # Write CSV header
            csv_writer.writerow(['Rank', 'Company', 'Symbol', 'Weight', 'Price', 'Change', 'Percent_Change'])
            
            # Read and process each line
            for line in infile:
                line = line.strip()
                
                # Skip empty lines and header line
                if not line or line.startswith('#') or 'Company' in line:
                    continue
                
                # Parse the line using regex to handle tab-separated values
                # Pattern: Rank<tab>Company<tab>Symbol<tab>Weight<tab>Price<tab>Chg<tab>% Chg
                parts = line.split('\t')
                
                if len(parts) >= 7:
                    rank = parts[0].strip()
                    company = parts[1].strip()
                    symbol = parts[2].strip()
                    weight = parts[3].strip()
                    price = parts[4].strip()
                    change = parts[5].strip()
                    percent_change = parts[6].strip()
                    
                    # Clean up the data
                    # Remove commas from price and convert to float
                    price = price.replace(',', '')
                    
                    # Extract numeric values from weight (remove %)
                    weight = weight.replace('%', '')
                    
                    # Extract numeric values from percent change
                    percent_change = percent_change.replace('(', '').replace(')', '').replace('%', '')
                    
                    # Write to CSV
                    csv_writer.writerow([rank, company, symbol, weight, price, change, percent_change])
                    
        print(f"Successfully converted {input_file} to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error during conversion: {e}")

def main():
    input_file = 'nq100.txt'
    output_file = 'nq100.csv'
    
    print(f"Converting {input_file} to {output_file}...")
    
    # Check if input file exists and has content
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"Warning: {input_file} is empty. Creating sample data...")
                create_sample_data(input_file)
    except FileNotFoundError:
        print(f"Warning: {input_file} not found. Creating sample data...")
        create_sample_data(input_file)
    
    convert_nq100_to_csv(input_file, output_file)
    
    # Display first few lines of the converted CSV
    try:
        with open(output_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            print("\nFirst 5 lines of converted CSV:")
            for i, row in enumerate(reader):
                if i < 5:
                    print(f"Row {i+1}: {row}")
                else:
                    break
    except FileNotFoundError:
        print(f"Could not read output file {output_file}")

def create_sample_data(filename):
    """Create sample nq100 data if file doesn't exist or is empty"""
    sample_data = """#	Company	Symbol	Weight	      Price	Chg	% Chg	
1	Nvidia	NVDA	13.74%	   190.29	1.44	(0.76%)	
2	Apple Inc.	AAPL	11.81%	   269.10	-1.91	(-0.71%)	
3	Microsoft	MSFT	10.43%	   472.19	-0.75	(-0.16%)	
4	Amazon	AMZN	7.36%	   231.88	5.38	(2.38%)	
5	Alphabet Inc. (Class A)	GOOGL	5.88%	   316.70	1.55	(0.49%)	
6	Alphabet Inc. (Class C)	GOOG	5.48%	   317.19	1.87	(0.59%)	
7	Meta Platforms	META	4.95%	   660.99	10.58	(1.63%)	
8	Broadcom Inc.	AVGO	4.83%	   343.06	-4.56	(-1.31%)	
9	Tesla, Inc.	TSLA	4.50%	   455.01	16.94	(3.87%)	
10	ASML Holding	ASML	1.42%	   1,228.89	65.11	(5.59%)"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(sample_data)
    print(f"Created sample data in {filename}")

if __name__ == "__main__":
    main()
