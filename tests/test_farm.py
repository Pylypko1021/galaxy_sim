import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person
from civilization_sim.new_agents.resources import Food
from civilization_sim.new_agents.buildings import Farm

def test_farm_building():
    """Test that agents build farms when resources are available."""
    model = CivilizationModel(initial_people=1, num_tribes=1, initial_food=0, initial_trees=0, initial_predators=0, initial_stone=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    tribe_id = person.tribe_id
    
    # Give resources
    model.tribe_stockpiles[tribe_id]["wood"] = 5
    model.tribe_stockpiles[tribe_id]["stone"] = 5
    model.tribe_stockpiles[tribe_id]["food"] = 0 # Low food triggers farm building
    
    model.step()
    
    # Farm should be built
    # Note: The agent moves AFTER building, so we need to check the position where they WERE
    # Or, since we don't know exactly where they moved, we can check the whole grid or schedule
    farms = [a for a in model.schedule.agents if isinstance(a, Farm)]
    assert len(farms) == 1
    
    # Resources consumed
    assert model.tribe_stockpiles[tribe_id]["wood"] == 3
    assert model.tribe_stockpiles[tribe_id]["stone"] == 3

def test_farm_production():
    """Test that farms produce food over time."""
    model = CivilizationModel(initial_people=0, num_tribes=0, initial_food=0, initial_trees=0, initial_predators=0, initial_stone=0)
    
    # Place a farm
    farm = Farm(model, tribe_id=0)
    model.schedule.add(farm)
    model.grid.place_agent(farm, (5, 5))
    
    # Run steps
    # Threshold is 10. 
    for _ in range(9):
        model.step()
        
    # Should be no food yet
    cell_mates = model.grid.get_cell_list_contents([(5, 5)])
    food = [a for a in cell_mates if isinstance(a, Food)]
    assert len(food) == 0
    
    # 10th step
    model.step()
    
    # Should be food now
    cell_mates = model.grid.get_cell_list_contents([(5, 5)])
    food = [a for a in cell_mates if isinstance(a, Food)]
    assert len(food) == 1
