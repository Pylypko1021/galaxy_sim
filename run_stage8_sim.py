
import time
import logging
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person

# Configure logging to file only
logging.basicConfig(
    filename='stage8_simulation.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)

def run_stage8_simulation():
    print("=== ЗАПУСК СИМУЛЯЦІЇ ЕТАПУ 8 (UTILITY AI) ===")
    width = 50
    height = 50
    initial_people = 100
    num_tribes = 5
    steps = 500 
    
    model = CivilizationModel(
        width=width, 
        height=height, 
        initial_people=initial_people,
        initial_food=200,
        initial_trees=100,
        initial_stone=50,
        initial_iron=20,
        num_tribes=num_tribes,
        num_predator_packs=3
    )
    
    print(f"Карта: {width}x{height}")
    print(f"Агенти: {initial_people}")
    print(f"Племена: {num_tribes}")
    print(f"Кроки: {steps}")
    print("-" * 40)

    start_time = time.time()
    
    for i in range(steps):
        model.step()
        
        if i % 50 == 0:
            print(f"\n--- Крок {i} ---")
            people_count = sum(1 for a in model.schedule.agents if isinstance(a, Person))
            print(f"Популяція: {people_count}")
            
            # Check stockpiles to see if gathering is working
            for tribe_id, stock in model.tribe_stockpiles.items():
                print(f"  Плем'я {tribe_id}: Їжа={stock['food']}, Дерево={stock['wood']}, Камінь={stock['stone']}")

    end_time = time.time()
    print("-" * 40)
    print(f"Симуляція завершена за {end_time - start_time:.2f} секунд")

if __name__ == "__main__":
    run_stage8_simulation()
