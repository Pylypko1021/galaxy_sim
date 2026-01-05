
import sys
import os
import logging
import random
from civilization_sim.model import CivilizationModel
from civilization_sim.agents import Person, Barracks

# Configure logging to file, but we will print major events manually
logging.basicConfig(
    filename='global_simulation.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def run_simulation():
    print("=== Initializing Global Simulation ===")
    width = 50
    height = 50
    initial_people = 100
    steps = 3000
    
    model = CivilizationModel(
        width=width, 
        height=height, 
        initial_people=initial_people,
        initial_food=300, 
        initial_predators=5,
        initial_trees=200,
        initial_stone=100,
        initial_iron=50,
        num_tribes=5,
        num_predator_packs=3
    )

    print(f"Map Size: {width}x{height}")
    print(f"Initial Population: {initial_people}")
    print(f"Initial Tribes: 5")
    print(f"Simulation Length: {steps} steps")
    print("-" * 40)

    # Track history
    war_history = set()
    split_history = []
    max_pop = 0
    
    # We need to hook into the logging or check state changes to report events
    # Since we can't easily hook logging in this script without modifying the model,
    # we will monitor state changes.

    previous_tribes = set(model.tribe_stockpiles.keys())
    previous_wars = set()

    for i in range(steps):
        model.step()
        
        # 1. Check for new wars
        current_wars = model.wars.copy()
        new_wars = current_wars - previous_wars
        ended_wars = previous_wars - current_wars
        
        for w in new_wars:
            t1, t2 = w
            print(f"[Step {i}] WAR DECLARED: Tribe {t1} vs Tribe {t2}")
            war_history.add(w)
            
        for w in ended_wars:
            t1, t2 = w
            print(f"[Step {i}] PEACE TREATY: Tribe {t1} and Tribe {t2}")
            
        previous_wars = current_wars

        # 2. Check for new tribes (Splits)
        current_tribes = set(model.tribe_stockpiles.keys())
        new_tribes = current_tribes - previous_tribes
        for t in new_tribes:
            # Find who they split from or if they are new
            # It's hard to know exactly who they split from without looking at logs, 
            # but we can just announce the new tribe.
            trait = model.tribe_traits.get(t, "Unknown")
            print(f"[Step {i}] NEW TRIBE FORMED: Tribe {t} (Trait: {trait})")
            split_history.append(t)
            
        previous_tribes = current_tribes

        # 3. Periodic Status Update
        if i % 100 == 0:
            pop = sum(1 for a in model.schedule.agents if isinstance(a, Person))
            max_pop = max(max_pop, pop)
            barracks = sum(1 for a in model.schedule.agents if isinstance(a, Barracks))
            active_wars = len(model.wars)
            print(f"Step {i}: Pop={pop}, Tribes={len(current_tribes)}, Active Wars={active_wars}, Barracks={barracks}")

    print("-" * 40)
    print("=== Simulation Complete ===")
    print(f"Final Population: {sum(1 for a in model.schedule.agents if isinstance(a, Person))}")
    print(f"Max Population: {max_pop}")
    print(f"Total Wars Fought: {len(war_history)}")
    print(f"Total Tribe Splits: {len(split_history)}")
    
    # Print Tribe Stats
    print("\nFinal Tribe Statistics:")
    for t_id, stock in model.tribe_stockpiles.items():
        count = model.tribe_counts.get(t_id, 0)
        trait = model.tribe_traits.get(t_id, "None")
        leader = model.tribe_leaders.get(t_id, "None")
        print(f"Tribe {t_id} ({trait}): {count} members. Stock: Food={stock['food']}, Wood={stock['wood']}, Stone={stock['stone']}, Iron={stock['iron']}, Tools={stock['tools']}")

if __name__ == "__main__":
    run_simulation()
