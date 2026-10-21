"""
Collision-aware movement controller for the warehouse fleet.
Coordinates robot movement using existing A* paths.
"""

from warehouse import ROWS, COLS, warehouse

MOVE_INTERVAL = 10


def update_collision_aware(robots):
    """Advance robots safely by one coordinated movement step."""

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

        while robot.path and tuple(robot.path[0]) == (
            robot.row, robot.col
        ):
            robot.path.pop(0)

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

    proposed = {}

    # Give each contested destination to the lowest robot ID.
    for robot, target in sorted(
        ready, key=lambda item: item[0].robot_id
    ):
        if target not in proposed.values():
            proposed[robot] = target

    # Prevent head-on swaps.
    for robot, target in list(proposed.items()):
        other = occupied.get(target)

        if other is None or other not in proposed:
            continue

        if proposed[other] == (robot.row, robot.col):
            proposed.pop(robot, None)
            proposed.pop(other, None)

    # A robot may enter an occupied cell only if its occupant
    # is also approved to leave. Repeat after cancellations.
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
        if robot.path and tuple(robot.path[0]) == target:
            robot.path.pop(0)

        robot.row, robot.col = target
