
import time
import logging
from civilization_sim.model import CivilizationModel
from civilization_sim.agents import Person, House, Farm, Smithy, Market, Barracks, Road, Library, Hospital, Temple, Tavern, Barbarian

# Configure logging to file only
logging.basicConfig(
    filename='stage4_5_simulation.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)

def run_stage4_5_simulation():
    print("=== ЗАПУСК СИМУЛЯЦІЇ ЕТАПІВ 4 ТА 5 (ДОБРОБУТ І КАТАКЛІЗМИ) ===")
    width = 50
    height = 50
    initial_people = 100
    num_tribes = 5
    steps = 1000 # Enough to see invasions and droughts
    
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
    
    drought_count = 0
    invasion_count = 0
    
    for i in range(steps):
        model.step()
        
        if (i + 1) % 100 == 0:
            # Gather stats
            people = sum(1 for a in model.schedule.agents if isinstance(a, Person))
            hospitals = sum(1 for a in model.schedule.agents if isinstance(a, Hospital))
            temples = sum(1 for a in model.schedule.agents if isinstance(a, Temple))
            taverns = sum(1 for a in model.schedule.agents if isinstance(a, Tavern))
            barbarians = sum(1 for a in model.schedule.agents if isinstance(a, Barbarian))
            
            print(f"Крок {i+1}: Нас={people}, Лікарень={hospitals}, Храмів={temples}, Таверн={taverns}, Варварів={barbarians}")
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
    smithies = len([a for a in model.schedule.agents if isinstance(a, Smithy)])
    markets = len([a for a in model.schedule.agents if isinstance(a, Market)])
    barracks = len([a for a in model.schedule.agents if isinstance(a, Barracks)])
    libraries = len([a for a in model.schedule.agents if isinstance(a, Library)])
    hospitals = len([a for a in model.schedule.agents if isinstance(a, Hospital)])
    temples = len([a for a in model.schedule.agents if isinstance(a, Temple)])
    taverns = len([a for a in model.schedule.agents if isinstance(a, Tavern)])
    roads = len([a for a in model.schedule.agents if isinstance(a, Road)])
    
    print(f"\nФінальне населення: {len(people)}")
    print(f"Побудовано будівель:")
    print(f"  - Будинки: {houses}")
    print(f"  - Ферми: {farms}")
    print(f"  - Кузні: {smithies}")
    print(f"  - Ринки: {markets}")
    print(f"  - Казарми: {barracks}")
    print(f"  - Бібліотеки: {libraries}")
    print(f"  - Лікарні: {hospitals}")
    print(f"  - Храми: {temples}")
    print(f"  - Таверни: {taverns}")
    print(f"  - Дороги: {roads}")
    
    # Check logs for specific events
    print("\nАналіз подій (з логів):")
    try:
        with open('stage4_5_simulation.log', 'r') as f:
            logs = f.read()
            print(f"  - Вторгнень варварів: {logs.count('BARBARIAN INVASION')}")
            print(f"  - Посух почалося: {logs.count('A DROUGHT has begun')}")
            print(f"  - Відновлень від чуми: {logs.count('recovered from plague')}")
            print(f"  - Смертей від чуми: {logs.count('died of plague')}")
            print(f"  - Варварів знищило будівель: {logs.count('Barbarian destroyed')}")
    except FileNotFoundError:
        print("  Log file not found.")

if __name__ == "__main__":
    run_stage4_5_simulation()
