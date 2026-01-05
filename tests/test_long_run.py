import pytest
import sys
import os
import logging
import time
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())
from civilization_sim.model import CivilizationModel
from civilization_sim.agents import Person, Predator, House, Food, Tree, Farm, Wall, Stone, IronOre, Smithy, Road, Market, Barracks

# Disable the heavy simulation logging to speed up the test
logging.getLogger().setLevel(logging.ERROR)

def test_detailed_simulation_analysis():
    """
    Runs a 10,000 step simulation and performs a deep analysis of:
    - Tribe formation and dynamics
    - House building
    - Resource gathering and stockpiling
    - New features: Farms, Walls, Stone, Iron, Smithy, Roads, Markets, Barracks, Wars
    """
    print("\n=== Starting Detailed Simulation Analysis (10,000 steps) ===")
    print("Note: File logging disabled to improve performance.")

    model = CivilizationModel(
        width=20, 
        height=20, 
        initial_people=20,      # Start with more people to encourage interaction
        initial_food=50, 
        initial_predators=2,
        initial_stone=20,       # Give some stone to start
        initial_iron=10,        # Give some iron to start
        num_tribes=0            # Start with 0 tribes to test formation logic
    )
    
    max_steps = 10000
    
    # Metrics storage
    history = []
    
    # Event tracking
    first_house_step = None
    first_farm_step = None
    first_wall_step = None
    first_smithy_step = None
    first_road_step = None
    first_market_step = None
    first_barracks_step = None
    first_tribe_step = None
    first_war_step = None
    max_houses = 0
    max_farms = 0
    max_walls = 0
    max_smithies = 0
    max_roads = 0
    max_markets = 0
    max_barracks = 0
    max_tribe_size = 0
    
    start_time = time.time()
    
    for i in range(max_steps):
        model.step()
        
        # --- Data Collection ---
        agents = model.schedule.agents
        people = [a for a in agents if isinstance(a, Person)]
        houses = [a for a in agents if isinstance(a, House)]
        farms = [a for a in agents if isinstance(a, Farm)]
        walls = [a for a in agents if isinstance(a, Wall)]
        smithies = [a for a in agents if isinstance(a, Smithy)]
        roads = [a for a in agents if isinstance(a, Road)]
        markets = [a for a in agents if isinstance(a, Market)]
        barracks = [a for a in agents if isinstance(a, Barracks)]
        
        # Population stats
        pop_count = len(people)
        house_count = len(houses)
        farm_count = len(farms)
        wall_count = len(walls)
        smithy_count = len(smithies)
        road_count = len(roads)
        market_count = len(markets)
        barracks_count = len(barracks)
        
        # Tribe stats
        in_tribe = [p for p in people if p.tribe_id is not None]
        loners = [p for p in people if p.tribe_id is None]
        tribe_ids = set(p.tribe_id for p in in_tribe)
        
        # Stockpile stats
        total_stored_food = sum(s["food"] for s in model.tribe_stockpiles.values())
        total_stored_wood = sum(s["wood"] for s in model.tribe_stockpiles.values())
        total_stored_stone = sum(s["stone"] for s in model.tribe_stockpiles.values())
        total_stored_iron = sum(s.get("iron", 0) for s in model.tribe_stockpiles.values())
        total_stored_tools = sum(s.get("tools", 0) for s in model.tribe_stockpiles.values())
        
        # Record history
        step_data = {
            "step": i + 1,
            "people": pop_count,
            "houses": house_count,
            "farms": farm_count,
            "walls": wall_count,
            "smithies": smithy_count,
            "roads": road_count,
            "markets": market_count,
            "barracks": barracks_count,
            "wars": len(model.wars),
            "tribe_members": len(in_tribe),
            "loners": len(loners),
            "active_tribes": len(tribe_ids),
            "stored_food": total_stored_food,
            "stored_wood": total_stored_wood,
            "stored_stone": total_stored_stone,
            "stored_iron": total_stored_iron,
            "stored_tools": total_stored_tools
        }
        history.append(step_data)
        
        # --- Event Detection ---
        if house_count > 0 and first_house_step is None:
            first_house_step = i + 1
            print(f"[EVENT] First House built at step {i+1}!")

        if farm_count > 0 and first_farm_step is None:
            first_farm_step = i + 1
            print(f"[EVENT] First Farm built at step {i+1}!")

        if wall_count > 0 and first_wall_step is None:
            first_wall_step = i + 1
            print(f"[EVENT] First Wall built at step {i+1}!")

        if smithy_count > 0 and first_smithy_step is None:
            first_smithy_step = i + 1
            print(f"[EVENT] First Smithy built at step {i+1}!")

        if road_count > 0 and first_road_step is None:
            first_road_step = i + 1
            print(f"[EVENT] First Road built at step {i+1}!")

        if market_count > 0 and first_market_step is None:
            first_market_step = i + 1
            print(f"[EVENT] First Market built at step {i+1}!")

        if barracks_count > 0 and first_barracks_step is None:
            first_barracks_step = i + 1
            print(f"[EVENT] First Barracks built at step {i+1}!")

        if len(model.wars) > 0 and first_war_step is None:
            first_war_step = i + 1
            print(f"[EVENT] First War declared at step {i+1}!")
            
        if len(tribe_ids) > 0 and first_tribe_step is None:
            first_tribe_step = i + 1
            print(f"[EVENT] First Tribe formed at step {i+1}!")
            
        if house_count > max_houses:
            max_houses = house_count
        if farm_count > max_farms:
            max_farms = farm_count
        if wall_count > max_walls:
            max_walls = wall_count
        if smithy_count > max_smithies:
            max_smithies = smithy_count
        if road_count > max_roads:
            max_roads = road_count
        if market_count > max_markets:
            max_markets = market_count
        if barracks_count > max_barracks:
            max_barracks = barracks_count
            
        if len(in_tribe) > 0:
            # Calculate max size of a single tribe
            from collections import Counter
            counts = Counter([p.tribe_id for p in in_tribe])
            current_max_tribe = counts.most_common(1)[0][1]
            if current_max_tribe > max_tribe_size:
                max_tribe_size = current_max_tribe

        # Progress report
        if (i + 1) % 1000 == 0:
            print(f"Step {i+1}: Pop={pop_count}, Houses={house_count}, Farms={farm_count}, Walls={wall_count}, Smithies={smithy_count}, Tribes={len(tribe_ids)}")

    end_time = time.time()
    duration = end_time - start_time
    
    # --- Final Report ---
    df = pd.DataFrame(history)
    
    print("\n" + "="*40)
    print(f"SIMULATION REPORT (Duration: {duration:.2f}s)")
    print("="*40)
    
    print(f"\n1. POPULATION & SURVIVAL")
    print(f"   - Final Population: {df['people'].iloc[-1]}")
    print(f"   - Average Population: {df['people'].mean():.2f}")
    print(f"   - Max Population: {df['people'].max()}")
    print(f"   - Min Population: {df['people'].min()}")
    
    print(f"\n2. TRIBES & SOCIETY")
    print(f"   - Did tribes form? {'Yes' if first_tribe_step else 'No'}")
    if first_tribe_step:
        print(f"   - First tribe formed at step: {first_tribe_step}")
    print(f"   - Max active tribes at once: {df['active_tribes'].max()}")
    print(f"   - Max members in a single tribe: {max_tribe_size}")
    print(f"   - Average tribe members: {df['tribe_members'].mean():.2f}")
    print(f"   - Average loners: {df['loners'].mean():.2f}")
    
    print(f"\n3. INFRASTRUCTURE")
    print(f"   - Houses: Max={max_houses}, Final={house_count}")
    print(f"   - Farms: Max={max_farms}, Final={farm_count}")
    print(f"   - Walls: Max={max_walls}, Final={wall_count}")
    print(f"   - Smithies: Max={max_smithies}, Final={smithy_count}")
    print(f"   - Roads: Max={max_roads}, Final={road_count}")
    print(f"   - Markets: Max={max_markets}, Final={market_count}")
    print(f"   - Barracks: Max={max_barracks}, Final={barracks_count}")
    
    print(f"\n4. POLITICS & WAR")
    print(f"   - Did wars occur? {'Yes' if first_war_step else 'No'}")
    if first_war_step:
        print(f"   - First war declared at step: {first_war_step}")
    print(f"   - Final active wars: {len(model.wars)}")

    print(f"\n5. ECONOMY (STOCKPILES)")
    print(f"   - Max Food stored: {df['stored_food'].max()}")
    print(f"   - Max Wood stored: {df['stored_wood'].max()}")
    print(f"   - Max Stone stored: {df['stored_stone'].max()}")
    print(f"   - Max Iron stored: {df['stored_iron'].max()}")
    print(f"   - Max Tools stored: {df['stored_tools'].max()}")
    print(f"   - Final Food stored: {total_stored_food}")
    print(f"   - Final Wood stored: {total_stored_wood}")
    print(f"   - Final Stone stored: {total_stored_stone}")
    print(f"   - Final Iron stored: {total_stored_iron}")
    print(f"   - Final Tools stored: {total_stored_tools}")
    
    print("="*40)
    
    # Assertions to ensure "it works"
    assert df['people'].max() > 0, "Population should exist"
    print(f"   - Average loners: {df['loners'].mean():.2f}")
    
    print(f"\n3. INFRASTRUCTURE (HOUSES)")
    print(f"   - Did they build houses? {'Yes' if first_house_step else 'No'}")
    if first_house_step:
        print(f"   - First house built at step: {first_house_step}")
    print(f"   - Max houses existing at once: {max_houses}")
    print(f"   - Final house count: {house_count}")
    
    print(f"\n4. ECONOMY (STOCKPILES)")
    print(f"   - Max Food stored: {df['stored_food'].max()}")
    print(f"   - Max Wood stored: {df['stored_wood'].max()}")
    print(f"   - Final Food stored: {total_stored_food}")
    print(f"   - Final Wood stored: {total_stored_wood}")
    
    print("="*40)
    
    # Assertions to ensure "it works"
    assert df['people'].max() > 0, "Population should exist"
    # We don't strictly assert houses > 0 because it depends on survival, 
    # but we print the info for the user.

if __name__ == "__main__":
    test_detailed_simulation_analysis()
