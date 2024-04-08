import pandas as pd
from itertools import product

from Entry_Strategy import get_rsi_upper_entries
from ExitOptimizer import exit_optimizer
from Exit_Cases import ExitCaseAnalyzer
from FeaturesModule import add_volume_shocker,add_volatility_pct,add_macd_upper

class AutoStrategy:
    def __init__(self, market_data,forward_test_market_data):
        self.market_data = market_data
        self.forward_test_market_data = forward_test_market_data
        self.combination_id = 0
        self.feature1 = 0
        self.feature2 = 0
        self.feature3 = 0

    def run_engine(self):
        self. process_market_data()
        combinations = self.generate_feature_combinations(num_features=3)
        Entries_main = get_rsi_upper_entries(self.market_data,70)

        best_combinations = pd.DataFrame()
        for _,row in combinations.iterrows():
            Entries = Entries_main.copy()
            best_cases_buy = self.get_best_exit_cases(row,Entries,"buy")
            best_cases_sell = self.get_best_exit_cases(row,Entries,"sell")
            best_combinations = pd.concat([best_combinations, best_cases_buy, best_cases_sell])
        print(best_combinations)
        forward_report = self.forward_test(best_combinations)
        return best_combinations,forward_report

    def process_market_data(self):
        self.market_data['date'] = pd.to_datetime(self.market_data['date'], format='%d-%m-%Y %H:%M')
        self.market_data = self.market_data.sort_values(by="date", ascending=True)
        self.forward_test_market_data['date'] = pd.to_datetime(self.forward_test_market_data['date'], format='%d-%m-%Y %H:%M')
        self.forward_test_market_data = self.forward_test_market_data.sort_values(by="date", ascending=True)

    def Generate_entries_with_features(self,Entries,market_data):
        if self.feature1:
            Entries = add_volume_shocker(Entries, market_data, 3)
        if self.feature2:
            Entries = add_volatility_pct(Entries, market_data, 0.004)
        if self.feature3:
            Entries = add_macd_upper(Entries, market_data, 2)

        Entries = Entries.groupby(Entries['date'].dt.date).first().reset_index(drop=True)
        print("Limited to 1 Entry per day:", len(Entries), "Entries")
        return Entries
    
    def get_best_exit_cases(self, row, Entries, entry_type):
        self.feature1, self.feature2, self.feature3, self.combination_id = row[['Feature 1', 'Feature 2', 'Feature 3', 'Combination ID']]
        print(f"Combination: {self.combination_id}, Type: {entry_type}, Features: {self.feature1}, {self.feature2}, {self.feature3}")
        # self.market_data = self.market_data.reset_index()
        Entries = self.Generate_entries_with_features(Entries, self.market_data)
        # self.market_data = self.market_data.reset_index()
        if not Entries.empty:
            BO, SO = exit_optimizer(Entries, self.market_data, 100000, "15:00")

            exit_data = BO if entry_type == "buy" else SO

            best_case_obj = ExitCaseAnalyzer(exit_data, entry_type, self.market_data)
            best_exit_cases = best_case_obj.analyze_exit_variations().reset_index(drop=True)

            best_exit_cases[['Combination ID', 'Feature 1', 'Feature 2', 'Feature 3','Entry Type']] = [self.combination_id, self.feature1, self.feature2, self.feature3, entry_type]

            return best_exit_cases
        else:
            return pd.DataFrame()
        
    
    def forward_test(self,best_combinations):
        print("Forward testing")
        forward_result=[]
        Entries_main = get_rsi_upper_entries(self.forward_test_market_data,70)
        for _,row in best_combinations.iterrows():
            Entries = Entries_main.copy()
            self.feature1, self.feature2, self.feature3, self.combination_id, entry_type = row[['Feature 1', 'Feature 2', 'Feature 3', 'Combination ID','Entry Type']]
            print(f"Combination: {self.combination_id}, Type: {entry_type}, Features: {self.feature1}, {self.feature2}, {self.feature3}")

            Entries = self.Generate_entries_with_features(Entries, self.forward_test_market_data)
            # self.forward_test_market_data = self.forward_test_market_data.reset_index()
            if not Entries.empty:
                BO, SO = exit_optimizer(Entries, self.forward_test_market_data, 100000, "15:00")
                exit_data = BO if entry_type == "buy" else SO

                Trades = exit_data[(exit_data['Stoploss']==row['Stoploss']) & (exit_data['Target']==row['Target'])]
                pnl = Trades['PAT'].sum()
                max_dd = self.max_drawdown_value(Trades, "PAT")
                no_of_trades = len(Trades)
                print(pnl, max_dd, no_of_trades)
                forward_result.append((self.combination_id,entry_type,self.feature1,self.feature2,self.feature3,row['Stoploss'], row['Target'],row['PAT'], 
                                    row['Max DD'],pnl,max_dd,no_of_trades))
            else:
                print("No Entries found")
        
        Forward_Report = pd.DataFrame(forward_result, columns=['Combination ID', 'Entry Type', 'Feature 1', 'Feature 2', ' Feature 3', 
                                        'Stoploss','Target', 'Backtest PAT', 'Backtest DD', 'Foward PAT', 'Foward DD', 'No of Forward Trades'])

        return Forward_Report

    @staticmethod
    def max_drawdown_value(trades, pnl_column_name):
        trades = trades.sort_values('Entry Date').reset_index(drop=True)
        trades['cumulative_pnl'] = trades[pnl_column_name].cumsum()
        drawdown = trades['cumulative_pnl'] - trades['cumulative_pnl'].cummax()
        max_drawdown = drawdown.min() 
        return max_drawdown

    @staticmethod
    def generate_feature_combinations(num_features):
        """Generate combinations of features."""
        combinations = list(product([0, 1], repeat=num_features))
        df = pd.DataFrame(combinations, columns=[f"Feature {i+1}" for i in range(num_features)])
        df.insert(0, "Combination ID", range(1, len(combinations) + 1))
        return df

# Sample
market_data = pd.read_csv("Reliance.csv")
forward_market_data = pd.read_csv("Reliance_Forward.csv")
RSI_Strategy = AutoStrategy(market_data,forward_market_data)
backtest_report, foward_report = RSI_Strategy.run_engine()
print(backtest_report)
print(foward_report)
