# basic config for the sim
NUM_ROUNDS = 50
NUM_NON_LLM_AGENTS = 3
MIN_TRUE_VALUE = 0.0
MAX_TRUE_VALUE = 100.0

# different types of agents
AGENT_TRUTHFUL = "Truthful"
AGENT_STRATEGIC = "Strategic"
AGENT_RANDOM = "Random"
AGENT_LLM = "LLM"

# first vs second price setup
AUCTION_FIRST_PRICE = "First-Price"
AUCTION_SECOND_PRICE = "Second-Price"

# characters for the LLM
PERSONA_HONEST = "honest"
PERSONA_PROFIT_MAX = "profit-maximizing"
PERSONA_RISK_AVERSE = "risk-averse"
PERSONA_RISK_SEEKING = "risk-seeking"

# using gpt-4o by default
MODEL_DEFAULT = "gpt-4o"

# sticking the key here for convenience
OPENAI_API_KEY = "your-api-key-here"
