import sys
import os

# Add the project root directory to sys.path to ensure module resolution works
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mesa.visualization import SolaraViz, make_space_component
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person, Predator, Barbarian
from civilization_sim.new_agents.resources import Food, Tree, Stone, IronOre, Mountain, River
from civilization_sim.new_agents.buildings import House, Farm, Wall, Smithy, Road, Market, Barracks, Library, Hospital, Temple, Tavern

# --- Path Management & Constants ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "public", "Resources")

# Map tribe_id (int) to Folder Name Strings
TRIBE_COLOR_MAP = {
    0: "Blue",
    1: "Red",
    2: "Yellow",
    3: "Purple",
    4: "Black"
}

def get_sprite(*parts):
    """
    Constructs a file path from parts, checks if the file exists locally,
    and returns the web-accessible static URL if it does.
    """
    # 1. Check local file existence logic
    local_path = os.path.join(RESOURCE_DIR, *parts)
    
    if os.path.exists(local_path):
        # 2. Return Web URL
        # Solara serves "public" folder at root
        url_suffix = "/".join(parts)
        return f"/static/public/Resources/{url_suffix}"
    else:
        # print(f"Warning: Sprite missing at {local_path}")
        return None

def agent_portrayal(agent):
    """
    Translates an agent into a portrayal dictionary for visualization.
    Uses pixel art sprites where available, falling back to shapes.
    """
    portrayal = {
        "x": agent.pos[0],
        "y": agent.pos[1],
    }

    image_url = None
    
    # --- 1. People (Layer 3) ---
    if isinstance(agent, Person):
        # Determine Tribe Color Folder
        # Default to Blue if tribe_id is None or out of range
        tribe_id = getattr(agent, "tribe_id", 0)
        # Ensure tribe_id is an integer (handle potential None)
        if tribe_id is None:
            tribe_id = 0
        tribe_color = TRIBE_COLOR_MAP.get(tribe_id % 5, "Blue") 
        tribe_dir = f"{tribe_color} Units"
        
        # Determine specific sprite based on Profession
        profession = getattr(agent, "profession", "None") # Default to None string if attr missing
        
        if profession == "Farmer":
            # Priority: Wood, then Axe, then Standard
            image_url = get_sprite("Units", tribe_dir, "Pawn", "Pawn_Idle Wood.png") or \
                        get_sprite("Units", tribe_dir, "Pawn", "Pawn_Idle Axe.png")
        
        elif profession == "Miner":
             image_url = get_sprite("Units", tribe_dir, "Pawn", "Pawn_Idle Pickaxe.png")
        
        elif profession in ["Guard", "Soldier"]:
             image_url = get_sprite("Units", tribe_dir, "Warrior", "Warrior_Idle.png")
        
        elif profession == "Archer":
             image_url = get_sprite("Units", tribe_dir, "Archer", "Archer_Idle.png")
        
        elif profession in ["Priest", "Healer"]:
             image_url = get_sprite("Units", tribe_dir, "Monk", "Idle.png")
        
        # Default / Fallback for Person
        if image_url is None:
             image_url = get_sprite("Units", tribe_dir, "Pawn", "Pawn_Idle.png")

        # Portrayal attributes
        portrayal["size"] = 55
        portrayal["layer"] = 3
        
        # Fallback Geometry if sprite still missing
        if image_url is None:
            portrayal["color"] = tribe_color.lower()
            portrayal["marker"] = "o"

    # --- 2. Buildings (Layer 2) ---
    elif isinstance(agent, (House, Barracks, Smithy, Temple, Hospital, Library, Wall, Farm)):
        # Building Color Map (Buildings have an owner/tribe too usually)
        tribe_id = getattr(agent, "tribe_id", 0) 
        if tribe_id is None: tribe_id = 0
        tribe_color = TRIBE_COLOR_MAP.get(tribe_id % 5, "Blue")
        building_dir = f"{tribe_color} Buildings"
        
        if isinstance(agent, (House, Farm)): # Farm often visualized as house in this asset packs
            image_url = get_sprite("Buildings", building_dir, "House1.png")
        elif isinstance(agent, Barracks):
            image_url = get_sprite("Buildings", building_dir, "Barracks.png")
        elif isinstance(agent, Smithy):
            image_url = get_sprite("Buildings", building_dir, "Archery.png") # Placeholder as requested
        elif isinstance(agent, (Temple, Hospital, Library)):
            image_url = get_sprite("Buildings", building_dir, "Monastery.png")
        elif isinstance(agent, Wall): # Using Tower for wall as requested
            image_url = get_sprite("Buildings", building_dir, "Tower.png")
        # TownCenter isn't imported from buildings specifically, but if it was:
        # elif isinstance(agent, TownCenter): image_url = get_sprite("Buildings", building_dir, "Castle.png")

        portrayal["size"] = 80
        portrayal["layer"] = 2
        
        # Fallback Geometry
        if image_url is None:
            portrayal["color"] = tribe_color.lower()
            portrayal["marker"] = "s" # square

    # --- 3. Nature & Resources (Layer 1) ---
    else:
        portrayal["layer"] = 1
        
        if isinstance(agent, Tree):
            image_url = get_sprite("Terrain", "Resources", "Wood", "Trees", "Tree1.png")
            portrayal["size"] = 90
        
        elif isinstance(agent, Stone):
            image_url = get_sprite("Terrain", "Decorations", "Rocks", "Rock1.png")
            portrayal["size"] = 50
        
        elif isinstance(agent, IronOre):
            image_url = get_sprite("Terrain", "Resources", "Gold", "Gold Stones", "Gold Stone 1.png")
            portrayal["size"] = 40
            
        elif isinstance(agent, Food):
            image_url = get_sprite("Terrain", "Decorations", "Bushes", "Bushe1.png")
            portrayal["size"] = 45
            
        elif isinstance(agent, Predator):
             # Try Sheep first
             image_url = get_sprite("Terrain", "Resources", "Meat", "Sheep", "Sheep_Idle.png")
             # Fallback to bandit pawn
             if image_url is None:
                 image_url = get_sprite("Units", "Black Units", "Pawn", "Pawn_Idle Axe.png")
             portrayal["size"] = 55
        
        elif isinstance(agent, Mountain):
             portrayal["color"] = "gray"
             portrayal["marker"] = "^"
             portrayal["size"] = 80
             
        elif isinstance(agent, River):
             portrayal["color"] = "cyan"
             portrayal["marker"] = "s"
             portrayal["size"] = 50

        elif isinstance(agent, Road):
             portrayal["color"] = "brown"
             portrayal["marker"] = "s"
             portrayal["size"] = 50

        # Catch-all fallback for Nature
        if image_url is None and "marker" not in portrayal:
            portrayal["color"] = "green"
            portrayal["marker"] = "o"
            portrayal["size"] = 20

    # Assignment
    if image_url:
        portrayal["image"] = image_url
    
    return portrayal

# --- Simulation Parameters ---
model_params = {
    "width": 60,
    "height": 45,
    "num_tribes": 3,
    "initial_people": 10,
}

def debug_post_process(ax, model):
    # print(f"DEBUG: Post Process Model: {model}")
    pass

# --- Visualization Component ---
# backend="matplotlib" is required for custom image markers in some versions of SolaraViz/MesaViz
SpaceGraph = make_space_component(
    agent_portrayal, 
    post_process=None,
    backend="matplotlib" 
)

class VisualizationModel(CivilizationModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure space is set for visualization
        self.space = self.grid
        
# --- Page Layout ---
# Instantiate model manually to ensure SolaraViz has a valid instance
concrete_model = CivilizationModel(**model_params)

page = SolaraViz(
    concrete_model,
    components=[SpaceGraph],
    name="Civilization Simulation"
)
