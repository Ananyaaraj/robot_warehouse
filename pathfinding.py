import heapq

from warehouse import ROWS, COLS, warehouse


# ==========================================
# A* HEURISTIC
# ==========================================

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ==========================================
# GET VALID NEIGHBORS
# ==========================================

def get_neighbors(position):

    row, col = position

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    neighbors = []

    for dr, dc in directions:

        new_row = row + dr
        new_col = col + dc

        if 0 <= new_row < ROWS and 0 <= new_col < COLS:

            if warehouse[new_row][new_col] == 0:
                neighbors.append((new_row, new_col))

    return neighbors


# ==========================================
# A* PATHFINDING
# ==========================================

def a_star(start, goal):

    open_set = []

    heapq.heappush(
        open_set,
        (0, start)
    )

    came_from = {}

    g_score = {
        start: 0
    }

    while open_set:

        current = heapq.heappop(open_set)[1]

        # Goal reached
        if current == goal:

            path = []

            while current in came_from:

                path.append(current)
                current = came_from[current]

            path.append(start)
            path.reverse()

            return path

        # Explore neighbors
        for neighbor in get_neighbors(current):

            tentative_g = g_score[current] + 1

            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g
                    + heuristic(neighbor, goal)
                )

                heapq.heappush(
                    open_set,
                    (f_score, neighbor)
                )

    # No path found
    return []