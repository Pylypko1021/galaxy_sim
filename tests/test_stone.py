import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person
from civilization_sim.new_agents.resources import Stone

def test_stone_gathering():
    """Test that agents gather stone."""
    model = CivilizationModel(initial_people=1, num_tribes=1, initial_food=0, initial_trees=0, initial_predators=0, initial_stone=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    tribe_id = person.tribe_id
    
    # Place stone on same cell
    stone = Stone(model)
    model.schedule.add(stone)
    model.grid.place_agent(stone, person.pos)
    
    model.step()
    
    # Stone should be gathered
    # >= 1 because of potential bonuses (Person might be Leader)
    assert model.tribe_stockpiles[tribe_id]["stone"] >= 1
    
    # The specific stone agent should be removed
    # We can check if the stone object is still in the schedule
    assert stone not in model.schedule.agents

def test_stone_generation():
    """Test that stone is generated initially."""
    model = CivilizationModel(initial_stone=10)
    stone_count = len([a for a in model.schedule.agents if isinstance(a, Stone)])
    assert stone_count == 10
