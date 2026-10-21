import heapq

from warehouse import ROWS, COLS, warehouse


def heuristic(a, b):
    """Manhattan distance for four-directional movement."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(position, blocked_positions=None):
    """Return walkable neighbors, excluding temporarily blocked cells."""
    row, col = position
    blocked_positions = set(blocked_positions or ())

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
        neighbor = (new_row, new_col)

        if not (0 <= new_row < ROWS and 0 <= new_col < COLS):
            continue

        if warehouse[new_row][new_col] != 0:
            continue

        if neighbor in blocked_positions:
            continue

        neighbors.append(neighbor)

    return neighbors


def a_star(start, goal, blocked_positions=None):
    """
    Find a path using A*.

    blocked_positions contains temporary obstacles such as other robots.
    The start cell is always allowed, but other blocked cells are avoided.
    Returns a list from start to goal, or [] if no path exists.
    """
    start = tuple(start)
    goal = tuple(goal)
    blocked_positions = set(blocked_positions or ())
    blocked_positions.discard(start)

    if not (0 <= start[0] < ROWS and 0 <= start[1] < COLS):
        return []

    if not (0 <= goal[0] < ROWS and 0 <= goal[1] < COLS):
        return []

    if warehouse[start[0]][start[1]] != 0:
        return []

    if warehouse[goal[0]][goal[1]] != 0:
        return []

    if goal in blocked_positions:
        return []

    open_set = [(heuristic(start, goal), start)]
    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in closed_set:
            continue

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            return path

        closed_set.add(current)

        for neighbor in get_neighbors(current, blocked_positions):
            if neighbor in closed_set:
                continue

            tentative_g = g_score[current] + 1

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                f_score = tentative_g + heuristic(neighbor, goal)

                heapq.heappush(open_set, (f_score, neighbor))

    return []
