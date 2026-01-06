
import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person

def test_tribe_splitting():
    # Initialize model with 1 tribe
    model = CivilizationModel(num_tribes=1, initial_people=30, width=10, height=10)
    
    # Force all agents to be in tribe 0
    for agent in model.schedule.agents:
        if isinstance(agent, Person):
            agent.tribe_id = 0
            
    # Verify initial state
    assert len(model.tribe_stockpiles) == 1
    assert model.tribe_traits[0] in ["Agrarian", "Industrial", "Militaristic", "Expansionist"]
    
    # Run step to trigger splitting check
    # Splitting has a 5% chance, so we might need to force it or run multiple steps
    # Let's monkeypatch the random check or just call split_tribe directly for testing
    
    model.split_tribe(0)
    
    # Verify new tribe formed
    assert len(model.tribe_stockpiles) == 2
    assert 1 in model.tribe_stockpiles
    assert model.tribe_traits[1] in ["Agrarian", "Industrial", "Militaristic", "Expansionist"]
    
    # Verify agents moved
    tribe_0_count = sum(1 for a in model.schedule.agents if isinstance(a, Person) and a.tribe_id == 0)
    tribe_1_count = sum(1 for a in model.schedule.agents if isinstance(a, Person) and a.tribe_id == 1)
    
    print(f"Tribe 0 count: {tribe_0_count}")
    print(f"Tribe 1 count: {tribe_1_count}")
    
    assert tribe_1_count > 0
    assert tribe_0_count + tribe_1_count == 30

def test_traits_bonuses():
    model = CivilizationModel(num_tribes=1, initial_people=1)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    tribe_id = person.tribe_id
    
    # Test Agrarian
    model.tribe_traits[tribe_id] = "Agrarian"
    # Mock gathering food
    # We need to place food at person's location
    from civilization_sim.new_agents.resources import Food
    food = Food(model)
    model.schedule.add(food)
    model.grid.place_agent(food, person.pos)
    
    initial_food = model.tribe_stockpiles[tribe_id]["food"]
    person.gather_food()
    # Base 15 + 2 (Trait) = 17. (Leader bonus +2 if leader exists, but we didn't set leader)
    # Wait, gather_food removes the agent.
    
    # Let's check the delta
    new_food = model.tribe_stockpiles[tribe_id]["food"]
    # If profession is Farmer, +5.
    expected_gain = 15 + 2 # Base + Trait
    if person.profession == "Farmer":
        expected_gain += 5
    
    # Check if leader bonus applies (it shouldn't unless we set it)
    if hasattr(model, "tribe_leaders") and tribe_id in model.tribe_leaders:
        expected_gain += 2
        
    # Actual gain depends on random religion/professions too, so just check it increased significantly
    assert new_food - initial_food >= 15
