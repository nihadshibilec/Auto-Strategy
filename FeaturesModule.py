import pandas as pd

def add_volume_shocker(Entries, market_data, threshold):
    market_data["avg_volume"] = market_data["volume"].rolling(window=50).mean()
    market_data['Volume Times'] = market_data['volume'] / market_data['avg_volume']
    market_data = market_data[market_data['Volume Times'] >= threshold]
    
    merged_df = pd.merge(Entries, market_data[['date', 'Volume Times']], on='date', how='inner')
    print("Added Volume Shocker, Found", len(merged_df), "Entries")
    return merged_df

def add_volatility_pct(Entries, market_data, threshold):
    market_data['change'] = (market_data['high'] - market_data['low']) / market_data['low']
    market_data = market_data[market_data['change'] >= threshold]
    
    merged_df = pd.merge(Entries, market_data[['date', 'change']], on='date', how='inner')
    print("Added Volatility pct, Found", len(merged_df), "Entries")
    return merged_df

def add_macd_upper(Entries, market_data, threshold):
    market_data['MACD_12_26_9'] = market_data.ta.macd(append=True)['MACD_12_26_9']
    market_data = market_data[market_data['MACD_12_26_9'] >= threshold]
    
    merged_df = pd.merge(Entries, market_data[['date', 'MACD_12_26_9']], on='date', how='inner')
    print("Added MACD, Found", len(merged_df), "Entries")
    return merged_df

