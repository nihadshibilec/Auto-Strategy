import pandas as pd
import pandas_ta as ta

def get_rsi_upper_entries(market_data, threshold):
    market_data['RSI'] = ta.rsi(market_data['close'], length=14)
    Entries = market_data[market_data['RSI'] >= threshold].copy()  # Use copy to avoid modifying original DataFrame
    print("RSI Upper, Found", len(Entries), "Entries")
    return Entries
