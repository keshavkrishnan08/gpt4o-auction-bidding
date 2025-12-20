import pandas as pd
import numpy as np
from scipy import stats
import os

def run_statistical_tests():
    print("-" * 30)
    print("Checking if the results are significant")
    print("-" * 30)
    
    # --- Exp 1: Strategic Reasoning ---
    exp1_path = "data/results.csv"
    if not os.path.exists(exp1_path):
        print(f"Can't find {exp1_path}")
        return
    
    df1 = pd.read_csv(exp1_path)
    personas = df1['persona'].unique()
    
    # compare BVR between first and second price
    print("\nTest 1: Bid-to-Value Ratio (FP vs SP)")
    df1['bvr'] = df1['llm_bid'] / df1['llm_true_value']
    
    for persona in personas:
        subset = df1[df1['persona'] == persona]
        fp_bvr = subset[subset['auction_type'] == 'First-Price']['bvr'].dropna()
        sp_bvr = subset[subset['auction_type'] == 'Second-Price']['bvr'].dropna()
        
        if len(fp_bvr) > 0 and len(sp_bvr) > 0:
            # use a simple t-test
            t_stat, t_pval = stats.ttest_ind(fp_bvr, sp_bvr, equal_var=False)
            
            # and a non-parametric one just to be sure
            u_stat, u_pval = stats.mannwhitneyu(fp_bvr, sp_bvr, alternative='two-sided')
            
            print(f"\nPersona: {persona}")
            print(f"  FP Mean: {fp_bvr.mean():.4f}, SP Mean: {sp_bvr.mean():.4f}")
            print(f"  t-test p-value: {t_pval:.6f}")
            print(f"  Mann-Whitney p-value: {u_pval:.6f}")
    
    # check profit differences
    print("\nTest 2: Profit Comparison (FP vs SP)")
    for persona in personas:
        subset = df1[df1['persona'] == persona]
        fp_profit = subset[subset['auction_type'] == 'First-Price']['llm_profit'].dropna()
        sp_profit = subset[subset['auction_type'] == 'Second-Price']['llm_profit'].dropna()
        
        if len(fp_profit) > 0 and len(sp_profit) > 0:
            t_stat, t_pval = stats.ttest_ind(fp_profit, sp_profit, equal_var=False)
            print(f"\nPersona: {persona}")
            print(f"  FP Avg Profit: ${fp_profit.mean():.2f}, SP Avg Profit: ${sp_profit.mean():.2f}")
            print(f"  p-value: {t_pval:.6f}")
    
    # --- Exp 2: Budgets ---
    exp2_path = "data/budget_results.csv"
    if not os.path.exists(exp2_path):
        return
    
    df2 = pd.read_csv(exp2_path)
    print("\nTest 3: Final Budget Comparison")
    
    def get_budget(row):
        if 'llm_budget_first_price' in row and row['auction_type'] == 'First-Price':
            return row['llm_budget_first_price']
        elif 'llm_budget_second_price' in row and row['auction_type'] == 'Second-Price':
            return row['llm_budget_second_price']
        return row.get('llm_remaining_budget', 0)
    
    df2['remaining_budget'] = df2.apply(get_budget, axis=1)
    
    final_budgets = df2.groupby(['persona', 'auction_type']).apply(
        lambda g: g.iloc[-1]['remaining_budget'] if len(g) > 0 else np.nan
    ).reset_index(name='final_budget')
    
    fp_finals = final_budgets[final_budgets['auction_type'] == 'First-Price']['final_budget']
    sp_finals = final_budgets[final_budgets['auction_type'] == 'Second-Price']['final_budget']
    
    if len(fp_finals) > 1 and len(sp_finals) > 1:
        t_stat, t_pval = stats.ttest_ind(fp_finals, sp_finals, equal_var=False)
        print(f"  Final Budget (FP) Avg: ${fp_finals.mean():.2f}")
        print(f"  Final Budget (SP) Avg: ${sp_finals.mean():.2f}")
        print(f"  p-value: {t_pval:.6f}")

if __name__ == "__main__":
    run_statistical_tests()
