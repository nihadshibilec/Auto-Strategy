import pandas as pd
from tqdm import tqdm

def exit_optimizer(entries, market_data, capital_per_trade, exit_time):
    pd.set_option('mode.chained_assignment', None)  # Disable warning
    market_data = market_data.reset_index()
    all_trades = pd.DataFrame()
    charges_per_trade = capital_per_trade * 0.002
    data = market_data.copy()
    
    for index, entry_row in tqdm(entries.iterrows(), total=len(entries), desc="Exit Optimizer: ", ncols=150):
        entry_time = pd.to_datetime(entry_row["date"])
        entry_price = entry_row["close"]
        eod = pd.to_datetime(entry_time.strftime("%Y-%m-%d") + " " + exit_time) # swing
        
        df = data[(data["date"] >= entry_time) & (data["date"] < eod)]
        volume = round((capital_per_trade * 5) / entry_price)

        target = 1.0020
        stop_loss = 0.9980
        target_values = [round(target + (i / 1000), 4) for i in range(0, 30, 1)]
        stop_loss_values = [round(stop_loss - (i / 1000), 4) for i in range(0, 30, 1)]
        trades = []

        target_check = 0
        reached_target = False
        reached_stop_loss = False
        
        for stop_loss_value in stop_loss_values:
            stop_loss_price = round(entry_price * stop_loss_value, 1)
            reached_target = False
            
            for target_value in target_values:
                if target_check >= target_value:
                    continue
                
                target_price = round(entry_price * target_value, 1)
                row_index = 0
                
                while row_index < len(df):
                    row = df.iloc[row_index]    
                    high = row["high"]
                    low = row["low"]
                    close = row["close"]
                    exit_date = row["date"]

                    if row_index == len(df) - 1:
                        pnl = ((close - entry_price) * volume)
                        for stop_loss_value2 in stop_loss_values:
                            if stop_loss_value2 > stop_loss_value:
                                continue
                            for target_value2 in target_values:
                                if target_value2 < target_value:
                                    continue
                                trades.append((entry_time, entry_price, exit_date, close, volume, stop_loss_value2, target_value2, pnl))

                        reached_target = True
                        reached_stop_loss = True
                        break
                    elif high >= target_price:
                        target_check = target_value
                        pnl = ((target_price - entry_price) * volume)
                        for stop_loss_value2 in stop_loss_values:
                            if stop_loss_value2 > stop_loss_value:
                                continue
                            trades.append((entry_time, entry_price, exit_date, target_price, volume, stop_loss_value2, target_value, pnl))
                        break
                    elif low <= stop_loss_price:
                        pnl = ((stop_loss_price - entry_price) * volume)
                        for target_value2 in target_values:
                            if target_value2 < target_value:
                                continue
                            trades.append((entry_time, entry_price, exit_date, stop_loss_price, volume, stop_loss_value, target_value2, pnl))
                        reached_target = True
                        break
                    row_index += 1

                if reached_target:
                    break
            if reached_stop_loss:
                break

        temp_trades_df = pd.DataFrame(trades)
        all_trades = pd.concat([all_trades, temp_trades_df])

    sorted_trades = all_trades.sort_values(by=[2])
    sorted_trades = sorted_trades.reset_index(drop=True)
    sorted_trades.columns = ['Entry Date', 'Entry Price', 'Exit Date', 'Exit Price', 'Quantity', 'Stoploss', 'Target', 'PnL']
    buy_optimized = sorted_trades.copy()
    sell_optimized = sorted_trades.copy()
    sell_optimized['PnL'] = sell_optimized['PnL'] * -1
    
    #####Charges ######
    buy_optimized['PAT'] = buy_optimized['PnL'] - charges_per_trade
    sell_optimized['PAT'] = sell_optimized['PnL'] - charges_per_trade
    
    return buy_optimized, sell_optimized
