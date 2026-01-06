import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person, Predator
from civilization_sim.new_agents.buildings import Wall, House

def test_wall_building():
    """Test that agents build walls near other buildings."""
    model = CivilizationModel(initial_people=1, num_tribes=1, initial_food=0, initial_trees=0, initial_predators=0, initial_stone=0)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    tribe_id = person.tribe_id
    
    # Place a house nearby (at 5,5)
    house = House(model)
    model.schedule.add(house)
    model.grid.place_agent(house, (5, 5))
    
    # Place person next to house (at 5,6)
    model.grid.move_agent(person, (5, 6))
    
    # Give resources
    model.tribe_stockpiles[tribe_id]["stone"] = 30
    
    model.step()
    
    # Wall should be built at person's position
    cell_mates = model.grid.get_cell_list_contents([(5, 6)])
    walls = [a for a in cell_mates if isinstance(a, Wall)]
    assert len(walls) == 1
    
    # Resources consumed
    assert model.tribe_stockpiles[tribe_id]["stone"] == 0

def test_wall_blocking():
    """Test that predators cannot move through walls."""
    model = CivilizationModel(initial_people=1, num_tribes=0, initial_food=0, initial_trees=0, initial_predators=1, initial_stone=0)
    predator = [a for a in model.schedule.agents if isinstance(a, Predator)][0]
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    
    # Setup: Predator at (5,5), Person at (5,7)
    # Wall at (5,6) blocking the path
    model.grid.move_agent(predator, (5, 5))
    model.grid.move_agent(person, (5, 7))
    
    wall = Wall(model)
    model.schedule.add(wall)
    model.grid.place_agent(wall, (5, 6))
    
    # Run step
    model.step()
    
    # Predator should NOT be at (5,6)
    assert predator.pos != (5, 6)
    
    # Predator should still be close (didn't teleport)
    # Note: Predator moves 1 step. If it was at (5,5), it could move to (4,5), (6,5), (5,4).
    # Distance from (5,5) should be 1.
    # If it stayed put (trapped), distance is 0.
    # If it moved diagonally (Moore neighborhood), distance is 2 (e.g. 4,4).
    # The test failed with dist=2, meaning it moved diagonally or 2 steps?
    # Ah, Moore neighborhood allows diagonal movement! (5,5) -> (6,6) is 1 step but Manhattan dist is 2.
    # Let's check Chebyshev distance (max(dx, dy)) which is 1 for Moore neighbors.
    chebyshev_dist = max(abs(predator.pos[0] - 5), abs(predator.pos[1] - 5))
    assert chebyshev_dist <= 1
