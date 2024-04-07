import pandas as pd
import numpy as np
from tqdm import tqdm

class ExitCaseAnalyzer:
    def __init__(self, exit_optimizer, entry_type, market_data):
        self.exit_optimizer = exit_optimizer
        self.entry_type = entry_type
        self.market_data = market_data
    
    def analyze_exit_variations(self):
        report = self.generate_exit_variations_report()
        report = self.select_best_exit_cases(report)
        return report

    @staticmethod
    def convert_timeframe(timeframe,data):
        data.set_index('date', inplace=True)
        Candle_data = data.resample(timeframe).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        Candle_data.reset_index(inplace=True)
        Candle_data.set_index('date', inplace=True) 
        Candle_data.dropna(subset=['close'], inplace=True)
        Candle_data.reset_index(inplace=True)
        return Candle_data
    
    @staticmethod
    def max_drawdown_value(trades, pnl_column_name):
        trades = trades.sort_values('Entry Date').reset_index(drop=True)
        trades['cumulative_pnl'] = trades[pnl_column_name].cumsum()
        drawdown = trades['cumulative_pnl'] - trades['cumulative_pnl'].cummax()
        max_drawdown = drawdown.min() 
        return max_drawdown

    def generate_exit_variations_report(self):
        trades = self.exit_optimizer.copy()
        trades["Entry Date"] = pd.to_datetime(trades["Entry Date"])
        trades["Exit Date"] = pd.to_datetime(trades["Exit Date"])
        
        target_values = [round(1.002 + (i/1000), 4) for i in range(0, 30, 1)]
        stop_loss_values = [round(0.998 - (i/1000), 4) for i in range(0, 30, 1)]
        final_report = []

        for stop_loss in tqdm(stop_loss_values, desc="Exit Cases:", total=len(stop_loss_values), ncols=150):
            for target in target_values:
                temp_trades = trades[(trades["Target"]==target) & (trades["Stoploss"]==stop_loss)]
                if temp_trades.empty:
                    continue
                
                pnl_main = temp_trades["PAT"].sum()
                no_of_trades = len(temp_trades)
                winrate = (temp_trades["PAT"] > 0).mean()
                avg_ratio = temp_trades[temp_trades['PAT'] > 0]['PAT'].mean() / -temp_trades[temp_trades['PAT'] <= 0]['PAT'].mean()
                positive_pnl_sum = temp_trades[temp_trades['PAT'] > 0]['PAT'].sum()
                negative_pnl_sum = temp_trades[temp_trades['PAT'] < 0]['PAT'].sum()
                pf = positive_pnl_sum / -negative_pnl_sum if negative_pnl_sum != 0 else float('inf')
                rr = (target - 1) / (1 - stop_loss) if self.entry_type == 'buy' else (1 - stop_loss) / (target - 1)
                max_dd = self.max_drawdown_value(temp_trades, "PAT")
                sharp_ratio = pnl_main / -max_dd if max_dd != 0 else np.nan

                final_report.append((stop_loss, target, pnl_main, max_dd, winrate, avg_ratio, rr, pf, sharp_ratio, no_of_trades))

        report_columns = ["Stoploss", "Target", "PAT", "Max DD", "Winrate", "Avg Ratio", "RR", "Profit Factor", "Sharp Ratio", "No of Trades"]
        report = pd.DataFrame(final_report, columns=report_columns)
        report = report.sort_values(by="PAT", ascending=False)
        return report

    def get_min_sl(self):
        market_data_copy = self.market_data.copy()
        market_data_copy.reset_index(inplace=True)
        daily_candle = self.convert_timeframe("1D", market_data_copy)
        daily_candle['volatility'] = (daily_candle['high'] - daily_candle['low']) / daily_candle['low']
        average_value = daily_candle['volatility'].mean()
        min_sl = round(average_value*.2,4)
        return min_sl

    def select_best_exit_cases(self,report):
        min_sl = self.get_min_sl()
        report = report.sort_values(by="Sharp Ratio", ascending=False)
        if self.entry_type =="buy":
            report = report[report["Stoploss"] <= (1-min_sl)]
        elif self.entry_type == "sell":
            report = report[report["Target"] >= (1+min_sl)]

        report = report[report["RR"] >= 1]
        report = report[report["Sharp Ratio"] >=1]
        report = report.head(3)
        return report
