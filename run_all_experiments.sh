#!/bin/bash

# setup folders
mkdir -p data
mkdir -p analysis
mkdir -p budget_experiment/analysis/plots

# wipe old results so we start fresh
rm -f data/results.csv
rm -f data/budget_results.csv
rm -f data/reasoning_logs.csv
rm -f data/budget_reasoning_logs.csv

# the different personas we want to test
PERSONAS=("honest" "profit-maximizing" "risk-averse" "risk-seeking")

echo "-------------------------------------------"
echo "Running all experiments..."
echo "-------------------------------------------"

for persona in "${PERSONAS[@]}"; do
    echo ""
    echo ">> Persona: $persona"
    
    echo "   Running Exp 1 (standard)..."
    python3 run_simulation.py --rounds 50 --persona "$persona"
    
    echo "   Running Exp 2 (budget limited)..."
    python3 budget_experiment/run_budget_simulation.py --rounds 50 --budget 500 --persona "$persona"
done


echo ""
echo "-------------------------------------------"
echo "Crunching numbers and making plots"
echo "-------------------------------------------"

# get the stats
python3 analysis/exp1_metrics.py
python3 budget_experiment/analysis/exp2_metrics.py

# generate the graphs
python3 analysis/graphs.py
python3 budget_experiment/analysis/graphs_budget.py

echo ""
echo "Done! check the analysis folders for the graphs."
