from mesa import Agent
import logging
from ..pathfinding import a_star_search
from .resources import Food, Tree, Stone, IronOre, Mountain
from .buildings import House, Farm, Wall, Smithy, Market, Road, Barracks, Library, Hospital, Temple, Tavern

class Person(Agent):
    def __init__(self, model, tribe_id=None):
        super().__init__(model)
        self.energy = 30
        self.age = 0
        self.tribe_id = tribe_id
        self.profession = self.random.choice(["Farmer", "Miner", "Guard", "Blacksmith", "Merchant", "Soldier", "Archer", "Scholar", "Healer", "Priest"])
        self.infected = False # For Plague
        
        # Memory System
        self.memory = {} # Mapping: ResourceType -> List of (x, y) coordinates
        self.scanner_cooldown = 0
        self.current_path = [] # List of (x, y) tuples for current movement path

    def scan_environment(self):
        if self.scanner_cooldown > 0:
            self.scanner_cooldown -= 1
            return

        # Scan a larger area occasionally
        scan_radius = 5
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=scan_radius)
        
        for agent in neighbors:
            # We are interested in resources and buildings
            if isinstance(agent, (Food, Tree, Stone, IronOre, House, Farm, Smithy, Market, Library, Hospital, Temple, Tavern)):
                agent_type = type(agent)
                if agent_type not in self.memory:
                    self.memory[agent_type] = set()
                self.memory[agent_type].add(agent.pos)
        
        self.scanner_cooldown = 10 # Scan every 10 steps

    def get_possible_actions(self, cell_mates):
        actions = []
        
        # Gather Actions
        # Enable gathering for everyone (Loners need food too)
        for agent in cell_mates:
            if isinstance(agent, Tree) and self.tribe_id is not None:
                actions.append({"type": "gather_wood", "target": agent})
            elif isinstance(agent, Stone) and self.tribe_id is not None:
                actions.append({"type": "gather_stone", "target": agent})
            elif isinstance(agent, IronOre) and self.tribe_id is not None:
                actions.append({"type": "gather_iron", "target": agent})
            elif isinstance(agent, Food):
                # Food is universal
                actions.append({"type": "gather_food", "target": agent})
        
        # Work Actions
        if self.tribe_id is not None:
            if self.profession == "Blacksmith" and any(isinstance(a, Smithy) for a in cell_mates):
                 actions.append({"type": "work_smithy"})
            if self.profession == "Scholar" and any(isinstance(a, Library) for a in cell_mates):
                 actions.append({"type": "work_library"})
            if self.profession == "Priest" and any(isinstance(a, Temple) for a in cell_mates):
                 actions.append({"type": "work_temple"})
            if self.profession == "Healer" and any(isinstance(a, Hospital) for a in cell_mates):
                 actions.append({"type": "work_hospital"})

        # Combat Actions
        attack_radius = 3 if self.profession == "Archer" else 1
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=attack_radius)
        for neighbor in neighbors:
            if isinstance(neighbor, Barbarian):
                actions.append({"type": "attack_barbarian", "target": neighbor})
            elif isinstance(neighbor, Predator):
                actions.append({"type": "attack_predator", "target": neighbor})
            elif isinstance(neighbor, Person) and neighbor.tribe_id != self.tribe_id and neighbor.tribe_id is not None:
                 actions.append({"type": "attack_enemy", "target": neighbor})

        # Build Actions
        if self.tribe_id is not None:
             stockpile = self.model.tribe_stockpiles[self.tribe_id]
             if stockpile["wood"] >= 3 or stockpile["stone"] >= 3:
                 actions.append({"type": "build_structure"})

        # Social
        if any(isinstance(a, Tavern) for a in cell_mates):
            actions.append({"type": "visit_tavern"})
            
        # Trade
        if any(isinstance(a, Person) for a in cell_mates if isinstance(a, Person) and a.tribe_id != self.tribe_id):
             actions.append({"type": "trade"})

        # Form Tribe
        if self.tribe_id is None:
             loners = [a for a in cell_mates if isinstance(a, Person) and a.tribe_id is None and a != self]
             if loners:
                 actions.append({"type": "form_tribe"})

        return actions

    def calculate_utility(self, action):
        score = 0
        action_type = action["type"]
        
        # Base Scores
        if action_type.startswith("gather"): score = 10
        elif action_type.startswith("work"): score = 10
        elif action_type.startswith("build"): score = 5
        elif action_type.startswith("attack"): score = 50
        elif action_type == "visit_tavern": score = 5
        elif action_type == "trade": score = 5

        # Context Modifiers
        if self.tribe_id is not None:
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            
            if action_type == "gather_food":
                if self.profession == "Farmer": score += 20
                if stockpile["food"] < 20: score += 60 # Critical
                elif stockpile["food"] < 50: score += 30 # Need
                if self.energy < 20: score += 40 # Personal survival

            elif action_type == "gather_wood":
                if stockpile["wood"] < 5: score += 60 # Critical
                elif stockpile["wood"] < 30: score += 40
            
            elif action_type == "gather_stone":
                if self.profession == "Miner": score += 20
                if stockpile["stone"] < 5: score += 60 # Critical
                elif stockpile["stone"] < 20: score += 40

            elif action_type == "gather_iron":
                if self.profession == "Miner": score += 20
                if stockpile["iron"] < 5: score += 40

            elif action_type == "work_smithy":
                if self.profession == "Blacksmith": score += 60
                if stockpile["iron"] > 0: score += 20

            elif action_type == "work_library":
                if self.profession == "Scholar": score += 60

            elif action_type == "work_temple":
                if self.profession == "Priest": score += 60
                if stockpile.get("morale", 0) < 50: score += 30

            elif action_type == "work_hospital":
                if self.profession == "Healer": score += 60
                if self.infected: score += 100

            elif action_type == "build_structure":
                # If we have lots of resources, build!
                if stockpile["wood"] > 15 and stockpile["stone"] > 15: score += 30
                
                # Boost if we have no science (need Library)
                if stockpile.get("science", 0) == 0 and stockpile["wood"] >= 15 and stockpile["stone"] >= 15:
                    score += 20
                
                # High priority if food is critical (Need Farm)
                if stockpile["food"] < 20 and stockpile["wood"] >= 2 and stockpile["stone"] >= 2:
                    score += 50

            elif action_type == "attack_enemy":
                target = action["target"]
                war_key = tuple(sorted((self.tribe_id, target.tribe_id)))
                if hasattr(self.model, "wars") and war_key in self.model.wars:
                    score += 100
                if self.profession == "Soldier": score += 50
                if hasattr(self.model, "tribe_religion") and self.model.tribe_religion.get(self.tribe_id) == "War God":
                    score += 20

            elif action_type == "visit_tavern":
                if self.energy < 25: score += 50

            elif action_type == "trade":
                if self.profession == "Merchant": score += 200

            elif action_type == "form_tribe":
                score += 50

        return score

    def step(self):
        if self.pos is None:
            return
        
        self.scan_environment()
        
        self.age += 1
        self.energy -= 1  # Living costs energy
        
        # Plague Effect
        if self.infected:
            self.energy -= 2 # Extra damage from plague
            
            # Spread Plague to neighbors
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=1)
            for neighbor in neighbors:
                if isinstance(neighbor, Person) and not neighbor.infected:
                    # 10% chance to infect neighbor
                    if self.random.random() < 0.1:
                        neighbor.infected = True
                        logging.info(f"Людина {self.unique_id} заразила Людину {neighbor.unique_id} чумою")

            # Chance to recover if at Hospital or with Medicine
            recovery_chance = 0.05
            if self.tribe_id is not None and hasattr(self.model, "tribe_technologies"):
                if "Medicine" in self.model.tribe_technologies.get(self.tribe_id, set()):
                    recovery_chance += 0.1
            
            # Hospital bonus
            cell_mates = self.model.grid.get_cell_list_contents([self.pos])
            if any(isinstance(a, Hospital) for a in cell_mates):
                recovery_chance += 0.2
                
            if self.random.random() < recovery_chance:
                self.infected = False
                logging.info(f"Людина {self.unique_id} одужала від чуми!")

        # Try to eat from stockpile if in a tribe and hungry
        self.withdraw_food()

        # Check for death condition FIRST, after energy consumption
        if self.energy <= 0:
            reason = "чуми" if self.infected else "голоду"
            logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} померла від {reason} в {self.pos}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        
        # Medicine Tech: Increased lifespan
        max_age = 100
        if self.tribe_id is not None and hasattr(self.model, "tribe_technologies"):
            if "Medicine" in self.model.tribe_technologies.get(self.tribe_id, set()):
                max_age = 120

        if self.age >= max_age:
            logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} померла від старості в {self.pos}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # --- ACTIONS (Utility AI) ---
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        possible_actions = self.get_possible_actions(cell_mates)
        
        best_action = None
        best_score = -1
        
        for action in possible_actions:
            score = self.calculate_utility(action)
            if score > best_score:
                best_score = score
                best_action = action
        
        # Execute Best Action
        if best_action:
            action_type = best_action["type"]
            if action_type == "gather_wood": self.gather_wood()
            elif action_type == "gather_stone": self.gather_stone()
            elif action_type == "gather_iron": self.gather_iron()
            elif action_type == "gather_food": self.gather_food()
            elif action_type == "work_smithy": self.work_smithy()
            elif action_type == "work_library": self.work_library()
            elif action_type == "work_temple": self.work_temple()
            elif action_type == "work_hospital": self.work_hospital()
            elif action_type == "visit_tavern": self.visit_tavern()
            elif action_type == "build_structure": self.build_house()
            elif action_type == "trade": self.trade()
            elif action_type == "form_tribe": self.form_tribe()
            elif action_type == "attack_barbarian": self.attack_barbarian()
            elif action_type == "attack_predator": self.attack_predator()
            elif action_type == "attack_enemy": self.attack_enemy()

        # Reproduce if conditions are met
        repro_threshold = 40
        if self.tribe_id is not None:
            # Trait bonus
            if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Expansionist":
                repro_threshold = 35
            
            # Morale bonus (Temple)
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            if stockpile.get("morale", 0) > 50:
                repro_threshold -= 5 # Happy people reproduce faster

        if self.energy >= repro_threshold:
            self.reproduce()
            
        # --- MOVE at the end of the step ---
        self.move()

    def gather_wood(self):
        if self.tribe_id is None:
            return  # Loners don't use stockpiles

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_mates:
            if isinstance(agent, Tree):
                amount = 1
                # Leader bonus
                if hasattr(self.model, "tribe_leaders") and self.tribe_id in self.model.tribe_leaders:
                    amount += 1
                
                # Government bonus: Republic
                if hasattr(self.model, "tribe_government") and self.model.tribe_government.get(self.tribe_id) == "Republic":
                    amount += 1
                
                # Trait bonus
                if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Industrial":
                    amount += 1
                
                self.model.tribe_stockpiles[self.tribe_id]["wood"] += amount
                logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} зібрала дерево. Запаси дерева: {self.model.tribe_stockpiles[self.tribe_id]['wood']}")
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
                break

    def gather_stone(self):
        if self.tribe_id is None:
            return  # Loners don't use stockpiles

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_mates:
            if isinstance(agent, Stone):
                amount = 1
                if self.profession == "Miner":
                    amount += 1
                # Leader bonus
                if hasattr(self.model, "tribe_leaders") and self.tribe_id in self.model.tribe_leaders:
                    amount += 1
                    
                # Government bonus: Republic
                if hasattr(self.model, "tribe_government") and self.model.tribe_government.get(self.tribe_id) == "Republic":
                    amount += 1

                # Trait bonus
                if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Industrial":
                    amount += 1

                # Tech bonus: Mining
                if hasattr(self.model, "tribe_technologies"):
                    if "Mining" in self.model.tribe_technologies.get(self.tribe_id, set()):
                        amount += 1

                self.model.tribe_stockpiles[self.tribe_id]["stone"] += amount
                logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} зібрала камінь. Запаси каменю: {self.model.tribe_stockpiles[self.tribe_id]['stone']}")
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
                break

    def gather_iron(self):
        if self.tribe_id is None:
            return

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_mates:
            if isinstance(agent, IronOre):
                amount = 1
                if self.profession == "Miner":
                    amount += 1
                # Trait bonus
                if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Industrial":
                    amount += 1

                # Leader bonus
                if hasattr(self.model, "tribe_leaders") and self.tribe_id in self.model.tribe_leaders:
                    amount += 1
                
                # Government bonus: Republic
                if hasattr(self.model, "tribe_government") and self.model.tribe_government.get(self.tribe_id) == "Republic":
                    amount += 1
                
                # Tech bonus: Mining
                if hasattr(self.model, "tribe_technologies"):
                    if "Mining" in self.model.tribe_technologies.get(self.tribe_id, set()):
                        amount += 1
                    
                self.model.tribe_stockpiles[self.tribe_id]["iron"] += amount
                logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} зібрала залізо. Запаси заліза: {self.model.tribe_stockpiles[self.tribe_id]['iron']}")
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
                break

    def work_smithy(self):
        if self.tribe_id is None:
            return
        
        if self.profession != "Blacksmith":
            return

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, Smithy) for agent in cell_mates):
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            if stockpile["iron"] >= 1:
                stockpile["iron"] -= 1
                amount = 1
                # Tech bonus: Bronze Working / Iron Working
                if hasattr(self.model, "tribe_technologies"):
                    techs = self.model.tribe_technologies.get(self.tribe_id, set())
                    if "Bronze Working" in techs: amount += 1
                    if "Iron Working" in techs: amount += 2
                
                stockpile["tools"] += amount
                logging.info(f"Коваль {self.unique_id} виготовив інструменти. Запаси інструментів: {stockpile['tools']}")

    def work_library(self):
        if self.tribe_id is None:
            return
        
        if self.profession != "Scholar":
            return

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, Library) for agent in cell_mates):
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            # Scholars generate science
            amount = 1
            # Leader bonus
            if hasattr(self.model, "tribe_leaders") and self.tribe_id in self.model.tribe_leaders:
                amount += 1
            
            stockpile["science"] += amount
            logging.info(f"Учений {self.unique_id} згенерував науку. Очки науки: {stockpile['science']}")

    def work_hospital(self):
        if self.tribe_id is None or self.profession != "Healer":
            return
        
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, Hospital) for agent in cell_mates):
            # Heal everyone on the same tile
            for agent in cell_mates:
                if isinstance(agent, Person) and agent.tribe_id == self.tribe_id:
                    if agent.infected:
                        if self.random.random() < 0.5:
                            agent.infected = False
                            logging.info(f"Цілитель {self.unique_id} вилікував Людину {agent.unique_id} від чуми")
                    if agent.energy < 30:
                        agent.energy += 5
                        logging.info(f"Цілитель {self.unique_id} вилікував Людину {agent.unique_id}")

    def work_temple(self):
        if self.tribe_id is None or self.profession != "Priest":
            return
            
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, Temple) for agent in cell_mates):
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            # Generate Morale
            morale_boost = 1
            
            # Government Bonuses
            if hasattr(self.model, "tribe_government"):
                gov = self.model.tribe_government.get(self.tribe_id)
                if gov == "Monarchy": morale_boost += 2
                if gov == "Theocracy": morale_boost += 3
            
            # Religion Bonuses
            if hasattr(self.model, "tribe_religion"):
                rel = self.model.tribe_religion.get(self.tribe_id)
                if rel == "War God": morale_boost += 2
                if rel == "Sun God": 
                    stockpile["science"] = stockpile.get("science", 0) + 1 # Sun God gives science
                    logging.info(f"Священик {self.unique_id} згенерував науку (Бог Сонця). Очки науки: {stockpile['science']}")
            
            # Tech bonus: Philosophy
            if hasattr(self.model, "tribe_technologies"):
                if "Philosophy" in self.model.tribe_technologies.get(self.tribe_id, set()):
                    morale_boost += 2

            stockpile["morale"] = stockpile.get("morale", 0) + morale_boost
            if stockpile["morale"] > 100: stockpile["morale"] = 100
            logging.info(f"Священик {self.unique_id} підняв мораль. Мораль племені: {stockpile['morale']}")

    def visit_tavern(self):
        if self.tribe_id is None: return
        
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, Tavern) for agent in cell_mates):
            # If hungry, eat with bonus
            if self.energy < 25:
                stockpile = self.model.tribe_stockpiles[self.tribe_id]
                if stockpile["food"] >= 1:
                    stockpile["food"] -= 1
                    self.energy += 20 # Big boost (normally 15)
                    logging.info(f"Людина {self.unique_id} поїла в Таверні. Енергія: {self.energy}")

    def attack_barbarian(self):
        if self.profession not in ["Guard", "Soldier"]:
            return
            
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1)
        barbarians = [a for a in neighbors if isinstance(a, Barbarian)]
        
        if barbarians:
            target = barbarians[0]
            damage = 10
            if self.profession == "Soldier": damage = 20
            
            self.energy -= 5
            target.energy -= damage
            logging.info(f"Захисник {self.unique_id} атакував Варвара в {target.pos}")
            if target.energy <= 0:
                self.model.grid.remove_agent(target)
                self.model.schedule.remove(target)

    def attack_predator(self):
        if self.profession != "Guard":
            return
        
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1)
        predators = [a for a in neighbors if isinstance(a, Predator)]
        
        if predators:
            target = predators[0]
            self.energy -= 10
            logging.info(f"Охоронець {self.unique_id} вбив Хижака {target.unique_id} в {target.pos}")
            self.model.grid.remove_agent(target)
            self.model.schedule.remove(target)

    def attack_enemy(self):
        if self.tribe_id is None:
            return
        if self.profession not in ["Soldier", "Archer", "Guard"]:
             return
        
        # Check for enemies in range
        attack_radius = 3 if self.profession == "Archer" else 1
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=attack_radius)
        enemies = [
            a for a in neighbors 
            if isinstance(a, Person) and a.tribe_id is not None and a.tribe_id != self.tribe_id
        ]
        
        for enemy in enemies:
            # Check if we are at war
            # War key is sorted tuple of tribe IDs to ensure uniqueness
            war_key = tuple(sorted((self.tribe_id, enemy.tribe_id)))
            if hasattr(self.model, "wars") and war_key in self.model.wars:
                # Attack!
                damage = 20
                if self.profession == "Archer": damage = 15 # Lower damage but range
                
                if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Militaristic":
                    damage += 10
                
                # Religion bonus: War God
                if hasattr(self.model, "tribe_religion") and self.model.tribe_religion.get(self.tribe_id) == "War God":
                    damage += 5

                self.energy -= 5 # Fighting is tiring
                enemy.energy -= damage # Damage
                logging.info(f"{self.profession} {self.unique_id} (Плем'я {self.tribe_id}) атакував Ворога {enemy.unique_id} в {enemy.pos}")
                
                if enemy.energy <= 0:
                    logging.info(f"Ворога {enemy.unique_id} вбито {self.profession} {self.unique_id}")
                    self.model.grid.remove_agent(enemy)
                    self.model.schedule.remove(enemy)
                return # Attack once per turn

    def build_house(self):
        if self.tribe_id is None:
            return # Loners cannot build houses in this implementation

        stockpile = self.model.tribe_stockpiles[self.tribe_id]
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        
        # -1. Library Priority (Critical for Tech)
        if stockpile["wood"] >= 15 and stockpile["stone"] >= 15 and stockpile.get("science", 0) == 0:
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Road, Barracks, Library)) for agent in cell_mates):
                stockpile["wood"] -= 15
                stockpile["stone"] -= 15
                library = Library(self.model, tribe_id=self.tribe_id)
                self.model.schedule.add(library)
                self.model.grid.place_agent(library, self.pos)
                logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} побудувала Бібліотеку (Пріоритет) в {self.pos}")
                return
        
        # 0. Barracks Priority (War) - Highest Priority
        if stockpile["wood"] >= 15 and stockpile["stone"] >= 15:
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Road, Barracks)) for agent in cell_mates):
                 tribe_pop = self.model.tribe_counts.get(self.tribe_id, 0)
                 # Lowered threshold to 5 to encourage militarization
                 if tribe_pop > 5:
                    stockpile["wood"] -= 15
                    stockpile["stone"] -= 15
                    barracks = Barracks(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(barracks)
                    self.model.grid.place_agent(barracks, self.pos)
                    logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} побудувала Казарму в {self.pos}")
                    return

        # 0.5 Library Priority (Science)
        if stockpile["wood"] >= 15 and stockpile["stone"] >= 15:
             # Allow building on Roads (Library on Road is fine)
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Barracks, Library)) for agent in cell_mates):
                 # Build if we have scholars but no library, or just generally if we are rich
                 # Check if tribe already has a library (simple check: do we have science?)
                 # Or just build one if we have the resources, prioritizing the first one
                 
                 # If we have plenty of resources OR we have 0 science (implying no library/research yet)
                 if (stockpile["wood"] >= 15 and stockpile["stone"] >= 15 and stockpile.get("science", 0) == 0) or \
                    (stockpile["wood"] >= 20 and stockpile["stone"] >= 20):
                    stockpile["wood"] -= 15
                    stockpile["stone"] -= 15
                    library = Library(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(library)
                    self.model.grid.place_agent(library, self.pos)
                    logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} побудувала Бібліотеку в {self.pos}")
                    return

        # 0.6 Hospital Priority (Health)
        if stockpile["wood"] >= 10 and stockpile["stone"] >= 5:
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Barracks, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                 # Build if we have healers or plague is active (hard to check global plague here, so just build if rich)
                 # Lowered threshold to ensure construction
                 if stockpile["wood"] >= 12 and stockpile["stone"] >= 6:
                    stockpile["wood"] -= 10
                    stockpile["stone"] -= 5
                    hospital = Hospital(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(hospital)
                    self.model.grid.place_agent(hospital, self.pos)
                    logging.info(f"Людина {self.unique_id} з племені {self.tribe_id} побудувала Лікарню в {self.pos}")
                    return

        # 0.7 Temple Priority (Morale)
        if stockpile["wood"] >= 10 and stockpile["stone"] >= 10:
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Barracks, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                 # Lowered threshold to ensure construction
                 if stockpile["wood"] >= 12 and stockpile["stone"] >= 12:
                    stockpile["wood"] -= 10
                    stockpile["stone"] -= 10
                    temple = Temple(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(temple)
                    self.model.grid.place_agent(temple, self.pos)
                    logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Temple at {self.pos}")
                    return

        # 0.8 Tavern Priority (Social)
        if stockpile["wood"] >= 8 and stockpile["stone"] >= 2:
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Barracks, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                 # Lowered threshold to ensure construction
                 if stockpile["wood"] >= 10 and stockpile["food"] > 50: # Only build if plenty of food
                    stockpile["wood"] -= 8
                    stockpile["stone"] -= 2
                    tavern = Tavern(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(tavern)
                    self.model.grid.place_agent(tavern, self.pos)
                    logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Tavern at {self.pos}")
                    return

        # 1. Smithy Priority: If we have Iron but no tools/smithy, build one!
        # Check if we can build a Smithy (Cost: 3 Wood, 3 Stone)
        if stockpile["wood"] >= 3 and stockpile["stone"] >= 3:
             # Save resources for Hospital/Temple (Need ~12)
             save_threshold = 25 if stockpile.get("science", 0) == 0 else 15
             if stockpile["wood"] > save_threshold and stockpile["stone"] > 10:
                 # Allow building on Roads (Smithy on Road is fine)
                 if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                     # Build if we have iron to process
                     if stockpile.get("iron", 0) > 0:
                        stockpile["wood"] -= 3
                        stockpile["stone"] -= 3
                        smithy = Smithy(self.model, tribe_id=self.tribe_id)
                        self.model.schedule.add(smithy)
                        self.model.grid.place_agent(smithy, self.pos)
                        logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Smithy at {self.pos}")
                        return

        # Check if we can build a Farm (Cost: 2 Wood, 2 Stone)
        # Prioritize farms if food is low (< 50) and we have resources
        if stockpile["food"] < 50 and stockpile["wood"] >= 2 and stockpile["stone"] >= 2:
             # Save resources unless food is critical (< 20)
             save_threshold = 25 if stockpile.get("science", 0) == 0 else 15
             if stockpile["wood"] > save_threshold or stockpile["food"] < 20:
                 if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Road, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                    stockpile["wood"] -= 2
                    stockpile["stone"] -= 2
                    farm = Farm(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(farm)
                    self.model.grid.place_agent(farm, self.pos)
                    logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Farm at {self.pos}")
                    return # Built something, done for this turn

        # Check if we can build a Wall (Cost: 3 Stone)
        # Build walls if we have excess stone and are near a house/farm (simple defense logic)
        if stockpile["stone"] >= 3:
             # Save stone for Temple (Need 12)
             save_threshold = 25 if stockpile.get("science", 0) == 0 else 15
             if stockpile["stone"] > save_threshold:
                 # Check if building already exists here
                 if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Road, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                     # Only build walls next to existing buildings to form a perimeter (simple heuristic)
                     neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=1)
                     if any(isinstance(a, (House, Farm)) for a in neighbors):
                        stockpile["stone"] -= 3
                        wall = Wall(self.model)
                        self.model.schedule.add(wall)
                        self.model.grid.place_agent(wall, self.pos)
                        logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Wall at {self.pos}")
                        return

        # 5. Market Priority (Trade)
        # Build market if we have excess resources and no market nearby
        if stockpile["wood"] >= 15 and stockpile["stone"] >= 15:
             # Allow building on Roads (Market on Road is fine, actually good for trade)
             if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Barracks, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                 # Only build if we have a surplus
                 # Lowered threshold to encourage market building
                 if stockpile["wood"] >= 15 and stockpile["stone"] >= 15:
                    stockpile["wood"] -= 15
                    stockpile["stone"] -= 15
                    market = Market(self.model, tribe_id=self.tribe_id)
                    self.model.schedule.add(market)
                    self.model.grid.place_agent(market, self.pos)
                    logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Market at {self.pos}")
                    return

        # 6. Road Priority (Infrastructure)
        # Build road if we are on a building site or connecting them
        if stockpile["stone"] >= 1:
             # Save stone for Temple/Barracks (Need ~15)
             save_threshold = 25 if stockpile.get("science", 0) == 0 else 15
             if stockpile["stone"] > save_threshold:
                 if not any(isinstance(agent, (Road, House, Farm, Wall, Smithy, Market, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                     # Check neighbors for buildings
                     neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=1)
                     if any(isinstance(a, (House, Farm, Smithy, Market, Road)) for a in neighbors):
                        stockpile["stone"] -= 1
                        road = Road(self.model)
                        self.model.schedule.add(road)
                        self.model.grid.place_agent(road, self.pos)
                        logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a Road at {self.pos}")
                        return

        # 7. House Priority (Expansion)
        # Increased threshold to allow saving for other things
        if stockpile["wood"] >= 3:
            # Save wood for Hospital/Temple (Need ~15)
            save_threshold = 25 if stockpile.get("science", 0) == 0 else 15
            if stockpile["wood"] > save_threshold:
                # Check if building already exists here
                if not any(isinstance(agent, (House, Farm, Wall, Smithy, Market, Road, Library, Hospital, Temple, Tavern)) for agent in cell_mates):
                    stockpile["wood"] -= 3
                    house = House(self.model)
                    self.model.schedule.add(house)
                    self.model.grid.place_agent(house, self.pos)
                    logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} built a House at {self.pos}")

    def form_tribe(self):
        if self.tribe_id is not None:
            return  # Already in a tribe

        # Look for other loners in the same cell
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        loners = [
            agent
            for agent in cell_mates
            if isinstance(agent, Person) and agent.tribe_id is None and agent.unique_id != self.unique_id
        ]

        if loners:
            other_loner = loners[0]
            self.model.form_new_tribe(self, other_loner)

    def trade(self):
        if self.tribe_id is None:
            return  # Loners don't trade

        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        
        # Market Trading Logic
        market = next((a for a in cell_mates if isinstance(a, Market)), None)
        if market:
            # If at a market, trade efficiency is boosted or global trade happens
            pass # Placeholder for advanced market logic

        other_tribe_members = [
            agent
            for agent in cell_mates
            if isinstance(agent, Person) and agent.tribe_id is not None and agent.tribe_id != self.tribe_id
        ]

        if not other_tribe_members:
            return

        other_agent = other_tribe_members[0]
        other_tribe_id = other_agent.tribe_id

        my_stockpile = self.model.tribe_stockpiles[self.tribe_id]
        other_stockpile = self.model.tribe_stockpiles[other_tribe_id]
        
        # Define "need" and "surplus" thresholds
        food_surplus_threshold = 100
        wood_surplus_threshold = 20
        
        # My tribe wants to sell food for wood
        if my_stockpile["food"] > food_surplus_threshold and other_stockpile["wood"] > wood_surplus_threshold:
            # Trade 10 food for 1 wood
            my_stockpile["food"] -= 10
            other_stockpile["food"] += 10
            my_stockpile["wood"] += 1
            other_stockpile["wood"] -= 1
            logging.info(f"Tribe {self.tribe_id} traded 10 food for 1 wood with Tribe {other_tribe_id}")

        # My tribe wants to sell wood for food
        elif my_stockpile["wood"] > wood_surplus_threshold and other_stockpile["food"] > food_surplus_threshold:
            logging.info(f"DEBUG: Trade condition met! My Wood {my_stockpile['wood']}, Other Food {other_stockpile['food']}")
            # Trade 1 wood for 10 food
            my_stockpile["wood"] -= 1
            other_stockpile["wood"] += 1
            my_stockpile["food"] += 10
            other_stockpile["food"] -= 10
            logging.info(f"Tribe {self.tribe_id} traded 1 wood for 10 food with Tribe {other_tribe_id}")

    def reproduce(self):
        # Only reproduce if safe in a house (optional, but good for civilization logic)
        # For now, let's keep it simple: reproduce anywhere, but maybe prefer houses later.
        self.energy -= 25
        child = Person(self.model, tribe_id=self.tribe_id)
        child.energy = 25
        self.model.schedule.add(child)
        self.model.grid.place_agent(child, self.pos)
        logging.info(f"Person {self.unique_id} from tribe {self.tribe_id} reproduced at {self.pos}. New Person {child.unique_id} created in same tribe.")

    def move(self):
        if self.pos is None:
            return
            
        # Check for predators on current cell or nearby
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False, radius=2
        )
        all_others_around = [a for a in (cell_mates + neighbors) if a is not self]
        predators_near = [agent for agent in all_others_around if isinstance(agent, Predator)]
        
        if predators_near:
            # Guards don't flee, they engage
            if self.profession == "Guard":
                nearest_predator = min(predators_near, key=lambda p: self.get_distance(self.pos, p.pos))
                if self.get_distance(self.pos, nearest_predator.pos) > 1:
                     possible_steps = self.model.grid.get_neighborhood(
                        self.pos, moore=True, include_center=False
                     )
                     best_step = min(possible_steps, key=lambda pos: self.get_distance(pos, nearest_predator.pos))
                     self.model.grid.move_agent(self, best_step)
                     return
                else:
                    return # Stay put to attack

            # Check if I am in a house
            if any(isinstance(agent, House) for agent in cell_mates):
                # I am safe, don't move!
                return

            # Run away from the nearest predator
            predator = min(predators_near, key=lambda p: self.get_distance(self.pos, p.pos))
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            # Find step that maximizes distance from predator
            best_step = max(possible_steps, key=lambda pos: self.get_distance(pos, predator.pos))
            self.model.grid.move_agent(self, best_step)
            return

        # --- Desired Target Selection ---
        target_type = None

        if self.tribe_id is not None:
            # Tribe member logic
            stockpile = self.model.tribe_stockpiles[self.tribe_id]
            
            # Profession priorities
            if self.profession == "Farmer":
                target_type = Food
            elif self.profession == "Miner":
                if stockpile.get("iron", 0) < 5:
                    target_type = IronOre
                else:
                    target_type = Stone
            elif self.profession == "Blacksmith":
                target_type = Smithy
            elif self.profession == "Merchant":
                target_type = Market
            elif self.profession == "Scholar":
                target_type = Library
            elif self.profession == "Healer":
                target_type = Hospital
            elif self.profession == "Priest":
                target_type = Temple
            
            # Survival override
            tribe_member_count = self.model.tribe_counts.get(self.tribe_id, 1)
            if stockpile["food"] < tribe_member_count * 5:
                target_type = Food
            
            # Default logic if profession target not found or not critical
            if not target_type:
                if stockpile["food"] < tribe_member_count * 15:
                    target_type = Food
                elif stockpile["wood"] < 3:
                    target_type = Tree
                elif stockpile["stone"] < 5:
                    target_type = Stone
        else:
            # Loner logic
            if self.energy < 20:
                target_type = Food

        # --- Memory-Based Movement (Star Pathfinding) ---
        if target_type:
            target_pos = None
            
            # 1. Check immediate surroundings first (updated via scan_environment usually, but good to be sure)
            current_area_targets = [
                a for a in self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1)
                if isinstance(a, target_type)
            ]
            if current_area_targets:
                 target_pos = current_area_targets[0].pos
            
            # 2. Check Memory
            elif target_type in self.memory and self.memory[target_type]:
                # Find closest memory location
                possible_locations = list(self.memory[target_type])
                possible_locations.sort(key=lambda p: self.get_distance(self.pos, p))
                
                # Verify and cleanup memory if we are there and it's empty
                valid_target_found = False
                for loc in possible_locations:
                    if loc == self.pos:
                        # We are here but didn't find it in step 1 -> It's gone
                        self.memory[target_type].remove(loc)
                        continue
                    else:
                        target_pos = loc
                        valid_target_found = True
                        break
                
                if not valid_target_found:
                    target_pos = None

            # 3. Pathfind to target
            if target_pos:
                path = a_star_search(self.model, self.pos, target_pos)
                if path and len(path) > 0:
                    next_step = path[0]
                    self.model.grid.move_agent(self, next_step)
                    return
                else:
                     # Path blocked or unreachable, maybe remove from memory or Ignore
                     pass

        # Random move (exploration)
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        
        weights = []
        valid_steps = []
        for step in possible_steps:
             cost = self.model.get_movement_cost(step)
             if cost < 100: # Filter passable
                 valid_steps.append(step)
                 weights.append(1.0 / cost)
        
        if valid_steps:
             new_position = self.random.choices(valid_steps, weights=weights, k=1)[0]
             self.model.grid.move_agent(self, new_position)
        
        return 

    def get_distance(self, pos1, pos2):
        # Manhattan distance for simplicity
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def gather_food(self):
        # Loners eat directly, they don't have a stockpile
        if self.tribe_id is None:
            cell_mates = self.model.grid.get_cell_list_contents([self.pos])
            for agent in cell_mates:
                if isinstance(agent, Food):
                    amount = 20
                    if self.profession == "Farmer":
                        amount += 5
                    self.energy += amount
                    logging.info(f"Loner {self.unique_id} ate food at {self.pos}. Energy: {self.energy}")
                    self.model.grid.remove_agent(agent)
                    self.model.schedule.remove(agent)
                    break
            return

        # Tribe members contribute to the stockpile
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_mates:
            if isinstance(agent, Food):
                # Each food item provides 20 units of energy/food
                amount = 20
                if self.profession == "Farmer":
                    amount += 5
                # Trait bonus
                if hasattr(self.model, "tribe_traits") and self.model.tribe_traits.get(self.tribe_id) == "Agrarian":
                    amount += 2

                # Tech bonus: Irrigation
                if hasattr(self.model, "tribe_technologies"):
                    techs = self.model.tribe_technologies.get(self.tribe_id, set())
                    if "Agriculture" in techs: amount += 1
                    if "Irrigation" in techs: amount += 2

                # Leader bonus
                if hasattr(self.model, "tribe_leaders") and self.tribe_id in self.model.tribe_leaders:
                    amount += 2 # +2 food bonus
                
                # Religion bonus: Harvest God
                if hasattr(self.model, "tribe_religion") and self.model.tribe_religion.get(self.tribe_id) == "Harvest God":
                    amount += 3
                
                # Religion bonus: Sea God
                if hasattr(self.model, "tribe_religion") and self.model.tribe_religion.get(self.tribe_id) == "Sea God":
                    amount += 1

                self.model.tribe_stockpiles[self.tribe_id]["food"] += amount
                logging.info(f"Person {self.unique_id} of tribe {self.tribe_id} gathered food. Tribe food: {self.model.tribe_stockpiles[self.tribe_id]['food']}")
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
                break
    
    def withdraw_food(self):
        if self.tribe_id is None:
            return  # Loners don't have a stockpile

        stockpile = self.model.tribe_stockpiles[self.tribe_id]

        # 1. Survival: If hungry, take from stockpile
        if self.energy < 20:
            if stockpile["food"] > 0:
                # Take what is needed to reach 30 energy, or whatever is left
                amount_to_take = min(30 - self.energy, stockpile["food"])
                self.energy += amount_to_take
                stockpile["food"] -= amount_to_take
                logging.info(f"Person {self.unique_id} of tribe {self.tribe_id} withdrew {amount_to_take} food for survival. Energy: {self.energy}")

        # 2. Prosperity: If tribe is rich, take food to reproduce
        # If energy is below reproduction threshold (40) but above hunger (20)
        # And stockpile has a healthy surplus (e.g., > 50)
        elif self.energy < 40 and stockpile["food"] > 50:
             # Take enough to reach reproduction threshold + a bit extra (target 45)
             amount_to_take = min(45 - self.energy, stockpile["food"])
             self.energy += amount_to_take
             stockpile["food"] -= amount_to_take
             logging.info(f"Person {self.unique_id} of tribe {self.tribe_id} withdrew {amount_to_take} food for reproduction. Energy: {self.energy}")

class Predator(Agent):
    def __init__(self, model, pack_id=None):
        super().__init__(model)
        self.energy = 50  # Increased initial energy
        self.age = 0
        self.pack_id = pack_id

    def step(self):
        if self.pos is None:
            return

        self.age += 1
        self.energy -= 1

        if self.energy <= 0:
            reason = "starvation"
            logging.info(f"Predator {self.unique_id} died of {reason} at {self.pos}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        if self.age >= 60:
            reason = "old age"
            logging.info(f"Predator {self.unique_id} died of {reason} at {self.pos}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # --- ACTION on current cell ---
        self.eat()

        if self.energy >= 80:  # Increased threshold to control population
            self.reproduce()

        # --- MOVE at the end ---
        self.move()

    def move(self):
        if self.pos is None:
            return
        # Look for Person in neighbors
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False, radius=2  # Restored vision radius
        )
        prey_near = [agent for agent in neighbors if isinstance(agent, Person)]
        
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        
        # Filter out steps that are blocked by Walls
        valid_steps = []
        for step in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents([step])
            if not any(isinstance(agent, Wall) for agent in cell_contents):
                valid_steps.append(step)
                
        if not valid_steps:
            return # Trapped!

        if prey_near:
            target = prey_near[0]
            # Only consider valid steps
            best_step = min(valid_steps, key=lambda pos: self.get_distance(pos, target.pos))
            self.model.grid.move_agent(self, best_step)
        else:
            new_position = self.random.choice(valid_steps)
            self.model.grid.move_agent(self, new_position)

    def eat(self):
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        
        has_house = any(isinstance(agent, House) for agent in cell_mates)
        
        pack_strength = 0
        if self.pack_id is not None:
            # Count pack members on the same cell
            pack_strength = len([
                agent 
                for agent in cell_mates 
                if isinstance(agent, Predator) and agent.pack_id == self.pack_id
            ])
            logging.info(f"DEBUG: Predator {self.unique_id} strength check. Strength: {pack_strength}, House: {has_house}")

        # A lone predator (or small pack) cannot attack a house
        if has_house and pack_strength < 3:
            logging.info(f"DEBUG: Predator {self.unique_id} blocked by house (strength {pack_strength} < 3)")
            return

        # If the pack is strong enough (or if there's no house), attack
        for agent in cell_mates:
            if isinstance(agent, Person):
                self.energy += 20
                logging.info(f"Predator {self.unique_id} (pack {self.pack_id}, strength {pack_strength}) ate Person {agent.unique_id} at {self.pos}")
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
                # Only eat one person per step
                break

    def reproduce(self):
        self.energy -= 30
        child = Predator(self.model, pack_id=self.pack_id)
        child.energy = 30
        self.model.schedule.add(child)
        self.model.grid.place_agent(child, self.pos)
        logging.info(f"Хижак {self.unique_id} зі зграї {self.pack_id} розмножився в {self.pos}")

    def get_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

class Barbarian(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 50
    
    def step(self):
        if self.pos is None:
            return
        
        self.energy -= 1
        if self.energy <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # Attack logic
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_mates:
            if isinstance(agent, (Person, House, Farm, Smithy, Market, Barracks, Library, Hospital, Temple, Tavern)):
                if isinstance(agent, Person):
                    agent.energy -= 20
                    self.energy += 10
                    logging.info(f"Варвар атакував Людину {agent.unique_id} в {self.pos}")
                    if agent.energy <= 0:
                        self.model.grid.remove_agent(agent)
                        self.model.schedule.remove(agent)
                else:
                    # Destroy building
                    logging.info(f"Варвар знищив {type(agent).__name__} в {self.pos}")
                    self.model.grid.remove_agent(agent)
                    self.model.schedule.remove(agent)
                return # Attack once per turn

        # Move logic: Move towards nearest building or person
        # ... (Simple random move for now)
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        # Filter out Mountains
        valid_steps = []
        for step in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents([step])
            if not any(isinstance(agent, Mountain) for agent in cell_contents):
                valid_steps.append(step)
        
        if valid_steps:
            new_position = self.random.choice(valid_steps)
            self.model.grid.move_agent(self, new_position)
