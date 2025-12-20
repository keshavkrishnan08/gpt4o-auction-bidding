import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# parent dir hack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_graphs(data_path: str = "data/results.csv", output_dir: str = "analysis/plots"):
    if not os.path.exists(data_path):
        print(f"No data at {data_path}. Run the sim first!")
        return

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path)
    
    # some basic styling
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['font.size'] = 10
    
    styles = {
        'First-Price': {'color': 'tab:blue', 'linestyle': '-', 'marker': 'o', 'label': 'First-Price'},
        'Second-Price': {'color': 'tab:orange', 'linestyle': '--', 'marker': 'x', 'label': 'Second-Price'}
    }
    
    # helper folders for the plots
    dirs = {
        "histograms": f"{output_dir}/histograms",
        "scatter": f"{output_dir}/scatter_plots",
        "trends": f"{output_dir}/trends",
        "comparisons": f"{output_dir}/comparisons"
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    
    personas = df['persona'].unique() if 'persona' in df.columns else ['default']
    
    for persona in personas:
        subset_persona = df[df['persona'] == persona] if 'persona' in df.columns else df
        
        # --- Histogram: where are the bids landing? ---
        plt.figure(figsize=(10, 6))
        for auction_type in subset_persona['auction_type'].unique():
            subset = subset_persona[subset_persona['auction_type'] == auction_type]
            style = styles.get(auction_type, {'color': 'gray'})
            plt.hist(subset['llm_bid'], bins=20, alpha=0.5, label=auction_type, color=style['color'])
        
        plt.title(f"LLM Bids: {persona}")
        plt.xlabel("Bid")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(True, alpha=0.3)
        output_path = f"{dirs['histograms']}/llm_bids_histogram_{persona}.png"
        plt.savefig(output_path)
        plt.close()
        
        # --- Scatter: Bid vs Value ---
        plt.figure(figsize=(10, 6))
        for auction_type in subset_persona['auction_type'].unique():
            subset = subset_persona[subset_persona['auction_type'] == auction_type]
            style = styles.get(auction_type, {'color': 'gray', 'marker': 'o'})
            plt.scatter(subset['llm_true_value'], subset['llm_bid'], 
                       alpha=0.6, label=auction_type, color=style['color'], marker=style['marker'], s=40)
            
        max_val = subset_persona['llm_true_value'].max()
        plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label="Truthful (y=x)")
        
        plt.title(f"Bid vs. Value: {persona}")
        plt.xlabel("True Value")
        plt.ylabel("Bid")
        plt.legend()
        plt.grid(True, alpha=0.3)
        output_path = f"{dirs['scatter']}/llm_bid_vs_value_scatter_{persona}.png"
        plt.savefig(output_path)
        plt.close()
        
        # --- Line: Rolling Avg ---
        subset_persona = subset_persona.copy()
        subset_persona['llm_bid_ratio'] = subset_persona['llm_bid'] / subset_persona['llm_true_value']
        
        plt.figure(figsize=(10, 6))
        for auction_type in subset_persona['auction_type'].unique():
            subset = subset_persona[subset_persona['auction_type'] == auction_type].copy()
            subset.sort_values('round', inplace=True)
            subset['rolling_ratio'] = subset['llm_bid_ratio'].rolling(window=20, min_periods=1).mean()
            
            style = styles.get(auction_type, {'color': 'gray', 'linestyle': '-'})
            plt.plot(subset['round'], subset['rolling_ratio'], 
                    label=f"{auction_type}", color=style['color'], linestyle=style['linestyle'], linewidth=2)
            
        plt.axhline(y=1.0, color='k', linestyle=':', alpha=0.5, label="Truthful (1.0)")
        plt.title(f"Bid/Value Ratio Over Time: {persona}")
        plt.xlabel("Round")
        plt.ylabel("Ratio")
        plt.legend()
        plt.grid(True, alpha=0.3)
        output_path = f"{dirs['trends']}/bid_ratio_over_time_{persona}.png"
        plt.savefig(output_path)
        plt.close()

    # --- Bar: Profit comparison across personas ---
    if 'persona' in df.columns and len(personas) > 1:
        plt.figure(figsize=(12, 6))
        
        profit_data = df.groupby(['persona', 'auction_type'])['llm_profit'].mean().unstack()
        
        colors = [styles.get(col, {'color': 'gray'})['color'] for col in profit_data.columns]
        profit_data.plot(kind='bar', figsize=(12, 6), color=colors, edgecolor='black', alpha=0.8)
        
        plt.title("Avg Profit by Persona")
        plt.xlabel("Persona")
        plt.ylabel("Avg Profit")
        plt.xticks(rotation=45)
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        output_path = f"{dirs['comparisons']}/profit_comparison_by_persona.png"
        plt.savefig(output_path)
        plt.close()

if __name__ == "__main__":
    generate_graphs()
