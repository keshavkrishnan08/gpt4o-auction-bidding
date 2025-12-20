import pandas as pd
import re
import os
from collections import Counter

def analyze_reasoning():
    # looking at the logs from both experiments
    files = ["data/reasoning_logs.csv", "data/budget_reasoning_logs.csv"]
    
    for file in files:
        if not os.path.exists(file):
            continue
            
        print(f"\n--- Analyzing: {file} ---")
        df = pd.read_csv(file)
        
        # simple check for auction theory keywords in the LLM's head
        keywords = {
            "bid shading": r"shade|shading|lower.*bid|reducing.*bid",
            "truthful bidding": r"truthful|honest|value.*bid|bid.*value",
            "competition": r"competit|rival|opponent|market",
            "risk": r"risk|uncertain|safe|conservative",
            "budget": r"budget|money|remaining|cash|balance"
        }
        
        for name, pattern in keywords.items():
            df[name] = df['reasoning'].str.contains(pattern, case=False, na=False)
            
        # how often does it mention these things?
        print("\nKeyword Frequency:")
        stats = df[list(keywords.keys())].mean() * 100
        print(stats)
        
        # does its persona actually match its thoughts?
        if 'persona' in df.columns:
            print("\nMentions by Persona:")
            print(df.groupby('persona')[list(keywords.keys())].mean() * 100)

        # just grab some random examples to read
        print("\nSome samples of its reasoning:")
        if not df.empty:
            samples = df.sample(min(3, len(df)))
            for i, row in samples.iterrows():
                print(f"\n[{row.get('persona', 'unknown')} | {row.get('auction_type', 'unknown')}]")
                print(f"Bid: {row['bid']} (Value: {row['true_value']})")
                print(f"Reasoning: {row['reasoning'][:300]}...")

if __name__ == "__main__":
    analyze_reasoning()
