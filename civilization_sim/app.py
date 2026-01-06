import sys
import os
# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person, Predator, Barbarian
from civilization_sim.new_agents.resources import Food, Tree, Stone, IronOre, Mountain, River
from civilization_sim.new_agents.buildings import House, Farm, Wall, Smithy, Road, Market, Barracks, Library, Hospital, Temple, Tavern

def agent_portrayal(agent):
    image = None
    color = "black"
    marker = "o"
    size = 50
    layer = 1

    # Base Resource Paths
    # Solara serves files in 'public' folder at the root path or /static
    # We moved Resources to civilization_sim/public/Resources
    base_unit_path = "/static/public/Resources/Units"
    base_building_path = "/static/public/Resources/Buildings"
    base_terrain_path = "/static/public/Resources/Terrain"

    if isinstance(agent, Person):
        layer = 2
        tribe_color = agent.model.tribe_colors[agent.tribe_id % len(agent.model.tribe_colors)] if agent.tribe_id is not None and hasattr(agent.model, 'tribe_colors') and agent.model.tribe_colors else "Blue"
        if tribe_color.startswith("#"): # Fallback if hex
            tribe_color = "Blue"
        
        # Determine Unit Type based on profession
        unit_type = "Pawn"
        action = "Idle"
        if hasattr(agent, "profession"):
             if agent.profession in ["Soldier", "Guard"]:
                 unit_type = "Warrior"
             elif agent.profession == "Archer":
                 unit_type = "Archer"
             elif agent.profession in ["Priest", "Healer", "Scholar"]:
                 unit_type = "Monk"
        
        # Construct Path: Resources/Units/Blue Units/Pawn/Pawn_Idle.png
        # Note: Folder names are like "Blue Units"
        image = f"{base_unit_path}/{tribe_color} Units/{unit_type}/{unit_type}_{action}.png"
        size = 40

    elif isinstance(agent, Barbarian):
        layer = 2
        image = f"{base_unit_path}/Red Units/Warrior/Warrior_Idle.png" # Barbarians as Red Warriors
        size = 40

    elif isinstance(agent, Predator):
        layer = 2
        # Use Sheep as placeholder? No, Sheep is prey. Maybe just a generic icon or "Red Units/Pawn"
        # Or no image, just shape.
        # Check if we have Wolves? No.
        # Let's use Red Units/Pawn/Pawn_Run.png
        image = f"{base_unit_path}/Red Units/Pawn/Pawn_Run.png"
        size = 35

    elif isinstance(agent, Food):
        layer = 1
        # Sheep is Food source
        image = f"{base_terrain_path}/Resources/Meat/Sheep/Sheep_Idle.png"
        size = 30
    
    elif isinstance(agent, Tree):
        layer = 1
        image = f"{base_terrain_path}/Resources/Wood/Trees/Tree1.png"
        size = 50

    elif isinstance(agent, Stone):
        layer = 1
        image = f"{base_terrain_path}/Decorations/Rocks/Rock1.png"
        size = 40

    elif isinstance(agent, IronOre):
        layer = 1
        image = f"{base_terrain_path}/Resources/Gold/Gold Stones/Gold Stone 1.png"
        size = 40

    elif isinstance(agent, Mountain):
        layer = 0
        image = f"{base_terrain_path}/Decorations/Rocks/Rock4.png" # Big rock
        size = 80
    
    elif isinstance(agent, House):
        layer = 1
        tribe_color = agent.model.tribe_colors[agent.tribe_id % len(agent.model.tribe_colors)] if agent.tribe_id is not None and hasattr(agent.model, 'tribe_colors') and agent.model.tribe_colors else "Blue"
        if tribe_color.startswith("#"): tribe_color = "Blue"
        image = f"{base_building_path}/{tribe_color} Buildings/House1.png"
        size = 60

    elif isinstance(agent, Farm):
        layer = 1
        # Use Bushes for basic farm look
        image = f"{base_terrain_path}/Decorations/Bushes/Bushe1.png"
        size = 50
    
    elif isinstance(agent, Wall):
        layer = 1
        tribe_color = "Blue" # Walls often neutral or specific to tribe. Use tribe logic if Wall has tribe_id? Wall inherits nothing usually.
        # But wait, Wall has no tribe_id in init?
        # Use generic Tower
        image = f"{base_building_path}/Blue Buildings/Tower.png"
        size = 60
    
    elif isinstance(agent, (Barracks, Smithy, Market, Library, Hospital, Temple, Tavern)):
        layer = 1
        tribe_color = agent.model.tribe_colors[agent.tribe_id % len(agent.model.tribe_colors)] if agent.tribe_id is not None and hasattr(agent.model, 'tribe_colors') and agent.model.tribe_colors else "Blue"
        if tribe_color.startswith("#"): tribe_color = "Blue"
        
        building_img = "House2.png"
        if isinstance(agent, Barracks): building_img = "Barracks.png"
        elif isinstance(agent, Temple): building_img = "Monastery.png"
        elif isinstance(agent, Library): building_img = "Monastery.png" # Use Monastery for Library too
        elif isinstance(agent, Smithy): building_img = "Archery.png" # Placeholder
        elif isinstance(agent, Market): building_img = "Castle.png" # Castle as Market/Center
        
        image = f"{base_building_path}/{tribe_color} Buildings/{building_img}"
        size = 70

    return {
        "color": color,   # Fallback
        "marker": marker, # Fallback
        "size": size,
        "image": image,   # Image Path
    }

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 40,
        "label": "Ширина",
        "min": 10,
        "max": 50,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 30,
        "label": "Висота",
        "min": 10,
        "max": 50,
        "step": 1,
    },
    "initial_people": {
        "type": "SliderInt",
        "value": 50,
        "label": "Кількість людей",
        "min": 1,
        "max": 200,
        "step": 1,
    },
    "num_tribes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Кількість племен",
        "min": 0,
        "max": 5,
        "step": 1,
    },
    "initial_predators": {
        "type": "SliderInt",
        "value": 2,
        "label": "Кількість хижаків",
        "min": 0,
        "max": 20,
        "step": 1,
    },
    "num_predator_packs": {
        "type": "SliderInt",
        "value": 1,
        "label": "Кількість зграй хижаків",
        "min": 0,
        "max": 10,
        "step": 1,
    },
    "initial_food": {
        "type": "SliderInt",
        "value": 50,
        "label": "Початкова їжа",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "initial_trees": {
        "type": "SliderInt",
        "value": 30,
        "label": "Початкова кількість дерев",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "initial_stone": {
        "type": "SliderInt",
        "value": 10,
        "label": "Початкова кількість каміння",
        "min": 0,
        "max": 50,
        "step": 1,
    },
    "initial_iron": {
        "type": "SliderInt",
        "value": 5,
        "label": "Початкова кількість заліза",
        "min": 0,
        "max": 20,
        "step": 1,
    },
}

model = CivilizationModel()

page = SolaraViz(
    model,
    components=[
        make_space_component(agent_portrayal),
        # Removed plots to maximize space for the grid
    ],
    model_params=model_params,
    name="Симуляція Цивілізації",
    play_interval=0  # Maximum speed (no delay)
)
