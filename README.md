# Ad Auction LLM Sim

A quick project to see how LLMs handle different auction types. Basically, do they know when to be honest (top-tier strategy for second-price auctions) and when to "shade" their bids (first-price auctions)? 

I also threw in a budget experiment to see if they panic when they're running out of money.

## What's in here?

* **Exp 1: Strategy.** This is the basic test. I run a bunch of rounds and see how gpt-4o bids in first-price vs second-price auctions. It also has some logic to change its strategy if it's on a losing streak.
* **Exp 2: Budgets.** Everyone gets $500. If you run out, you're done. There's a "crisis mode" where the LLM gets extra careful if its budget drops below 10%.
* **Agents.** I've got a baseline honest agent, a strategic one that just bids 70% of value, and some random ones for noise.

## Structure

* `run_simulation.py`: the main script for the first experiment.
* `budget_experiment/`: scripts for the budget-limited runs.
* `agents/`: code for the different types of bidders.
* `data/`: where all the CSVs end up.
* `analysis/`: scripts to make some graphs from the data.

## How to run it

I made a bash script to just run everything at once:

```bash
chmod +x run_all_experiments.sh
./run_all_experiments.sh
```

Make sure you have your `OPENAI_API_KEY` set in `config.py` (or as an env var).

## Results

After it finishes, check the `analysis/plots` folder. It should generate some scatter plots and histograms showing how the LLM behaved compared to its true value.
