import re
import sys
import os
import json
from openai import OpenAI

# bit of a hack to get config from the parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PERSONA_HONEST, PERSONA_PROFIT_MAX, PERSONA_RISK_AVERSE, PERSONA_RISK_SEEKING,
    MODEL_DEFAULT, OPENAI_API_KEY
)
from .base_agent import BaseAgent

class LLMAgent(BaseAgent):
    """
    LLM-based agent. It basically just asks GPT what to bid.
    """
    def __init__(self, name: str, model: str = MODEL_DEFAULT, temperature: float = 0.0, persona: str = PERSONA_HONEST):
        super().__init__(name)
        self.model = model
        self.temperature = temperature
        self.persona = persona
        self.history = [] # track previous rounds: round, value, bid, etc.
        self.last_reasoning = "" 
        
        # setup the openai client
        # trying to get the key from config first, then env vars
        api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            print("WARNING: No API key found. Using mock/fake behavior instead.")

    def update_history(self, round_num: int, true_value: float, bid: float, won: bool, price_paid: float):
        # logging how we did
        profit = (true_value - price_paid) if won else 0.0
        self.history.append({
            'round': round_num,
            'true_value': true_value,
            'bid': bid,
            'won': won,
            'price_paid': price_paid,
            'profit': profit
        })
        # only keep the last 20 rounds so the context window doesn't explode
        if len(self.history) > 20:
            self.history.pop(0)

    def _get_history_str(self) -> str:
        if not self.history:
            return "No previous history."
        
        lines = []
        # just show the last 5 rounds in the prompt
        for entry in self.history[-5:]:
            status = "WON" if entry['won'] else "LOST"
            lines.append(f"Round {entry['round']}: Value={entry['true_value']:.2f}, Bid={entry['bid']:.2f}, Result={status}, Price Paid={entry['price_paid']:.2f}, Profit={entry['profit']:.2f}")
        return "\n".join(lines)

    def _call_llm_api(self, prompt: str, remaining_budget: float = None, initial_budget: float = None) -> str:
        # returns the bid from openai (or a mock if we're testing)
        self.last_regime = "neutral" 
        
        if self.client:
            # Enforce JSON output so it's easier to parse
            system_content = (
                "You are a rational agent in an auction simulation. "
                "Output ONLY a valid JSON object with keys 'reasoning' (string) and 'bid' (number). "
                "Do not include any markdown formatting or extra text. "
                "Example: {\"reasoning\": \"Step-by-step logic...\", \"bid\": 10.5}"
            )
            
            # --- Handle low budget scenarios ---
            is_crisis = False
            if remaining_budget is not None and initial_budget is not None:
                # if we're down to <10% of our money, panic slightly
                if remaining_budget < (0.10 * initial_budget):
                    system_content += " CRITICAL ALERT: Your budget is critically low! Be very careful. Only bid on really good opportunities."
                    self.last_regime = "crisis"
                    is_crisis = True
            
            # --- Tweak strategy based on recent performance ---
            if not is_crisis:
                if len(self.history) >= 5:
                    recent_wins = sum(1 for h in self.history[-5:] if h['won'])
                    if recent_wins == 0:
                        # lost too much, try to be aggressive
                        system_content += " You've been losing lately. Maybe try bidding higher?"
                        self.last_regime = "adaptive_aggressive"
                    elif recent_wins >= 4:
                        # winning a lot, maybe dial it back to save cash
                        system_content += " You're winning a lot. Don't overpay."
                        self.last_regime = "adaptive_conservative"
            
            # 3 attempts in case the API flakes out
            retries = 3
            for attempt in range(retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.temperature,
                        max_tokens=250 
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"API Error (Attempt {attempt+1}/{retries}): {e}")
                    if attempt == retries - 1:
                        # fall back to 0 bid if it keeps failing
                        return json.dumps({"reasoning": "API Error, fallback bid", "bid": 0.0})
        
        # --- Mock values for testing without an API key ---
        self.last_regime = "mock"
        match = re.search(r"true value for the ad slot is ([\d\.]+)", prompt)
        if match:
            val_str = match.group(1).rstrip('.')
            true_value = float(val_str)
            
            bid_val = 0.0
            # basic logic for the different personas
            if self.persona == PERSONA_HONEST:
                bid_val = true_value
            elif self.persona == PERSONA_PROFIT_MAX:
                bid_val = true_value * 0.8
            elif self.persona == PERSONA_RISK_AVERSE:
                bid_val = true_value * 0.9
            elif self.persona == PERSONA_RISK_SEEKING:
                bid_val = min(true_value * 1.1, true_value)
            
            return json.dumps({
                "reasoning": f"Mock reasoning for {self.persona}. Value is {true_value}.",
                "bid": bid_val
            })
        
        return json.dumps({"reasoning": "Mock Fallback", "bid": 0})

    def bid(self, true_value: float, auction_type: str, remaining_budget: float = None, initial_budget: float = None) -> float:
        # build the prompt for gpt
        history_str = self._get_history_str()
        
        prompt = (
            f"You are in a {auction_type} auction. Your true value is {true_value:.2f}. "
            f"Your goal is to maximize profit. Persona: {self.persona}. "
        )
        
        if remaining_budget is not None:
             prompt += f"\nRemaining budget: ${remaining_budget:.2f}."

        prompt += (
            f"\n\nRecent history:\n{history_str}\n\n"
            f"Think step by step and decide your bid.\n"
            f"Response format (JSON ONLY):\n"
            f'{{"reasoning": "...", "bid": ...}}'
        )
        
        # if they keep losing, give 'em a nudge
        if len(self.history) >= 3:
            recent_losses = sum(1 for h in self.history[-3:] if not h['won'])
            if recent_losses == 3:
                 prompt += "\nYou lost the last 3 rounds. Try being more competitive."

        response = self._call_llm_api(prompt, remaining_budget, initial_budget)
        
        # --- Try to parse the JSON response ---
        try:
            # 1. basic json parse
            data = json.loads(response)
            self.last_reasoning = data.get("reasoning", "")
            return float(data.get("bid", 0.0))
        except json.JSONDecodeError:
            pass 
            
        try:
            # 2. if they wrapped it in markdown code blocks, strip 'em
            cleaned = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            self.last_reasoning = data.get("reasoning", "")
            return float(data.get("bid", 0.0))
        except json.JSONDecodeError:
            pass 
 
        # 3. Last ditch effort: find the last number in the text
        with open("data/parsing_failures.log", "a") as f:
            f.write(f"FAILED_PARSE | {self.persona} | {response}\n")
        
        numbers = re.findall(r"([\d\.]+)", response)
        fallback_bid = float(numbers[-1]) if numbers else 0.0
        self.last_reasoning = f"(PARSE ERROR) {response}"
        
        return fallback_bid
