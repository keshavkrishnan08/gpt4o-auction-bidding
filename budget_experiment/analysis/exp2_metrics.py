import pandas as pd
import numpy as np
import os

def calculate_budget_metrics():
    data_path = "data/budget_results.csv"
    if not os.path.exists(data_path):
        print("No budget_results.csv found for Exp 2.")
        return

    df = pd.read_csv(data_path)
    
    # Ensure necessary columns exist
    # Note: We now support 'llm_budget_first_price' / 'llm_budget_second_price'
    # but we will synthesize 'llm_remaining_budget' for backward compatibility in this script.
    required_cols = ['llm_bid', 'llm_true_value', 'llm_profit', 'winner', 'persona', 'llm_prompt_regime', 'price_paid']
    for col in required_cols:
        if col not in df.columns:
            if col == 'llm_prompt_regime':
                df[col] = 'unknown'
            else:
                print(f"Missing column: {col}")
                return

    # Synthesize effective remaining budget for the specific auction type of the row
    def get_budget(row):
        if 'llm_budget_first_price' in row and row['auction_type'] == 'First-Price':
            return row['llm_budget_first_price']
        elif 'llm_budget_second_price' in row and row['auction_type'] == 'Second-Price':
            return row['llm_budget_second_price']
        elif 'llm_remaining_budget' in row:
            return row['llm_remaining_budget']
        return 0.0

    df['llm_remaining_budget'] = df.apply(get_budget, axis=1)

    # Identify Runs (Robust to interleaved data)
    # A new run starts when round number drops (e.g. 10 -> 1)
    df['run_start'] = (df['round'] < df['round'].shift(1)) | (df.index == 0)
    df['run_id'] = df['run_start'].cumsum()

    # --- 1. Core Budget Metrics ---
    
    # Run-level stats
    run_stats = []
    
    for (run_id, persona, auction_type), group in df.groupby(['run_id', 'persona', 'auction_type']):
        initial_budget = group['llm_remaining_budget'].iloc[0] + group['price_paid'].iloc[0] if (group['winner'].iloc[0] == 'LLM_Agent') else group['llm_remaining_budget'].iloc[0]
        
        final_budget = group['llm_remaining_budget'].iloc[-1]
        llm_spend = group[group['winner'].str.contains("LLM", na=False)]['price_paid'].sum()
        
        inferred_initial = llm_spend + final_budget
        utilization = llm_spend / inferred_initial if inferred_initial > 0 else 0
        
        is_bankrupt = final_budget < 1.0 
        bankruptcy_round = group['round'].max() if is_bankrupt else np.nan
        rounds_survived = group['round'].max()
        
        run_stats.append({
            'run_id': run_id,
            'persona': persona,
            'auction_type': auction_type,
            'utilization': utilization,
            'is_bankrupt': is_bankrupt,
            'bankruptcy_round': bankruptcy_round,
            'rounds_survived': rounds_survived,
            'llm_spend': llm_spend,
            'inferred_initial': inferred_initial
        })
        
    run_df = pd.DataFrame(run_stats)
    
    print("\n=== 1. Core Budget Metrics ===")
    print("--- Budget Utilization Rate ---")
    print(run_df.groupby(['persona', 'auction_type'])['utilization'].mean())
    
    print("\n--- Bankruptcy Rate ---")
    print(run_df.groupby(['persona', 'auction_type'])['is_bankrupt'].mean())
    
    print("\n--- Average Bankruptcy Round (for bankrupt agents) ---")
    print(run_df[run_df['is_bankrupt']].groupby(['persona', 'auction_type'])['bankruptcy_round'].mean())
    
    # 3. Survival Efficiency = Rounds Survived / Budget Used
    run_df['survival_efficiency'] = run_df.apply(lambda row: row['rounds_survived'] / row['llm_spend'] if row['llm_spend'] > 10 else 0, axis=1)
    
    print("\n--- Survival Efficiency (Rounds / $ Spend) ---")
    print(run_df.groupby(['persona', 'auction_type'])['survival_efficiency'].mean())


    # --- 2. Crisis Response Effectiveness ---
    print("\n=== 2. Crisis Response Metrics ===")
    
    crisis_effects = []
    
    for (run_id, persona, auction_type), group in df.groupby(['run_id', 'persona', 'auction_type']):
        group = group.sort_values('round')
        
        group['prev_regime'] = group['llm_prompt_regime'].shift(1)
        
        crisis_starts = group[
            (group['llm_prompt_regime'] == 'crisis') & 
            (group['prev_regime'] != 'crisis') & 
            (group['prev_regime'].notna())
        ]
        
        for idx, row in crisis_starts.iterrows():
            crisis_round = row['round']
            pre_window = group[(group['round'] >= crisis_round - 5) & (group['round'] < crisis_round)]
            post_window = group[(group['round'] >= crisis_round) & (group['round'] < crisis_round + 5)]
            
            if len(pre_window) > 0 and len(post_window) > 0:
                def calc_spend(w):
                    w_spend = w[w['winner'].str.contains("LLM", na=False)]['price_paid'].sum()
                    return w_spend / len(w)
                    
                pre_spend_rate = calc_spend(pre_window)
                post_spend_rate = calc_spend(post_window)
                
                pre_win_rate = pre_window['winner'].str.contains("LLM", na=False).mean()
                post_win_rate = post_window['winner'].str.contains("LLM", na=False).mean()
                
                pre_avg_bid = pre_window['llm_bid'].mean()
                post_avg_bid = post_window['llm_bid'].mean()
                
                crisis_effects.append({
                    'persona': persona,
                    'auction_type': auction_type,
                    'delta_spend_rate': post_spend_rate - pre_spend_rate,
                    'delta_win_rate': post_win_rate - pre_win_rate,
                    'delta_bid_size': post_avg_bid - pre_avg_bid
                })
                
    if crisis_effects:
        eff_df = pd.DataFrame(crisis_effects)
        print("\n--- Crisis Response Effectiveness ---")
        print(eff_df.groupby(['persona', 'auction_type']).mean())
    else:
        print("\nNo crisis events detected (or not enough history around them).")

    # --- 3. Endgame Behavior ---
    print("\n=== 3. Endgame Behavior (Last 20 Rounds) ===")
    
    endgame_stats = []
    
    for (run_id, persona, auction_type), group in df.groupby(['run_id', 'persona', 'auction_type']):
        if len(group) > 20:
            endgame = group.tail(20)
            avg_bid = endgame['llm_bid'].mean()
            win_rate = endgame['winner'].str.contains("LLM", na=False).mean()
            final_budget = endgame['llm_remaining_budget'].iloc[-1]
            
            endgame_stats.append({
                'persona': persona,
                'auction_type': auction_type,
                'endgame_avg_bid': avg_bid,
                'endgame_win_rate': win_rate,
                'final_budget': final_budget
            })
            
    if endgame_stats:
        end_df = pd.DataFrame(endgame_stats)
        print(end_df.groupby(['persona', 'auction_type']).mean())
    else:
        print("Not enough rounds for endgame analysis.")

if __name__ == "__main__":
    calculate_budget_metrics()
