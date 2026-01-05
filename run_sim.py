import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from civilization_sim.model import CivilizationModel

print("Starting simulation... Logs are being written to simulation.log")

# Initialize model
model = CivilizationModel(width=20, height=20, initial_people=20, initial_food=50, initial_predators=2)

# Run for 10000 steps
for i in range(10000):
    model.step()
    # Print progress to terminal so user knows it's working
    if i % 1000 == 0:
        print(f"Simulating step {i}...")

print("Simulation finished! You can now open simulation.log to see the results.")