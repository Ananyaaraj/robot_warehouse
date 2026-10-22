"""
Collision-aware warehouse fleet movement.
Provides conflict-free multi-robot movement, swap prevention,
deadlock detection, heading updates, and movement event accounting.
"""

from warehouse import ROWS, COLS, warehouse
from pathfinding import a_star, get_neighbors

MOVE_INTERVAL = 10


def _clean_path(robot):
    """Remove the robot's current cell from the front of its path."""
    while robot.path and tuple(robot.path[0]) == (
        robot.row, robot.col
    ):
        robot.path.pop(0)


def _reroute_if_blocked(robot, robots):
    """Try an alternative route when the immediate next cell is occupied."""
    _clean_path(robot)

    if not robot.path:
        return False

    target = tuple(robot.path[0])
    occupied_by_other = any(
        other is not robot
        and (other.row, other.col) == target
        for other in robots
    )

    if not occupied_by_other:
        return False

    # The final path cell is the robot's intended destination
    goal = tuple(robot.path[-1])

    blocked = {
        (other.row, other.col)
        for other in robots
        if other is not robot
    }

    alternative = a_star(
        (robot.row, robot.col),
        goal,
        blocked_positions=blocked
    )

    if alternative and len(alternative) > 1:
        robot.path = alternative
        return True

    return False


def _resolve_deadlock(robot, robots):
    """Attempt a detour or side-step to break persistent deadlocks."""
    _clean_path(robot)
    if not robot.path:
        return False

    goal = tuple(robot.path[-1])
    occupied = {
        (other.row, other.col)
        for other in robots
        if other is not robot
    }

    # First attempt: full replan with all other robots blocked
    alt = a_star((robot.row, robot.col), goal, blocked_positions=occupied)
    if alt and len(alt) > 1:
        robot.path = alt
        return True

    # Second attempt: sidestep to an adjacent free cell
    neighbors = get_neighbors((robot.row, robot.col), blocked_positions=occupied)
    if neighbors:
        # Choose neighbor closest to goal
        neighbors.sort(key=lambda n: abs(n[0] - goal[0]) + abs(n[1] - goal[1]))
        escape_cell = neighbors[0]
        # Replan from escape cell to goal
        escape_path = a_star(escape_cell, goal, blocked_positions=occupied)
        if escape_path:
            robot.path = [escape_cell] + escape_path
            return True

    return False


def update_collision_aware(robots, enforce_timer=True):
    """
    Advance robots without overlapping or swapping positions.
    Returns metrics dictionary with movement statistics.
    """
    metrics = {
        "moves_executed": 0,
        "conflicts_resolved": 0,
        "swaps_prevented": 0,
        "deadlocks_detected": 0
    }

    # Step 1: Pre-emptively reroute robots if next cell is occupied
    for robot in robots:
        if not robot.is_faulty:
            _reroute_if_blocked(robot, robots)

    occupied = {
        (robot.row, robot.col): robot
        for robot in robots
    }

    ready = []

    for robot in robots:
        if robot.is_faulty or not robot.path:
            robot.drain_idle()
            continue

        if enforce_timer:
            robot.move_timer += 1
            if robot.move_timer < MOVE_INTERVAL:
                continue
            robot.move_timer = 0

        _clean_path(robot)

        if not robot.path:
            robot.drain_idle()
            continue

        target = tuple(robot.path[0])
        row, col = target

        if not (0 <= row < ROWS and 0 <= col < COLS):
            continue

        if warehouse[row][col] != 0:
            continue

        if abs(row - robot.row) + abs(col - robot.col) != 1:
            continue

        ready.append((robot, target))

    # Resolve destination conflicts deterministically (lowest robot_id takes precedence)
    proposed = {}
    ready_robots = {r for r, _ in ready}

    for robot, target in sorted(
        ready, key=lambda item: item[0].robot_id
    ):
        if target not in proposed.values():
            proposed[robot] = target
        else:
            metrics["conflicts_resolved"] += 1

    # Cancel head-on swaps (Robot A -> B, Robot B -> A)
    for robot, target in list(proposed.items()):
        other = occupied.get(target)

        if other is None or other not in proposed:
            continue

        if proposed[other] == (robot.row, robot.col):
            proposed.pop(robot, None)
            proposed.pop(other, None)
            metrics["swaps_prevented"] += 2

    # Cancel moves into cells whose occupants won't leave
    changed = True
    while changed:
        changed = False
        for robot, target in list(proposed.items()):
            occupant = occupied.get(target)
            if occupant is not None and occupant not in proposed:
                proposed.pop(robot)
                metrics["conflicts_resolved"] += 1
                changed = True

    # Check for blocked robots & handle deadlock detection
    for robot in ready_robots:
        if robot not in proposed:
            robot.blocked_steps += 1
            robot.drain_idle()
            if robot.blocked_steps >= 4:
                metrics["deadlocks_detected"] += 1
                _resolve_deadlock(robot, robots)
        else:
            robot.blocked_steps = 0

    # Apply approved moves together
    for robot, target in proposed.items():
        _clean_path(robot)

        if robot.path and tuple(robot.path[0]) == target:
            robot.path.pop(0)

        # Update heading and position
        robot.update_heading_from_step(target[0], target[1])
        robot.row, robot.col = target
        robot.drain_move()
        metrics["moves_executed"] += 1

    return metrics
