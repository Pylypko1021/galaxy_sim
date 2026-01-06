
import time
import logging
from civilization_sim.model import CivilizationModel
from civilization_sim.new_agents.people import Person, Barbarian
from civilization_sim.new_agents.buildings import House, Farm, Smithy, Market, Barracks, Road, Library, Hospital, Temple, Tavern
from civilization_sim.new_agents.resources import Mountain, River

# Configure logging to file only
logging.basicConfig(
    filename='stage7_simulation.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)

def run_stage7_simulation():
    print("=== ЗАПУСК СИМУЛЯЦІЇ ЕТАПУ 7 (ГЕОГРАФІЯ ТА ЕКОЛОГІЯ) ===")
    width = 50
    height = 50
    initial_people = 100
    num_tribes = 5
    steps = 1000 
    
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
    
    # Terrain Stats
    mountains = sum(1 for a in model.schedule.agents if isinstance(a, Mountain))
    rivers = sum(1 for a in model.schedule.agents if isinstance(a, River))
    print(f"Згенеровано ландшафт: Гір={mountains}, Річок (клітин)={rivers}")
    print("-" * 40)

    start_time = time.time()
    
    for i in range(steps):
        model.step()
        
        if (i + 1) % 100 == 0:
            # Gather stats
            people = sum(1 for a in model.schedule.agents if isinstance(a, Person))
            farms = sum(1 for a in model.schedule.agents if isinstance(a, Farm))
            
            print(f"Крок {i+1} ({model.season}): Нас={people}, Ферм={farms}")
            if model.drought_active:
                print("  [!] ПОСУХА АКТИВНА")

    end_time = time.time()
    duration = end_time - start_time
    
    print("-" * 40)
    print("=== СИМУЛЯЦІЯ ЗАВЕРШЕНА ===")
    print(f"Тривалість: {duration:.2f} сек")
    
    # Final Stats
    people = [a for a in model.schedule.agents if isinstance(a, Person)]
    houses = len([a for a in model.schedule.agents if isinstance(a, House)])
    farms = len([a for a in model.schedule.agents if isinstance(a, Farm)])
    
    print(f"\nФінальне населення: {len(people)}")
    print(f"Побудовано будівель:")
    print(f"  - Будинки: {houses}")
    print(f"  - Ферми: {farms}")
    
    # Check logs for specific events
    print("\nАналіз подій (з логів):")
    try:
        with open('stage7_simulation.log', 'r') as f:
            logs = f.read()
            print(f"  - Змін сезонів: {logs.count('SEASON CHANGE')}")
            print(f"  - Вторгнень варварів: {logs.count('BARBARIAN INVASION')}")
    except FileNotFoundError:
        print("Лог файл не знайдено.")

if __name__ == "__main__":
    run_stage7_simulation()
