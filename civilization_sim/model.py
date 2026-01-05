from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import logging
from civilization_sim.agents import Person, Food, Predator, Tree, House, Stone, Farm, Wall, IronOre, Smithy, Road, Market, Barracks, Barbarian, Hospital, Temple, Tavern, Mountain, River

# Configure logging
logging.basicConfig(
    filename='simulation.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)

def compute_people_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Person))

def compute_food_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Food))

def compute_predator_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Predator))

def compute_tree_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Tree))

def compute_stone_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Stone))

def compute_iron_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, IronOre))

def compute_house_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, House))

def compute_farm_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Farm))

def compute_smithy_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Smithy))

def compute_road_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Road))

def compute_market_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Market))

def compute_barracks_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Barracks))

def compute_hospital_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Hospital))

def compute_temple_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Temple))

def compute_tavern_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, Tavern))

def compute_avg_energy(model):
    people = [agent.energy for agent in model.schedule.agents if isinstance(agent, Person)]
    return sum(people) / len(people) if people else 0

class CivilizationModel(Model):
    def __init__(self, width=20, height=20, initial_people=20, initial_food=50, initial_predators=2, initial_trees=30, initial_stone=10, initial_iron=5, num_tribes=3, num_predator_packs=1, seed=None):
        super().__init__(seed=seed)
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.running = True
        self.num_tribes = num_tribes
        self.num_predator_packs = num_predator_packs
        # Generate a list of random colors for the tribes
        self.tribe_colors = ["#" + ''.join(self.random.choices('0123456789ABCDEF', k=6)) for _ in range(num_tribes)] if num_tribes > 0 else []
        self.pack_colors = ["#" + ''.join(self.random.choices('0123456789ABCDEF', k=6)) for _ in range(num_predator_packs)] if num_predator_packs > 0 else []
        self.next_tribe_id = num_tribes
        self.tribe_stockpiles = {i: {"food": 0, "wood": 0, "stone": 0, "iron": 0, "tools": 0, "science": 0} for i in range(num_tribes)}
        self.tribe_counts = {} # Cache for performance
        self.wars = set() # Set of tuples (tribe_id_1, tribe_id_2)
        self.tribe_leaders = {} # Map tribe_id -> agent_id
        
        # Stage 5: Cataclysms and Challenges
        self.drought_active = False
        self.barbarian_wave_interval = 200 # Increased from 100 to give more breathing room
        self.barbarian_wave_timer = 0
        
        # Stage 6: Politics and Culture
        self.tribe_government = {}
        self.available_governments = ["Monarchy", "Republic", "Theocracy"]
        self.tribe_religion = {}
        self.available_deities = ["War God", "Harvest Goddess", "Sun God", "Sea God"]
        self.diplomacy = {i: {j: "Neutral" for j in range(num_tribes) if i != j} for i in range(num_tribes)}
        
        for i in range(num_tribes):
            self.tribe_government[i] = self.random.choice(self.available_governments)
            self.tribe_religion[i] = self.random.choice(self.available_deities)
            logging.info(f"Tribe {i}: Gov={self.tribe_government[i]}, Religion={self.tribe_religion[i]}")

        # Stage 7: Geography and Ecology
        self.season = "Spring"
        self.season_timer = 0
        self.season_length = 100 # Steps per season
        
        # Tribe Technologies
        self.tribe_technologies = {i: set() for i in range(num_tribes)}
        self.available_technologies = {
            "Agriculture": {"cost": 30, "req": None, "description": "Basic farming knowledge"},
            "Irrigation": {"cost": 50, "req": "Agriculture", "description": "Farms produce +2 food"},
            "Mining": {"cost": 30, "req": None, "description": "Better stone/ore extraction"},
            "Masonry": {"cost": 50, "req": "Mining", "description": "Walls are stronger"},
            "Bronze Working": {"cost": 60, "req": "Mining", "description": "Bronze Age: Better tools (+1)"},
            "Iron Working": {"cost": 100, "req": "Bronze Working", "description": "Iron Age: Superior tools (+2)"},
            "Writing": {"cost": 40, "req": None, "description": "Unlocks advanced culture"},
            "Philosophy": {"cost": 80, "req": "Writing", "description": "Morale boost (+2)"},
            "Medicine": {"cost": 50, "req": "Writing", "description": "Increased lifespan (+20 steps)"}
        }
        
        # Tribe Traits
        self.tribe_traits = {}
        self.available_traits = ["Agrarian", "Industrial", "Militaristic", "Expansionist"]
        for i in range(num_tribes):
            self.tribe_traits[i] = self.random.choice(self.available_traits)
            logging.info(f"Tribe {i} initialized with trait: {self.tribe_traits[i]}")
        
        # Generate Terrain
        self.generate_terrain()

        # Initialize DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "People": compute_people_count,
                "Food": compute_food_count,
                "Predators": compute_predator_count,
                "Trees": compute_tree_count,
                "Stone": compute_stone_count,
                "Iron": compute_iron_count,
                "Houses": compute_house_count,
                "Farms": compute_farm_count,
                "Smithies": compute_smithy_count,
                "Roads": compute_road_count,
                "Markets": compute_market_count,
                "Barracks": compute_barracks_count,
                "Hospitals": compute_hospital_count,
                "Temples": compute_temple_count,
                "Taverns": compute_tavern_count,
                "Avg Energy": compute_avg_energy
            }
        )

        logging.info("Simulation started")
        
        # Create people
        for i in range(initial_people):
            tribe_id = i % self.num_tribes if self.num_tribes > 0 else None
            a = Person(self, tribe_id=tribe_id)
            self.schedule.add(a)
            
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            logging.info(f"Created Person {a.unique_id} of tribe {tribe_id} at ({x}, {y})")

        # Create predators
        for i in range(initial_predators):
            pack_id = i % self.num_predator_packs if self.num_predator_packs > 0 else None
            p = Predator(self, pack_id=pack_id)
            self.schedule.add(p)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(p, (x, y))
            logging.info(f"Created Predator {p.unique_id} of pack {pack_id} at ({x}, {y})")

        # Create food
        for i in range(initial_food):
            f = Food(self)
            self.schedule.add(f)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(f, (x, y))

        # Create trees
        for i in range(initial_trees):
            t = Tree(self)
            self.schedule.add(t)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(t, (x, y))

        # Create stone
        for i in range(initial_stone):
            s = Stone(self)
            self.schedule.add(s)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(s, (x, y))

        # Create iron
        for i in range(initial_iron):
            ir = IronOre(self)
            self.schedule.add(ir)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(ir, (x, y))

        self.datacollector.collect(self)

    def generate_terrain(self):
        # Generate River
        # Simple river: Start at top, meander to bottom
        start_x = self.random.randrange(self.grid.width)
        start_y = 0
        current_x, current_y = start_x, start_y
        
        while 0 <= current_y < self.grid.height:
            # Place river
            if 0 <= current_x < self.grid.width:
                # Check if empty or just overwrite? Better to check empty to avoid deleting people if called later
                # But called in init, so mostly empty except resources
                cell_contents = self.grid.get_cell_list_contents([(current_x, current_y)])
                if not any(isinstance(a, (Person, House)) for a in cell_contents):
                    r = River(self)
                    self.schedule.add(r)
                    self.grid.place_agent(r, (current_x, current_y))
            
            # Move
            # Bias towards down (0, 1)
            moves = [(0, 1), (0, 1), (1, 0), (-1, 0)]
            move = self.random.choice(moves)
            current_x += move[0]
            current_y += move[1]

        # Generate Mountains
        # Clusters of mountains
        num_clusters = 5
        for _ in range(num_clusters):
            center_x = self.random.randrange(self.grid.width)
            center_y = self.random.randrange(self.grid.height)
            
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if self.random.random() < 0.6: # 60% chance to be mountain in cluster
                        mx, my = center_x + dx, center_y + dy
                        if 0 <= mx < self.grid.width and 0 <= my < self.grid.height:
                            cell_contents = self.grid.get_cell_list_contents([(mx, my)])
                            if not any(isinstance(a, (Person, House, River)) for a in cell_contents):
                                m = Mountain(self)
                                self.schedule.add(m)
                                self.grid.place_agent(m, (mx, my))

    def form_new_tribe(self, agent1, agent2):
        new_tribe_id = self.next_tribe_id
        agent1.tribe_id = new_tribe_id
        agent2.tribe_id = new_tribe_id
        self.tribe_stockpiles[new_tribe_id] = {"food": 0, "wood": 0, "stone": 0, "iron": 0, "tools": 0, "science": 0}
        self.tribe_technologies[new_tribe_id] = set()
        
        # Generate a new color for the new tribe
        new_color = "#" + ''.join(self.random.choices('0123456789ABCDEF', k=6))
        self.tribe_colors.append(new_color)
        
        # Assign random trait
        trait = self.random.choice(self.available_traits)
        self.tribe_traits[new_tribe_id] = trait
        
        # Initialize Government and Religion for new tribe
        self.tribe_government[new_tribe_id] = self.random.choice(["Monarchy", "Republic", "Theocracy"])
        self.tribe_religion[new_tribe_id] = self.random.choice(["Sun God", "War God", "Harvest God", "Sea God"])
        
        # Initialize Diplomacy for new tribe
        self.diplomacy[new_tribe_id] = {}
        # Initialize relations with existing tribes
        # Note: self.next_tribe_id is not incremented yet, so it points to the new tribe ID
        # We want to iterate over all PREVIOUS tribe IDs.
        for other_id in range(self.next_tribe_id):
             self.diplomacy[new_tribe_id][other_id] = "Neutral"
             if other_id in self.diplomacy:
                 self.diplomacy[other_id][new_tribe_id] = "Neutral"

        self.next_tribe_id += 1
        logging.info(f"Agents {agent1.unique_id} and {agent2.unique_id} formed a new tribe: {new_tribe_id} with trait {trait}")

    def check_tribe_splitting(self):
        # Check if any tribe is too large and should split
        # Increased threshold to prevent constant splitting
        split_threshold = 60
        
        # We need to iterate over a copy of keys because we might add new tribes
        current_tribes = list(self.tribe_counts.keys())
        
        for tribe_id in current_tribes:
            count = self.tribe_counts[tribe_id]
            stockpile = self.tribe_stockpiles.get(tribe_id, {"food": 0})
            food = stockpile["food"]
            
            should_split = False
            
            # Condition 1: Massive population (Administrative collapse)
            if count > 120:
                if self.random.random() < 0.02: # 2% chance if massive
                    should_split = True
            
            # Condition 2: Large population AND Low Food (Resource scarcity)
            elif count > split_threshold:
                # If food per capita is low (< 5), high chance of unrest
                if food < count * 5:
                    if self.random.random() < 0.01: # 1% chance
                        should_split = True
                else:
                    # Very low chance if well fed
                    if self.random.random() < 0.0005: # 0.05% chance
                        should_split = True
            
            if should_split:
                self.split_tribe(tribe_id)

    def split_tribe(self, parent_tribe_id):
        # Find all members
        members = [a for a in self.schedule.agents if isinstance(a, Person) and a.tribe_id == parent_tribe_id]
        if not members:
            return

        # Pick a rebel leader (random member)
        rebel_leader = self.random.choice(members)
        
        # Find members close to the rebel leader to join the split
        # Let's take 1/3 of the population
        split_size = len(members) // 3
        if split_size < 2:
            return

        # Sort members by distance to rebel leader
        members.sort(key=lambda a: abs(a.pos[0] - rebel_leader.pos[0]) + abs(a.pos[1] - rebel_leader.pos[1]))
        
        # The closest ones join the new tribe
        rebels = members[:split_size]
        
        # Create new tribe
        new_tribe_id = self.next_tribe_id
        self.next_tribe_id += 1
        
        self.tribe_stockpiles[new_tribe_id] = {"food": 50, "wood": 10, "stone": 0, "iron": 0, "tools": 0, "science": 0} # Start with some resources
        self.tribe_technologies[new_tribe_id] = set()
        
        new_color = "#" + ''.join(self.random.choices('0123456789ABCDEF', k=6))
        self.tribe_colors.append(new_color)
        
        trait = self.random.choice(self.available_traits)
        self.tribe_traits[new_tribe_id] = trait
        
        # Initialize Government and Religion for new tribe (Split)
        self.tribe_government[new_tribe_id] = self.random.choice(["Monarchy", "Republic", "Theocracy"])
        self.tribe_religion[new_tribe_id] = self.random.choice(["Sun God", "War God", "Harvest God", "Sea God"])
        
        # Initialize Diplomacy for new tribe
        self.diplomacy[new_tribe_id] = {}
        # Initialize relations with existing tribes
        # Iterate over all tribes up to new_tribe_id (exclusive)
        for other_id in range(new_tribe_id):
             self.diplomacy[new_tribe_id][other_id] = "Neutral"
             if other_id in self.diplomacy:
                 self.diplomacy[other_id][new_tribe_id] = "Neutral"
        
        # Reassign agents
        for rebel in rebels:
            rebel.tribe_id = new_tribe_id
            
        logging.info(f"Tribe {parent_tribe_id} SPLIT! New Tribe {new_tribe_id} formed with {len(rebels)} members. Trait: {trait}")


    def update_politics(self):
        # 1. Leader Selection
        # Group agents by tribe
        agents_by_tribe = {}
        for agent in self.schedule.agents:
            if isinstance(agent, Person) and agent.tribe_id is not None:
                agents_by_tribe.setdefault(agent.tribe_id, []).append(agent)
        
        for tribe_id, members in agents_by_tribe.items():
            # Check if leader exists and is alive
            current_leader_id = self.tribe_leaders.get(tribe_id)
            leader_alive = False
            if current_leader_id:
                leader = next((a for a in members if a.unique_id == current_leader_id), None)
                if leader:
                    leader_alive = True
            
            if not leader_alive and members:
                # Elect new leader based on Government Type
                gov = self.tribe_government.get(tribe_id, "Monarchy")
                if gov == "Monarchy":
                    # Oldest person (Elder)
                    new_leader = max(members, key=lambda a: a.age)
                elif gov == "Republic":
                    # Random election (simulated)
                    new_leader = self.random.choice(members)
                elif gov == "Theocracy":
                    # Priest or oldest
                    priests = [m for m in members if m.profession == "Priest"]
                    if priests:
                        new_leader = self.random.choice(priests)
                    else:
                        new_leader = max(members, key=lambda a: a.age)
                
                self.tribe_leaders[tribe_id] = new_leader.unique_id
                logging.info(f"Tribe {tribe_id} ({gov}) elected new leader: {new_leader.unique_id}")

        # 2. Diplomacy (War, Peace, Alliance)
        tribe_ids = list(self.tribe_stockpiles.keys())
        for i in range(len(tribe_ids)):
            for j in range(i + 1, len(tribe_ids)):
                id1 = tribe_ids[i]
                id2 = tribe_ids[j]
                
                stock1 = self.tribe_stockpiles[id1]
                stock2 = self.tribe_stockpiles[id2]
                
                war_key = tuple(sorted((id1, id2)))
                is_at_war = war_key in self.wars
                relation = self.diplomacy[id1].get(id2, "Neutral")
                
                # Factors
                gov1, gov2 = self.tribe_government[id1], self.tribe_government[id2]
                rel1, rel2 = self.tribe_religion[id1], self.tribe_religion[id2]
                
                # --- ALLIANCE LOGIC ---
                if relation != "Alliance" and not is_at_war:
                    # Chance to ally if:
                    # 1. Same Religion (Theocracy bonus)
                    # 2. Both Republics (Trade bonus)
                    # 3. Both Rich (> 300 food)
                    
                    alliance_score = 0
                    if rel1 == rel2: alliance_score += 2
                    if gov1 == "Republic" and gov2 == "Republic": alliance_score += 2
                    if stock1["food"] > 300 and stock2["food"] > 300: alliance_score += 1
                    
                    if alliance_score >= 3:
                        if self.random.random() < 0.05:
                            self.diplomacy[id1][id2] = "Alliance"
                            self.diplomacy[id2][id1] = "Alliance"
                            logging.info(f"ALLIANCE FORMED: Tribe {id1} and Tribe {id2} are now Allies!")

                # --- WAR LOGIC ---
                if not is_at_war and relation != "Alliance":
                    war_chance = 0.0
                    
                    # Resource Scarcity (Primary Driver)
                    if stock1["food"] < 50 and stock2["food"] > 200: war_chance += 0.05
                    if stock2["food"] < 50 and stock1["food"] > 200: war_chance += 0.05
                    
                    # Religious Conflict
                    if rel1 != rel2:
                        if gov1 == "Theocracy" or gov2 == "Theocracy":
                            war_chance += 0.02
                            
                    # Militaristic Government
                    if gov1 == "Monarchy": war_chance += 0.01
                    if gov2 == "Monarchy": war_chance += 0.01
                    
                    if self.random.random() < war_chance:
                        self.wars.add(war_key)
                        self.diplomacy[id1][id2] = "War"
                        self.diplomacy[id2][id1] = "War"
                        logging.info(f"WAR DECLARED: Tribe {id1} vs Tribe {id2} (Reason: Scarcity/Religion/Gov)")

                # --- PEACE LOGIC ---
                elif is_at_war:
                    # Peace if both exhausted or rich enough
                    if (stock1["food"] > 100 and stock2["food"] > 100) or (stock1["food"] < 10 and stock2["food"] < 10):
                        if self.random.random() < 0.1:
                            self.wars.remove(war_key)
                            self.diplomacy[id1][id2] = "Neutral"
                            self.diplomacy[id2][id1] = "Neutral"
                            logging.info(f"PEACE DECLARED: Tribe {id1} and Tribe {id2} are at peace.")

    def check_research(self):
        for tribe_id, stockpile in self.tribe_stockpiles.items():
            science = stockpile.get("science", 0)
            techs = self.tribe_technologies.get(tribe_id, set())
            
            # Find researchable techs
            possible_techs = []
            for tech_name, data in self.available_technologies.items():
                if tech_name not in techs:
                    # Check requirements
                    req = data.get("req")
                    if req is None or req in techs:
                        if science >= data["cost"]:
                            possible_techs.append(tech_name)
            
            # Research one
            if possible_techs:
                tech_to_research = self.random.choice(possible_techs)
                cost = self.available_technologies[tech_to_research]["cost"]
                stockpile["science"] -= cost
                techs.add(tech_to_research)
                logging.info(f"Tribe {tribe_id} researched {tech_to_research}!")

    def step(self):
        # Update Season
        self.season_timer += 1
        if self.season_timer >= self.season_length:
            self.season_timer = 0
            seasons = ["Spring", "Summer", "Autumn", "Winter"]
            current_idx = seasons.index(self.season)
            self.season = seasons[(current_idx + 1) % 4]
            logging.info(f"SEASON CHANGE: It is now {self.season}")

        self.update_politics()
        self.check_research()
        # Pre-calculate tribe counts for performance
        self.tribe_counts = {}
        for agent in self.schedule.agents:
            if isinstance(agent, Person) and agent.tribe_id is not None:
                self.tribe_counts[agent.tribe_id] = self.tribe_counts.get(agent.tribe_id, 0) + 1
        
        # Check for tribe splitting
        self.check_tribe_splitting()

        self.schedule.step()
        
        # Randomly grow new food
        # Grow multiple food items per step to sustain population
        for _ in range(10):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            f = Food(self)
            self.schedule.add(f)
            self.grid.place_agent(f, (x, y))
            logging.info(f"New Food grew at ({x}, {y})")

        # Randomly grow new trees
        for _ in range(5):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            t = Tree(self)
            self.schedule.add(t)
            self.grid.place_agent(t, (x, y))
            logging.info(f"New Tree grew at ({x}, {y})")

        # Randomly spawn new stone (geological process, rare)
        for _ in range(5):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            s = Stone(self)
            self.schedule.add(s)
            self.grid.place_agent(s, (x, y))
            logging.info(f"New Stone appeared at ({x}, {y})")

        # Randomly spawn new iron (very rare)
        if self.random.random() < 0.3: # 30% chance per step
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            ir = IronOre(self)
            self.schedule.add(ir)
            self.grid.place_agent(ir, (x, y))
            logging.info(f"New Iron Ore appeared at ({x}, {y})")

        # Respawn predator if extinct (Migration simulation)
        if compute_predator_count(self) == 0:
            if self.random.random() < 0.1: # 10% chance per step to migrate in
                pack_id = self.random.randrange(self.num_predator_packs) if self.num_predator_packs > 0 else None
                p = Predator(self, pack_id=pack_id)
                self.schedule.add(p)
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(p, (x, y))
                logging.info(f"A new Predator of pack {pack_id} migrated to ({x}, {y})")

        # Respawn humans if near extinct (Migration simulation)
        if compute_people_count(self) <= 2:
            if self.random.random() < 0.2: # 20% chance per step to migrate in
                # Spawn a small group
                for _ in range(2):
                    tribe_id = self.random.randrange(self.num_tribes) if self.num_tribes > 0 else None
                    p = Person(self, tribe_id=tribe_id)
                    self.schedule.add(p)
                    x = self.random.randrange(self.grid.width)
                    y = self.random.randrange(self.grid.height)
                    self.grid.place_agent(p, (x, y))
                    logging.info(f"A new Person of tribe {tribe_id} migrated to ({x}, {y})")

        # --- Stage 5: Cataclysms and Challenges Logic ---
        
        # 1. Drought Logic
        if self.drought_active:
            # Chance to end drought (e.g., 5% per step)
            if self.random.random() < 0.05:
                self.drought_active = False
                logging.info("The DROUGHT has ended! Rain returns to the land.")
        else:
            # Chance to start drought (e.g., 0.5% per step) - Reduced from 1%
            if self.random.random() < 0.005:
                self.drought_active = True
                logging.info("A DROUGHT has begun! Crops will wither and farms will stop producing.")

        # 2. Plague Logic (New)
        # Small chance to start a plague if population is high (> 50)
        if compute_people_count(self) > 50 and self.random.random() < 0.005:
            # Infect a random person
            people = [a for a in self.schedule.agents if isinstance(a, Person)]
            if people:
                patient_zero = self.random.choice(people)
                patient_zero.infected = True
                logging.info(f"PLAGUE OUTBREAK! Patient Zero is Person {patient_zero.unique_id} at {patient_zero.pos}")

        # 3. Barbarian Invasion Logic
        self.barbarian_wave_timer += 1
        if self.barbarian_wave_timer >= self.barbarian_wave_interval:
            self.barbarian_wave_timer = 0
            # Spawn a wave of barbarians
            num_barbarians = self.random.randint(2, 5) # Reduced from 3-8
            logging.info(f"BARBARIAN INVASION! {num_barbarians} barbarians have arrived to pillage!")
            for _ in range(num_barbarians):
                b = Barbarian(self)
                self.schedule.add(b)
                # Spawn at random edge of map
                if self.random.random() < 0.5:
                    x = self.random.choice([0, self.grid.width - 1])
                    y = self.random.randrange(self.grid.height)
                else:
                    x = self.random.randrange(self.grid.width)
                    y = self.random.choice([0, self.grid.height - 1])
                
                self.grid.place_agent(b, (x, y))
            
        self.datacollector.collect(self)
        logging.info(f"Step {self.schedule.steps} completed. People: {compute_people_count(self)}, Predators: {compute_predator_count(self)}, Food: {compute_food_count(self)}")

