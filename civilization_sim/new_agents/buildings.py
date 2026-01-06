from mesa import Agent
import logging
from .resources import Food, River

class Building(Agent):
    """Base class for all buildings."""
    def __init__(self, model, tribe_id=None):
        super().__init__(model)
        self.tribe_id = tribe_id

class House(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Wall(Building):
    def __init__(self, model):
        # Walls might not have an owner initially, or are neutral, but let's keep __init__ signature compatible if needed
        super().__init__(model)

class Road(Building):
    def __init__(self, model):
        super().__init__(model)

class Smithy(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Market(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Barracks(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Library(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Hospital(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Temple(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Tavern(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)

class Farm(Building):
    def __init__(self, model, tribe_id=None):
        super().__init__(model, tribe_id)
        self.growth_progress = 0
        self.growth_rate = 1  # Progress per step
        self.harvest_threshold = 10 # Steps to grow food

    def step(self):
        if self.pos is None:
            return

        # Check for Drought
        if hasattr(self.model, "drought_active") and self.model.drought_active:
            return # No growth during drought
            
        # Check for Winter
        if hasattr(self.model, "season") and self.model.season == "Winter":
            return # No growth during winter

        growth_bonus = 0
        # Check for nearby River (Irrigation bonus)
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=1)
        if any(isinstance(a, River) for a in neighbors):
            growth_bonus += 1

        self.growth_progress += (self.growth_rate + growth_bonus)
        if self.growth_progress >= self.harvest_threshold:
            # Grow food on this cell
            food = Food(self.model)
            self.model.schedule.add(food)
            self.model.grid.place_agent(food, self.pos)
            self.growth_progress = 0
            source = "River Farm" if growth_bonus > 0 else "Farm"
            logging.info(f"{source} {self.unique_id} (Tribe {self.tribe_id}) produced food at {self.pos}")
