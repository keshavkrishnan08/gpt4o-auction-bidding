import argparse
import random
import pandas as pd
import os
from typing import List

from config import (
    NUM_ROUNDS, NUM_NON_LLM_AGENTS, MIN_TRUE_VALUE, MAX_TRUE_VALUE,
    AGENT_TRUTHFUL, AGENT_STRATEGIC, AGENT_RANDOM, AGENT_LLM,
    AUCTION_FIRST_PRICE, AUCTION_SECOND_PRICE,
    PERSONA_HONEST, PERSONA_PROFIT_MAX, PERSONA_RISK_AVERSE, PERSONA_RISK_SEEKING
)
from agents.truthful_agent import TruthfulAgent
from agents.strategic_agent import StrategicAgent
from agents.random_agent import RandomAgent
from agents.llm_agent import LLMAgent
from agents.base_agent import BaseAgent
from auctions.first_price import run_first_price_auction
from auctions.second_price import run_second_price_auction

def run_simulation(num_rounds: int, num_non_llm_agents: int, persona: str):
    print(f"Starting simulation: {num_rounds} rounds, {num_non_llm_agents} extra agents. Persona is {persona}.")
    
    # sticking all agents in a list
    agents: List[BaseAgent] = []
    
    # adding the 'honest' baseline
    agents.append(TruthfulAgent(name=AGENT_TRUTHFUL))
    
    # and the strategic one that bids half
    agents.append(StrategicAgent(name=AGENT_STRATEGIC))
    
    # fill up the rest with random agents
    for i in range(max(1, num_non_llm_agents - 2)):
        agents.append(RandomAgent(name=f"{AGENT_RANDOM}_{i+1}"))
        
    # the main LLM agent we're testing
    llm_agent = LLMAgent(name=AGENT_LLM, persona=persona)
    agents.append(llm_agent)
    
    results = []
    
    for round_num in range(1, num_rounds + 1):
        if round_num % 20 == 0:
            print(f"Working on round {round_num}/{num_rounds}...")
            
        # Give everyone a random value for this round
        true_values = {agent.name: random.uniform(MIN_TRUE_VALUE, MAX_TRUE_VALUE) for agent in agents}
        llm_true_value = true_values[llm_agent.name] 
        
        # Test both first and second price auctions for comparison
        for auction_type in [AUCTION_FIRST_PRICE, AUCTION_SECOND_PRICE]:
            
            bids_list = []
            bids_map = {} 
            
            for agent in agents:
                val = true_values[agent.name]
                bid = agent.bid(val, auction_type)
                bids_list.append(bid)
                bids_map[agent.name] = bid
            
            # double check we have the right order
            bids_list = [bids_map[agent.name] for agent in agents]
                
            # run the actual auction logic
            winner = None
            price_paid = 0
            if auction_type == AUCTION_FIRST_PRICE:
                winner_idx, price_paid = run_first_price_auction(bids_list)
                winner = agents[winner_idx].name if winner_idx != -1 else None
            elif auction_type == AUCTION_SECOND_PRICE:
                winner_idx, price_paid = run_second_price_auction(bids_list)
                winner = agents[winner_idx].name if winner_idx != -1 else None

            # check how our LLM did
            llm_bid = bids_map[llm_agent.name]
            llm_won = (winner == llm_agent.name)
            llm_profit = (llm_true_value - price_paid) if llm_won else 0

            # grab reasoning if the agent provided it
            llm_regime = getattr(llm_agent, "last_regime", "unknown")

            if hasattr(llm_agent, 'last_reasoning') and llm_agent.last_reasoning:
                reasoning_file = "data/reasoning_logs.csv"
                # make sure we have a header
                if not os.path.exists(reasoning_file):
                    with open(reasoning_file, 'w') as f:
                        f.write("round,persona,auction_type,true_value,bid,reasoning,prompt_regime\n")
                
                # fix up quotes so CSV doesn't break
                safe_reasoning = llm_agent.last_reasoning.replace('"', '""')
                with open(reasoning_file, 'a') as f:
                    f.write(f'{round_num},{persona},{auction_type},{llm_true_value},{llm_bid},"{safe_reasoning}",{llm_regime}\n')

            # package up everything for this round
            row = {
                "round": round_num,
                "auction_type": auction_type,
                "persona": persona,
                "winner": winner,
                "price_paid": price_paid,
                "llm_true_value": llm_true_value,
                "llm_bid": llm_bid,
                "llm_profit": llm_profit,
                "llm_prompt_regime": llm_regime
            }

            for agent in agents:
                row[f"{agent.name}_true_value"] = true_values[agent.name]
                row[f"{agent.name}_bid"] = bids_map[agent.name]
                
            results.append(row)
        
    # dumping everything to data/
    os.makedirs("data", exist_ok=True)
    output_path = "data/results.csv"
    
    df = pd.DataFrame(results)
    
    # append if it already exists, otherwise write new
    if os.path.exists(output_path):
        df.to_csv(output_path, mode='a', header=False, index=False)
        print(f"Results appended to {output_path}")
    else:
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ad Auction Simulation Script")
    parser.add_argument("--rounds", type=int, default=NUM_ROUNDS, help="how many rounds to run")
    parser.add_argument("--agents", type=int, default=NUM_NON_LLM_AGENTS, help="number of non-llm agents")
    parser.add_argument("--persona", type=str, default=PERSONA_HONEST, 
                        choices=[PERSONA_HONEST, PERSONA_PROFIT_MAX, PERSONA_RISK_AVERSE, PERSONA_RISK_SEEKING],
                        help="persona for the llm agent")
    
    args = parser.parse_args()
    
    run_simulation(args.rounds, args.agents, args.persona)
