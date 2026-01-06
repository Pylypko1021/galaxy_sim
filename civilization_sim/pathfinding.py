import heapq

def a_star_search(model, start, goal):
    """
    A* Pathfinding algorithm.
    :param model: The MESA model (needs grid and get_movement_cost)
    :param start: (x, y) tuple
    :param goal: (x, y) tuple
    :return: List of tuples [(x, y), ...] representing the path (excluding start, including goal) or None
    """
    
    # Priority queue stores (f_score, h_score, current_node)
    open_set = []
    heapq.heappush(open_set, (0, 0, start))
    
    came_from = {}
    
    # Cost from start to current node
    g_score = {start: 0}
    
    # Estimated cost from start to goal through current node (f = g + h)
    f_score = {start: heuristic(start, goal)}
    
    open_set_hash = {start}
    
    while open_set:
        current = heapq.heappop(open_set)[2]
        open_set_hash.remove(current)
        
        if current == goal:
            return reconstruct_path(came_from, current)
        
        # Get neighbors (Von Neumann or Moore? Let's use Moore as per simulation standard usually)
        # Using moore=True, include_center=False
        neighbors = model.grid.get_neighborhood(current, moore=True, include_center=False)
        
        for neighbor in neighbors:
            # Check if passable (cost < 100)
            cost = model.get_movement_cost(neighbor)
            if cost >= 100:
                continue
            
            tentative_g_score = g_score[current] + cost
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f = tentative_g_score + heuristic(neighbor, goal)
                f_score[neighbor] = f
                
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f, heuristic(neighbor, goal), neighbor))
                    open_set_hash.add(neighbor)
                    
    return None # No path found

def heuristic(a, b):
    # Manhattan distance is good for grid, but Chebyshev is better for Moore neighborhood
    # return abs(a[0] - b[0]) + abs(a[1] - b[1])
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    # The path is from goal to start, so reverse it
    # We remove the start node because the agent is already there
    return total_path[::-1][1:]
