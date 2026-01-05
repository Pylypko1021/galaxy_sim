import sys
import os
import logging

# Add current directory to sys.path
sys.path.append(os.getcwd())

from civilization_sim.model import CivilizationModel

# Configure logging to print to stdout for this check
logging.basicConfig(level=logging.INFO, format='%(message)s')

print("Starting balanced simulation check...")

# Initialize model with enough people to potentially trigger splitting eventually
model = CivilizationModel(width=30, height=30, initial_people=40, initial_food=100, initial_predators=2)

# Run for 500 steps
for i in range(500):
    model.step()
    
    if i % 50 == 0:
        tribes = model.tribe_counts
        print(f"Step {i}: {len(tribes)} tribes. Counts: {tribes}")
        # Check if we have too many tribes
        if len(tribes) > 10:
            print("WARNING: Too many tribes formed!")
            break

print("Simulation finished.")
