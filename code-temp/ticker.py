import pandas as pd
import yfinance as yf
import os

# 1. Get the current S&P 500 list from Wikipedia
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    df = table[0]
    # Some tickers use '.' instead of '-' (e.g., BRK.B), yfinance prefers '-'
    tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
    return tickers

if __name__ == "__main__":
    get_sp500_tickers()