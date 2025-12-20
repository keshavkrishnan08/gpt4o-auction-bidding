import argparse
import random
import pandas as pd
import numpy as np
import os
import sys

# hack to import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PERSONA_HONEST, PERSONA_PROFIT_MAX, PERSONA_RISK_AVERSE, PERSONA_RISK_SEEKING,
    AUCTION_FIRST_PRICE, AUCTION_SECOND_PRICE
)
from agents.llm_agent import LLMAgent
from agents.truthful_agent import TruthfulAgent
from agents.strategic_agent import StrategicAgent
from agents.random_agent import RandomAgent
from auctions.first_price import run_first_price_auction
from auctions.second_price import run_second_price_auction

def run_budget_simulation(rounds=100, num_agents=3, initial_budget=1000.0, persona=PERSONA_HONEST):
    print(f"Starting Budget Simulation: {rounds} rounds, ${initial_budget} budget, Persona: {persona}")
    
    # agents setup
    agents = []
    
    # our LLM agent
    llm_agent = LLMAgent("LLM_Agent", persona=persona)
    agents.append(llm_agent)
    
    # mix of other agents to compete against
    agent_types = [TruthfulAgent, StrategicAgent, RandomAgent]
    for i in range(num_agents):
        agent_class = agent_types[i % len(agent_types)]
        agents.append(agent_class(f"Agent_{i+1}_{agent_class.__name__}"))
        
    results = []
    reasoning_logs = []
    
    for round_num in range(1, rounds + 1):
        if round_num % 10 == 0:
            print(f"Processing round {round_num}/{rounds}...")
            
        # Give everyone a random value
        true_values = {agent.name: random.uniform(0, 100) for agent in agents}
        llm_true_value = true_values[llm_agent.name]
        
        # Parallel tracking for first and second price auctions
        if round_num == 1:
            budgets_fp = {agent.name: initial_budget for agent in agents}
            budgets_sp = {agent.name: initial_budget for agent in agents}
        
        for auction_type in [AUCTION_FIRST_PRICE, AUCTION_SECOND_PRICE]:
            
            # Select the correct budget pool for this auction type
            current_budgets = budgets_fp if auction_type == AUCTION_FIRST_PRICE else budgets_sp
            
            bids_map = {}
            for agent in agents:
                current_budget = current_budgets[agent.name]
                val = true_values[agent.name]
                
                # if you're broke, you can't bid
                if current_budget <= 0.01:
                    bid = 0.0
                else:
                    if isinstance(agent, LLMAgent):
                        bid = agent.bid(val, auction_type, remaining_budget=current_budget, initial_budget=initial_budget)
                    else:
                        bid = agent.bid(val, auction_type)
                    
                    # can't bid more than you have
                    if bid > current_budget:
                        bid = current_budget
                
                bids_map[agent.name] = bid
                
            # matching agent order
            bids_list = [bids_map[agent.name] for agent in agents]
                
            # run it
            winner_idx = -1
            price_paid = 0
            if auction_type == AUCTION_FIRST_PRICE:
                winner_idx, price_paid = run_first_price_auction(bids_list)
            elif auction_type == AUCTION_SECOND_PRICE:
                winner_idx, price_paid = run_second_price_auction(bids_list)
                
            winner = agents[winner_idx].name if winner_idx != -1 else None
            
            # deduct price from winner's budget
            if winner:
                current_budgets[winner] -= price_paid
                
            # track metrics
            llm_bid = bids_map[llm_agent.name]
            llm_won = (winner == llm_agent.name)
            llm_profit = (llm_true_value - price_paid) if llm_won else 0
            llm_budget = current_budgets[llm_agent.name]
            llm_regime = getattr(llm_agent, "last_regime", "unknown")
            
            # log everything
            llm_agent.update_history(round_num, llm_true_value, llm_bid, llm_won, price_paid)
            
            if hasattr(llm_agent, 'last_reasoning') and llm_agent.last_reasoning:
                reasoning_logs.append({
                    "round": round_num,
                    "persona": persona,
                    "auction_type": auction_type,
                    "true_value": llm_true_value,
                    "budget": llm_budget,
                    "bid": llm_bid,
                    "reasoning": llm_agent.last_reasoning,
                    "prompt_regime": llm_regime
                })
                
            row = {
                "round": round_num,
                "auction_type": auction_type,
                "persona": persona,
                "winner": winner,
                "price_paid": price_paid,
                "llm_true_value": llm_true_value,
                "llm_bid": llm_bid,
                "llm_profit": llm_profit,
                "llm_budget_first_price": budgets_fp[llm_agent.name],
                "llm_budget_second_price": budgets_sp[llm_agent.name],
                "llm_prompt_regime": llm_regime
            }
            
            for agent in agents:
                row[f"{agent.name}_true_value"] = true_values[agent.name]
                row[f"{agent.name}_bid"] = bids_map[agent.name]
                
            results.append(row)
        
    # saving to data/
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(results)
    output_file = "data/budget_results.csv"

    if os.path.exists(output_file):
        try:
             # simple check to see if we can append
             existing_df = pd.read_csv(output_file, nrows=0)
             if set(existing_df.columns) == set(df.columns):
                 df.to_csv(output_file, mode='a', header=False, index=False)
             else:
                 df.to_csv(output_file, index=False)
        except:
             df.to_csv(output_file, index=False) 
    else:
        df.to_csv(output_file, index=False)
        
    print(f"Results saved to {output_file}")
    
    # save the reasoning traces
    if reasoning_logs:
        df_log = pd.DataFrame(reasoning_logs)
        log_file = "data/budget_reasoning_logs.csv"
        if os.path.exists(log_file):
            df_log.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df_log.to_csv(log_file, index=False)
        print(f"Reasoning logs saved to {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Budget-Constrained Auction Sim")
    parser.add_argument("--rounds", type=int, default=100, help="how many rounds")
    parser.add_argument("--agents", type=int, default=3, help="number of opponents")
    parser.add_argument("--budget", type=float, default=1000.0, help="starting budget")
    parser.add_argument("--persona", type=str, default=PERSONA_HONEST, help="persona name")
    
    args = parser.parse_args()
    
    run_budget_simulation(rounds=args.rounds, num_agents=args.agents, initial_budget=args.budget, persona=args.persona)

