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
    if isinstance(agent, Person):
        color = "grey"  # Default for loners or if tribes are off
        if agent.tribe_id is not None and agent.model.tribe_colors:
            color = agent.model.tribe_colors[agent.tribe_id % len(agent.model.tribe_colors)]
        
        marker = "o"
        if hasattr(agent, "profession"):
            if agent.profession == "Farmer":
                marker = "P" # Plus (filled)
            elif agent.profession == "Miner":
                marker = "d" # Thin diamond
            elif agent.profession == "Guard":
                marker = "^" # Triangle up
            elif agent.profession == "Blacksmith":
                marker = "p" # Pentagon
            elif agent.profession == "Merchant":
                marker = "v" # Triangle down
            elif agent.profession == "Soldier":
                marker = ">" # Triangle right
            elif agent.profession == "Scholar":
                marker = "*" # Star
            elif agent.profession == "Healer":
                marker = "+" # Plus
            elif agent.profession == "Priest":
                marker = "1" # Tri_down (using 1 as placeholder for now, or maybe just a different shape)

        return {
            "color": color,
            "marker": marker,
            "size": 50,
        }
    elif isinstance(agent, Barbarian):
        return {
            "color": "red",
            "marker": "x",
            "size": 60,
        }
    elif isinstance(agent, Predator):
        color = "#A52A2A"  # A default brown-red for loner predators
        if agent.pack_id is not None and agent.model.pack_colors:
            color = agent.model.pack_colors[agent.pack_id % len(agent.model.pack_colors)]
        return {
            "color": color,
            "marker": "o",
            "size": 60,
        }
    elif isinstance(agent, Food):
        return {
            "color": "green",
            "marker": "s",
            "size": 30
        }
    elif isinstance(agent, Tree):
        return {
            "color": "brown",
            "marker": "s",
            "size": 40
        }
    elif isinstance(agent, Stone):
        return {
            "color": "grey",
            "marker": "s",
            "size": 40
        }
    elif isinstance(agent, IronOre):
        return {
            "color": "#B7410E", # Rust
            "marker": "s",
            "size": 40
        }
    elif isinstance(agent, House):
        return {
            "color": "black",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Farm):
        return {
            "color": "yellow",
            "marker": "s",
            "size": 60
        }
    elif isinstance(agent, Smithy):
        return {
            "color": "#8B0000", # Dark Red
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Wall):
        return {
            "color": "grey",
            "marker": "s",
            "size": 80
        }
         
    elif isinstance(agent, Road):
        return {
            "color": "#D2B48C", # Tan
            "marker": "s",
            "size": 25
        }
    elif isinstance(agent, Market):
        return {
            "color": "purple",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Barracks):
        return {
            "color": "red",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Library):
        return {
            "color": "blue",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Hospital):
        return {
            "color": "pink",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Temple):
        return {
            "color": "gold",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Tavern):
        return {
            "color": "orange",
            "marker": "s",
            "size": 70
        }
    elif isinstance(agent, Mountain):
        return {
            "color": "grey",
            "marker": "^", # Triangle up
            "size": 90
        }
    elif isinstance(agent, River):
        return {
            "color": "blue",
            "marker": "s",
            "size": 80
        }
    
    # Default fallback to prevent NoneType error
    return {
        "color": "black",
        "marker": "o",
        "size": 10
    }

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 20,
        "label": "Ширина",
        "min": 10,
        "max": 50,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Висота",
        "min": 10,
        "max": 50,
        "step": 1,
    },
    "initial_people": {
        "type": "SliderInt",
        "value": 20,
        "label": "Кількість людей",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "num_tribes": {
        "type": "SliderInt",
        "value": 3,
        "label": "Кількість племен",
        "min": 0,
        "max": 10,
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
        make_plot_component("Люди"),
        make_plot_component("Їжа"),
        make_plot_component("Будинки"),
        make_plot_component("Ферми"),
        make_plot_component("Середня енергія"),
    ],
    model_params=model_params,
    name="Симуляція Цивілізації",
    play_interval=0  # Maximum speed (no delay)
)
