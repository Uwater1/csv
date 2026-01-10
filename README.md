# Financial Data Processing Pipeline

This repository contains a comprehensive pipeline for collecting, processing, and transforming financial data from multiple sources including SEC EDGAR filings and stock price data.

## Overview

The pipeline processes financial facts data from SEC EDGAR database and stock price data from Yahoo Finance, transforming raw JSON data into structured CSV formats suitable for analysis.

## Data Sources

- **SEC EDGAR**: Company financial facts data in JSON format
- **Yahoo Finance**: Historical stock price data
- **Wikipedia**: S&P 500 ticker symbols
- **NASDAQ 100**: Pre-defined list of technology companies

## Pipeline Steps

### 1. Symbol Collection and Preparation

#### `code-temp/ticker.py`
- Scrapes S&P 500 ticker symbols from Wikipedia
- Handles ticker format conversions (e.g., BRK.B → BRK-B for yfinance compatibility)

#### `code-temp/create_full_nq100.py`
- Creates complete NASDAQ 100 dataset with 101 companies
- Includes company rankings, weights, and current market data
- Converts tab-separated text to structured CSV format

#### `code-temp/convert_nq100.py`
- Converts NASDAQ 100 data from text format to CSV
- Handles data cleaning (removes commas from prices, extracts percentages)

#### `code-temp/compare_symbols.py`
- Compares symbols between NASDAQ 100 and S&P 500 datasets
- Identifies unique symbols in each dataset
- Saves NASDAQ 100 unique symbols to `nq100_unique_symbols.txt`

#### `code-temp/extract_cik.py`
- Extracts CIK (Central Index Key) values from CSV files
- CIK values are used to identify companies in SEC filings
- Saves extracted CIKs to `cik_values.txt`

### 2. Stock Price Data Download

#### `download_yfinance.py`
- Downloads historical stock price data using yfinance library
- Reads symbols from `code-temp/nq100_unique_symbols.txt` and `code-temp/20260105.csv`
- Downloads 10 years of daily data for each symbol
- Saves individual CSV files to `price/` directory
- Includes rate limiting to avoid API restrictions

### 3. SEC EDGAR Data Extraction

#### `extract_cik_files.py`
- Filters SEC EDGAR JSON files based on CIK values
- Copies matching files from source directory to `facts/` directory
- Handles various filename formats (CIK0000356676.json, CIK0000356682-submissions-001.json)

#### `extract.py`
- Processes individual SEC EDGAR facts JSON files
- Extracts financial facts data into structured CSV format
- Creates columns: taxonomy, fact_name, unit, value, start, end, fy, fp, form, filed, frame, decimals
- Sanitizes company names for safe filenames

#### `batch_extract.py`
- Batch processes all JSON files in `facts/` directory
- Applies `extract.py` logic to multiple files
- Outputs processed CSVs to `factCsv/` directory
- Provides processing statistics and error handling

### 4. Data Transformation

#### `trasfer.py` (transfer.py)
- Transforms raw facts CSV into pivoted table format
- Creates `fact_unit` column combining fact_name and unit
- Pivots data so filing dates become columns, fact_units become rows
- Uses aggregation to handle duplicate entries
- Outputs `_t.csv` files (e.g., `Apple_Inc_t.csv`)

### 5. Data Filtering

#### `filter_fact_units.py`
- Filters transformed CSV files to remove outdated fact_units
- Identifies last 4 quarters based on current date (2026-01-10)
- Removes fact_units with no data in recent quarters
- Cleans CSV by removing empty rows, resulting in more focused datasets

## Directory Structure

```
csv/
├── batch_extract.py              # Batch JSON to CSV conversion
├── cik_values.txt               # Extracted CIK values
├── download_yfinance.py         # Stock price data downloader
├── extract.py                   # Single JSON to CSV converter
├── extract_cik_files.py         # CIK-based file filtering
├── filter_fact_units.py         # Recent data filter
├── trasfer.py                   # Data pivoting transformation
├── LICENSE
├── list.txt
├── README.md
├── requirements.txt
code-temp/
├── 20260105.csv                # S&P 500 data
├── Apple_Inc_t.csv             # Processed Apple facts (example)
├── compare_symbols.py          # Symbol comparison utility
├── convert_nq100.py            # NASDAQ 100 format converter
├── create_full_nq100.py        # NASDAQ 100 data generator
├── extract_cik.py              # CIK extraction utility
├── extract_cik_files.py        # CIK file extractor
├── nq100.csv                   # NASDAQ 100 companies
├── nq100.txt                   # NASDAQ 100 raw data
├── nq100_unique_symbols.txt    # Unique NASDAQ symbols
├── sample_nq100.csv            # Sample NASDAQ data
├── sample_nq100.txt            # Sample NASDAQ raw data
├── ticker.py                   # S&P 500 ticker scraper
csv/
├── BATS_AAPL, 3.csv           # Stock data samples
├── BATS_AMAT, 3.csv
├── ...
factCsv/
├── Apple_Inc.csv              # Raw Apple facts
├── Microsoft.csv              # Raw Microsoft facts
├── ...                        # Other company facts
facts/
├── CIK0000002488_facts.csv    # Raw SEC JSON data
price/
├── AAPL.csv                   # Apple stock prices
├── MSFT.csv                   # Microsoft stock prices
├── ...                        # Other stock price data
```

## Usage

### Prerequisites
- Python 3.7+
- Required packages: pandas, yfinance, requests

### Running the Pipeline

1. **Extract CIK values:**
   ```bash
   python code-temp/extract_cik.py
   ```

2. **Extract relevant SEC files:**
   ```bash
   python extract_cik_files.py cik_values.txt /path/to/sec/data facts
   ```

3. **Batch process facts data:**
   ```bash
   python batch_extract.py
   ```

4. **Transform data format:**
   ```bash
   python trasfer.py factCsv/Apple_Inc.csv
   ```

5. **Filter recent data:**
   ```bash
   python filter_fact_units.py
   ```

6. **Download stock prices:**
   ```bash
   python download_yfinance.py
   ```

## Data Formats

### Raw Facts CSV
```
taxonomy,fact_name,unit,value,start,end,fy,fp,form,filed,frame,decimals
us-gaap,AccountsPayableCurrent,USD,1000000,2023-01-01,2023-03-31,2023,Q1,10-Q,2023-05-01,,2
```

### Transformed Pivoted CSV
```
fact_unit,2023-02-01,2023-05-01,2023-08-01,2023-11-01,2024-02-01,...
AccountsPayableCurrent / USD,1000000,1100000,1200000,1300000,1400000,...
```

### Filtered CSV
Contains only fact_units with data in the last 4 quarters, removing outdated or inactive metrics.

## Notes

- Current date context: 2026-01-10 (used for filtering recent quarters)
- NASDAQ 100 data includes 101 companies with market weights
- SEC data processing handles various filing forms (10-K, 10-Q, 8-K)
- Stock price data covers 10-year historical period with daily granularity
- Error handling included for API rate limits and missing data
