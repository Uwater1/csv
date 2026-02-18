# Financial Data Processing Pipeline

## Structure

- `code-temp-old/`: Contains input CSV files with stock symbols
- `factCsv/`: Contains processed financial data
- `price/`: Contains downloaded historical price data (one CSV per symbol)
- `download_yfinance.py`: Script to download data from yfinance
- `research_bottoms_v4.py`: Script to identify bottom patterns, as an example alpha