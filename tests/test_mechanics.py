import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.agents import Person, Predator, Food

def test_starvation():
    """Test that agents die when energy reaches 0."""
    # Setup model with 1 person, no food
    model = CivilizationModel(initial_people=1, num_tribes=0, initial_food=0, initial_trees=0, initial_predators=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    person_id = person.unique_id
    
    # Set energy to 1. Next step it will drop to 0 and they should die.
    person.energy = 1
    
    model.step()
    
    # Verify the specific person is removed from schedule
    agents_ids = [a.unique_id for a in model.schedule.agents]
    assert person_id not in agents_ids

def test_reproduction():
    """Test that agents reproduce when energy is high enough."""
    model = CivilizationModel(initial_people=1, num_tribes=1, initial_food=0, initial_trees=0, initial_predators=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    
    # Set energy above reproduction threshold (40)
    person.energy = 50
    
    model.step()
    
    # Verify population increased (original + child + maybe migrants)
    # We just want to ensure it's at least 2 and the parent lost energy
    people = [a for a in model.schedule.agents if isinstance(a, Person)]
    assert len(people) >= 2
    
    # Verify parent lost energy (cost is 25)
    # Parent had 50, lost 1 (living), lost 25 (baby) = 24 approx
    # We need to find the parent again
    parent = next((p for p in people if p.unique_id == person.unique_id), None)
    assert parent is not None
    assert parent.energy < 30

def test_food_gathering():
    """Test that agents gain energy from food."""
    model = CivilizationModel(initial_people=1, num_tribes=0, initial_food=0, initial_trees=0, initial_predators=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    
    # Set energy low enough so they don't reproduce after eating
    person.energy = 20
    initial_energy = person.energy
    
    # Place food on same cell
    food = Food(model)
    food_id = food.unique_id
    model.schedule.add(food)
    model.grid.place_agent(food, person.pos)
    
    model.step()
    
    # Person should have eaten the food (+15 energy) and lost 1 living cost
    # 20 - 1 + 15 = 34
    assert person.energy == 34
    
    # The specific food item should be gone
    agents_ids = [a.unique_id for a in model.schedule.agents]
    assert food_id not in agents_ids
