#!/usr/bin/env python3
"""
Transfer script to process CSV files from factCsv directory.
Processes financial facts data and outputs pivoted table format.
Output format: fact_name/unit | filed | value (pivoted by filing date)
"""
import sys
import pandas as pd
import os


def transfer_facts(csv_path: str):
    """Read a CSV file and create a pivoted table output."""
    try:
        df = pd.read_csv(csv_path)
        
        # Create unique identifier for each fact (fact_name + unit)
        df['fact_unit'] = df['fact_name'] + ' / ' + df['unit']
        
        # Pivot table: fact_unit as rows, filed as columns, value as values
        # Use aggregation for duplicates
        pivot_df = df.pivot_table(
            index='fact_unit',
            columns='filed',
            values='value',
            aggfunc='first'  # Take first value if duplicates
        )
        
        # Reset index to make fact_unit a column
        pivot_df = pivot_df.reset_index()
        
        # Get output filename
        base_name = os.path.splitext(csv_path)[0]
        output_path = base_name + '_t.csv'
        
        # Save to CSV
        pivot_df.to_csv(output_path, index=False)
        
        print(f"Successfully processed: {csv_path}")
        print(f"Total facts: {len(pivot_df)}")
        print(f"Filing dates: {len(pivot_df.columns) - 1}")
        print(f"Output saved to: {output_path}")
        
        # Show sample
        print("\nSample output (first 5 rows, first 5 columns):")
        print(pivot_df.iloc[:5, :5].to_string())
        
        return pivot_df
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python trasfer.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    df = transfer_facts(csv_file)
    
    if df is not None:
        print("\nTransfer completed successfully!")


if __name__ == "__main__":
    main()
