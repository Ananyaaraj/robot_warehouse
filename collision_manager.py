"""
Collision-aware warehouse fleet movement.
Uses stable rerouting and simultaneous collision checks.
"""

from warehouse import ROWS, COLS, warehouse
from pathfinding import a_star

MOVE_INTERVAL = 10


def _clean_path(robot):
    """Remove the robot's current cell from the front of its path."""
    while robot.path and tuple(robot.path[0]) == (
        robot.row, robot.col
    ):
        robot.path.pop(0)


def _reroute_if_blocked(robot, robots):
    """Try one alternative route when the next cell is occupied."""
    _clean_path(robot)

    if not robot.path:
        return

    target = tuple(robot.path[0])
    occupied_by_other = any(
        other is not robot
        and (other.row, other.col) == target
        for other in robots
    )

    if not occupied_by_other:
        return

    # The final path cell is the robot's intended destination.
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


def update_collision_aware(robots):
    """Advance robots without overlapping or swapping positions."""

    # Only attempt rerouting when a robot's next cell is occupied.
    for robot in robots:
        _reroute_if_blocked(robot, robots)

    occupied = {
        (robot.row, robot.col): robot
        for robot in robots
    }

    ready = []

    for robot in robots:
        if not robot.path:
            continue

        robot.move_timer += 1

        if robot.move_timer < MOVE_INTERVAL:
            continue

        robot.move_timer = 0
        _clean_path(robot)

        if not robot.path:
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

    # Resolve destination conflicts deterministically.
    proposed = {}

    for robot, target in sorted(
        ready, key=lambda item: item[0].robot_id
    ):
        if target not in proposed.values():
            proposed[robot] = target

    # Cancel head-on swaps.
    for robot, target in list(proposed.items()):
        other = occupied.get(target)

        if other is None or other not in proposed:
            continue

        if proposed[other] == (robot.row, robot.col):
            proposed.pop(robot, None)
            proposed.pop(other, None)

    # Cancel moves into cells whose occupants won't leave.
    changed = True

    while changed:
        changed = False

        for robot, target in list(proposed.items()):
            occupant = occupied.get(target)

            if occupant is not None and occupant not in proposed:
                proposed.pop(robot)
                changed = True

    # Apply approved moves together.
    for robot, target in proposed.items():
        _clean_path(robot)

        if robot.path and tuple(robot.path[0]) == target:
            robot.path.pop(0)

        robot.row, robot.col = target
