import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def generate_budget_graphs():
    data_path = "data/budget_results.csv"
    output_dir = "analysis/plots"
    
    if not os.path.exists(data_path):
        print(f"No data found at {data_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path)
    
    # --- Style Configuration ---
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['font.size'] = 10
    
    styles = {
        'First-Price': {'color': 'tab:blue', 'linestyle': '-', 'marker': '', 'label': 'First-Price'},
        'Second-Price': {'color': 'tab:orange', 'linestyle': '--', 'marker': '', 'label': 'Second-Price'}
    }
    
    personas = df['persona'].unique()
    auction_types = df['auction_type'].unique() if 'auction_type' in df.columns else ['Unknown']
    
    # --- 1. Remaining Budget over Time ---
    plt.figure(figsize=(12, 6))
    for persona in personas:
        for auction_type in auction_types:
            subset = df[(df['persona'] == persona) & (df['auction_type'] == auction_type)]
            if not subset.empty:
                style = styles.get(auction_type, {'color': 'gray', 'linestyle': '-'})
                label = f"{persona} ({auction_type})"
                
                # Select correct column
                col_name = 'llm_budget_first_price' if auction_type == 'First-Price' else 'llm_budget_second_price'
                if col_name not in subset.columns:
                     col_name = 'llm_remaining_budget'
                
                if col_name in subset.columns:
                    plt.plot(subset['round'], subset[col_name], label=label, 
                            color=style['color'], linestyle=style['linestyle'], linewidth=2)
        
    plt.title("LLM Remaining Budget Over Rounds")
    plt.xlabel("Round")
    plt.ylabel("Remaining Budget ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}/budget_over_time.png")
    plt.close()
    print(f"Saved budget plot to {output_dir}/budget_over_time.png")
    
    # --- 2. Cumulative Profit over Time ---
    plt.figure(figsize=(12, 6))
    for persona in personas:
        for auction_type in auction_types:
            subset = df[(df['persona'] == persona) & (df['auction_type'] == auction_type)].copy()
            if not subset.empty:
                subset.sort_values('round', inplace=True)
                subset['cumulative_profit'] = subset['llm_profit'].cumsum()
                
                style = styles.get(auction_type, {'color': 'gray', 'linestyle': '-'})
                label = f"{persona} ({auction_type})"
                
                plt.plot(subset['round'], subset['cumulative_profit'], label=label, 
                        color=style['color'], linestyle=style['linestyle'], linewidth=2)
        
    plt.title("LLM Cumulative Profit Over Rounds")
    plt.xlabel("Round")
    plt.ylabel("Cumulative Profit ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}/cumulative_profit.png")
    plt.close()
    print(f"Saved profit plot to {output_dir}/cumulative_profit.png")

if __name__ == "__main__":
    generate_budget_graphs()
