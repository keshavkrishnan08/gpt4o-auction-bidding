import pandas as pd
import os
import sys

def calculate_budget_stats():
    data_path = "data/budget_results.csv"
    if not os.path.exists(data_path):
        print(f"No data found at {data_path}")
        return

    df = pd.read_csv(data_path)
    
    print("\n--- Budget Simulation Statistics ---")
    
    # Group by Persona
    personas = df['persona'].unique()
    
    for persona in personas:
        subset = df[df['persona'] == persona]
        
        total_profit = subset['llm_profit'].sum()
        final_budget = subset['llm_remaining_budget'].iloc[-1]
        rounds_played = len(subset)
        wins = subset[subset['winner'] == 'LLM_Agent'].shape[0]
        win_rate = (wins / rounds_played) * 100
        
        # Metrics
        subset['bid_ratio'] = subset['llm_bid'] / subset['llm_true_value']
        mean_ratio = subset['bid_ratio'].mean()
        profit_variance = subset['llm_profit'].var()
        
        # Budget Utilization
        initial_budget = 1000.0 # Assuming default, or we could infer from first round if we tracked it
        # Actually, we can infer from the first round's remaining budget + price paid if won?
        # Or just assume 1000. Or better, take max of remaining budget in round 1?
        # Let's assume 1000 for now as per default.
        total_spent = initial_budget - final_budget
        utilization = (total_spent / initial_budget) * 100
        
        # Market Efficiency
        total_possible_value = 0
        total_realized_value = 0
        
        for idx, row in subset.iterrows():
            # We need to find max true value. 
            # The CSV has columns like "{agent}_true_value"
            true_value_cols = [c for c in df.columns if c.endswith('_true_value')]
            max_val = row[true_value_cols].max()
            total_possible_value += max_val
            
            winner_name = row['winner']
            if pd.notna(winner_name):
                winner_val = row.get(f"{winner_name}_true_value", 0)
                total_realized_value += winner_val
                
        efficiency = (total_realized_value / total_possible_value) * 100 if total_possible_value > 0 else 0

        print(f"\nPersona: {persona}")
        print(f"  Total Profit:       ${total_profit:.2f}")
        print(f"  Profit Variance:    {profit_variance:.2f}")
        print(f"  Final Budget:       ${final_budget:.2f}")
        print(f"  Budget Utilization: {utilization:.1f}%")
        print(f"  Win Rate:           {win_rate:.1f}% ({wins}/{rounds_played})")
        print(f"  Avg Bid:            ${subset['llm_bid'].mean():.2f}")
        print(f"  Avg Bid/Value Ratio:{mean_ratio:.2f}")
        print(f"  Market Efficiency:  {efficiency:.1f}%")
        
        # Check for bankruptcy
        bankruptcy_round = subset[subset['llm_remaining_budget'] <= 0.01]['round'].min()
        if pd.notna(bankruptcy_round):
            print(f"  Went Bankrupt at:   Round {int(bankruptcy_round)}")
        else:
            print(f"  Survived all {rounds_played} rounds")

if __name__ == "__main__":
    # Change CWD to script directory to find data if run from there
    # But usually run from root of budget_experiment
    calculate_budget_stats()
