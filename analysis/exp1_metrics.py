import pandas as pd
import numpy as np
import os

def calculate_metrics():
    # load the experiment 1 data
    data_path = "data/results.csv"
    if not os.path.exists(data_path):
        print("No results.csv found for Exp 1.")
        return

    df = pd.read_csv(data_path)
    
    # check we have what we need
    required_cols = ['llm_bid', 'llm_true_value', 'llm_profit', 'winner', 'persona', 'auction_type', 'llm_prompt_regime']
    for col in required_cols:
        if col not in df.columns:
            if col == 'llm_prompt_regime':
                df[col] = 'unknown' # fallback for older logs
            else:
                print(f"Missing column: {col}")
                return

    # calculate bid-to-value ratio (BVR)
    df['bvr'] = df['llm_bid'] / df['llm_true_value']
    
    print("\n--- Core Stats ---")
    print("Bid-to-Value Ratio (BVR):")
    bvr_stats = df.groupby(['persona', 'auction_type'])['bvr'].agg(['mean', 'std', 'count'])
    print(bvr_stats)
    
    # how many times did we actually win?
    df['is_winner'] = df['winner'].str.contains("LLM", na=False)
    
    print("\nWin Rate:")
    win_rate = df.groupby(['persona', 'auction_type'])['is_winner'].mean()
    print(win_rate)

    # how much profit are we making?
    print("\nAvg Profit:")
    profit_stats = df.groupby(['persona', 'auction_type'])['llm_profit'].agg(['mean', 'var'])
    print(profit_stats)

    # calculate market efficiency (winner's value / max possible value)
    value_cols = [c for c in df.columns if "_true_value" in c]
    df['max_value'] = df[value_cols].max(axis=1)
    
    def get_winner_value(row):
        if pd.isna(row['winner']): return 0
        col_name = f"{row['winner']}_true_value"
        return row.get(col_name, 0)

    df['winner_value'] = df.apply(get_winner_value, axis=1)
    df['efficiency'] = df['winner_value'] / df['max_value']
    
    print("\nMarket Efficiency:")
    efficiency_stats = df.groupby(['persona', 'auction_type'])['efficiency'].mean()
    print(efficiency_stats)


    # looking at how the LLM adapts its strategy
    print("\n--- Strategy Volatility (Std Dev of BVR) ---")
    print(bvr_stats['std'])

    # trying to detect when the prompt strategy changed and how the LLM reacted
    df['run_start'] = (df['round'] < df['round'].shift(1)) | (df.index == 0)
    df['run_id'] = df['run_start'].cumsum()
    
    transitions = []
    
    for (run_id, persona, auction), group in df.groupby(['run_id', 'persona', 'auction_type']):
        group = group.sort_values('round')
        
        # compare with previous round's regime
        group['prev_regime'] = group['llm_prompt_regime'].shift(1)
        group['prev_bvr'] = group['bvr'].shift(1)
        
        # find where the regime switched
        switch_mask = (group['llm_prompt_regime'] != group['prev_regime']) & (group['prev_regime'].notna()) & (group['llm_prompt_regime'] != 'unknown')
        switches = group[switch_mask]
        
        for idx, row in switches.iterrows():
            trans_type = f"{row['prev_regime']} -> {row['llm_prompt_regime']}"
            delta_bvr = row['bvr'] - row['prev_bvr']
            
            transitions.append({
                'persona': persona,
                'transition': trans_type,
                'delta_bvr': delta_bvr
            })
            
    if transitions:
        trans_df = pd.DataFrame(transitions)
        print("\n--- Response to Prompt Changes (Mean Delta BVR) ---")
        print(trans_df.groupby(['transition'])['delta_bvr'].agg(['mean', 'count']))
    else:
        print("\nNo prompt switches found.")


if __name__ == "__main__":
    calculate_metrics()
