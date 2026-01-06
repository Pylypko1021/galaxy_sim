import pytest
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person, Predator, Barbarian
from civilization_sim.new_agents.resources import Tree, Food
from civilization_sim.new_agents.buildings import House

def test_tribe_formation():
    # 1. Create a model with num_tribes=0, so all agents start as loners
    model = CivilizationModel(initial_people=2, num_tribes=0, initial_food=0, initial_trees=0, initial_predators=0)
    
    # 2. Verify all initial agents are loners
    agents = [a for a in model.schedule.agents if isinstance(a, Person)]
    assert len(agents) == 2
    p1 = agents[0]
    p2 = agents[1]
    assert p1.tribe_id is None
    assert p2.tribe_id is None
    
    # 3. Place two loners on the same cell
    model.grid.move_agent(p1, (5, 5))
    model.grid.move_agent(p2, (5, 5))
    
    # 4. Run the model for one step
    model.step()
    
    # 5. Verify they now have the same, non-None tribe_id
    assert p1.tribe_id is not None
    assert p1.tribe_id == p2.tribe_id
    
    # 6. Verify the model has a new tribe color and stockpile for them
    new_tribe_id = p1.tribe_id
    assert new_tribe_id in model.tribe_stockpiles
    assert len(model.tribe_colors) == 1

def test_resource_sharing():
    # 1. Create a model with one tribe and one person
    model = CivilizationModel(initial_people=1, num_tribes=1, initial_food=0, initial_trees=0, initial_predators=0)
    # Get the person agent, filtering out any other agent types that might be in the schedule
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    tribe_id = person.tribe_id
    assert tribe_id == 0
    
    # 2. Place the person and a tree on the same cell
    tree = Tree(model)
    model.schedule.add(tree) # Add tree to schedule to allow removal
    model.grid.move_agent(person, (5, 5))
    model.grid.place_agent(tree, (5, 5))
    
    # 3. Run one step and verify wood is added to stockpile
    model.step()
    # Updated to >= 1 because leader bonus might apply (adding +1)
    assert model.tribe_stockpiles[tribe_id]["wood"] >= 1
    
    # 4. Set person's energy low and give the tribe food
    person.energy = 10
    model.tribe_stockpiles[tribe_id]["food"] = 15
    
    # 5. Run another step and verify the person withdrew food
    model.step()
    # Energy should be 10 (start) - 1 (cost of living) + 15 (withdrew) = 24
    assert person.energy == 24
    assert model.tribe_stockpiles[tribe_id]["food"] == 0

def test_trading():
    # 1. Create a model with two tribes
    model = CivilizationModel(initial_people=2, num_tribes=2, initial_predators=0, initial_food=0, initial_trees=0)
    p1 = [a for a in model.schedule.agents if isinstance(a, Person) and a.tribe_id == 0][0]
    p2 = [a for a in model.schedule.agents if isinstance(a, Person) and a.tribe_id == 1][0]
    
    # 2. Give Tribe 0 a surplus of food and Tribe 1 a surplus of wood
    model.tribe_stockpiles[0]["food"] = 110
    model.tribe_stockpiles[1]["wood"] = 30
    
    # 3. Place the agents on the same cell and set properties to ensure trade
    model.grid.move_agent(p1, (5, 5))
    model.grid.move_agent(p2, (5, 5))
    
    p1.energy = 60 # Prevent withdrawal from stockpile
    p2.energy = 60
    p1.profession = "Merchant" # Prioritize trade
    p2.profession = "Merchant"

    # 4. Run one step
    model.step()
    
    # 5. Verify the trade happened (10 food for 1 wood)
    assert model.tribe_stockpiles[0]["food"] == 100
    assert model.tribe_stockpiles[0]["wood"] == 1
    assert model.tribe_stockpiles[1]["food"] == 10
    # Tribe 1 had 30 wood, traded 1 away (29 left). 
    # The agent is a Merchant, so it prioritizes trading over building.
    assert model.tribe_stockpiles[1]["wood"] == 29

def test_pack_hunting():
    model = CivilizationModel(initial_people=1, initial_predators=3, num_predator_packs=1)
    person = [a for a in model.schedule.agents if isinstance(a, Person)][0]
    predators = [a for a in model.schedule.agents if isinstance(a, Predator)]

    # 2. Place the person in a house
    house = House(model)
    model.schedule.add(house)
    model.grid.move_agent(person, (5, 5))
    model.grid.place_agent(house, (5, 5))

    # 3. Place two predators on the same cell; person should be safe
    model.grid.move_agent(predators[0], (5, 5))
    model.grid.move_agent(predators[1], (5, 5))

    model.step()
    
    # Verify the person survived (was not eaten)
    assert person in model.schedule.agents
    # Also verify that predators are blocked (optional, but implied by survival if they are on same cell)
    cell_contents = model.grid.get_cell_list_contents([(5, 5)])
    assert person in cell_contents
