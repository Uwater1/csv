import csv

def get_symbols_from_csv(filename, symbol_column):
    """Extract symbols from a CSV file"""
    symbols = set()
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if symbol_column in row:
                    symbol = row[symbol_column].strip()
                    if symbol:
                        symbols.add(symbol)
                        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return set()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return set()
    
    return symbols

def compare_symbols():
    """Compare symbols between nq100.csv and 20260105.csv"""
    
    # Get symbols from both files
    nq100_symbols = get_symbols_from_csv('nq100.csv', 'Symbol')
    sp500_symbols = get_symbols_from_csv('20260105.csv', 'Symbol')
    
    print(f"Found {len(nq100_symbols)} symbols in nq100.csv")
    print(f"Found {len(sp500_symbols)} symbols in 20260105.csv")
    
    # Find symbols in nq100 but not in 20260105
    unique_to_nq100 = nq100_symbols - sp500_symbols
    
    # Find symbols in 20260105 but not in nq100
    unique_to_sp = sp500_symbols - nq100_symbols
    
    # Find common symbols
    common_symbols = nq100_symbols & sp500_symbols
    
    print(f"\n=== SYMBOLS IN nq100.csv BUT NOT IN 20260105.csv ===")
    print(f"Count: {len(unique_to_nq100)}")
    
    if unique_to_nq100:
        # Sort alphabetically for better readability
        sorted_unique = sorted(unique_to_nq100)
        for i, symbol in enumerate(sorted_unique, 1):
            print(f"{i:2d}. {symbol}")
    else:
        print("None")
    
    print(f"\n=== SYMBOLS IN 20260105.csv BUT NOT IN nq100.csv ===")
    print(f"Count: {len(unique_to_sp)}")
    
    if unique_to_sp:
        # Sort alphabetically
        sorted_unique_sp = sorted(unique_to_sp)
        for i, symbol in enumerate(sorted_unique_sp[:20], 1):  # Show first 20
            print(f"{i:2d}. {symbol}")
        if len(unique_to_sp) > 20:
            print(f"... and {len(unique_to_sp) - 20} more")
    else:
        print("None")
    
    print(f"\n=== COMMON SYMBOLS ===")
    print(f"Count: {len(common_symbols)}")
    
    # Save the unique symbols to a file
    if unique_to_nq100:
        with open('nq100_unique_symbols.txt', 'w') as f:
            for symbol in sorted(unique_to_nq100):
                f.write(f"{symbol}\n")
        print(f"\nUnique nq100 symbols saved to 'nq100_unique_symbols.txt'")
    
    return unique_to_nq100, unique_to_sp, common_symbols

def main():
    print("Comparing symbols between nq100.csv and 20260105.csv...")
    print("=" * 60)
    
    unique_to_nq100, unique_to_sp, common_symbols = compare_symbols()
    
    print(f"\n=== SUMMARY ===")
    print(f"NASDAQ 100 unique symbols: {len(unique_to_nq100)}")
    print(f"S&P 500 unique symbols: {len(unique_to_sp)}")
    print(f"Common symbols: {len(common_symbols)}")
    print(f"Total unique symbols across both: {len(unique_to_nq100 | unique_to_sp | common_symbols)}")

if __name__ == "__main__":
    main()
