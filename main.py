
import pygame
import sys

from warehouse import ROWS, COLS, CELL_SIZE, warehouse
from benchmark_loader import MAP_FILE, SCENARIO_DIR, load_map, load_scenarios
from robot import Robot
from task import Task
from task_generator import TaskGenerator
from task_queue import TaskQueue


# ==========================================
# INITIALIZE PYGAME
# ==========================================

pygame.init()

WIDTH = 1100
HEIGHT = 750

GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE

OFFSET_X = max(10, (WIDTH - GRID_WIDTH) // 2)
OFFSET_Y = 220

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multi-Robot Warehouse Benchmark")

clock = pygame.time.Clock()



# ==========================================
# LOAD BENCHMARK SCENARIOS
# ==========================================

print("Loading warehouse benchmark scenarios...")

benchmark_map = load_map(MAP_FILE)

scenario_file = (
    SCENARIO_DIR / "warehouse-10-20-10-2-1-random-1.scen"
)

scenarios = load_scenarios(scenario_file, benchmark_map)

if len(scenarios) < 8:
    pygame.quit()
    raise RuntimeError("Not enough benchmark scenarios loaded.")

print(f"Loaded {len(scenarios)} benchmark scenarios.")


# Benchmark coordinates are (x, y).
# The simulation uses (row, column) = (y, x).

def to_grid_position(position):
    x, y = position
    return (y, x)


# ==========================================
# CREATE FIVE ROBOTS AT VALID LOCATIONS
# ==========================================

robot_positions = []
used_positions = set()

for scenario in scenarios:
    position = to_grid_position(scenario.start)

    if position in used_positions:
        continue

    row, col = position

    if warehouse[row][col] == 0:
        robot_positions.append(position)
        used_positions.add(position)

    if len(robot_positions) == 5:
        break

if len(robot_positions) < 5:
    pygame.quit()
    raise RuntimeError("Could not find five unique robot start positions.")

robots = [
    Robot(row, col, robot_id, OFFSET_X, OFFSET_Y)
    for robot_id, (row, col) in enumerate(robot_positions, start=1)
]

for robot in robots:
    print(
        f"Robot R{robot.robot_id} starts at "
        f"(row={robot.row}, col={robot.col})"
    )


# ==========================================
# CREATE INITIAL TASKS FROM SCENARIOS
# ==========================================

priorities = ["HIGH", "MEDIUM", "LOW"]
tasks = []

for task_id, scenario in enumerate(scenarios[5:8], start=1):
    pickup = to_grid_position(scenario.start)
    dropoff = to_grid_position(scenario.goal)

    task = Task(
        task_id,
        pickup,
        dropoff,
        priorities[task_id - 1]
    )

    tasks.append(task)

    print(
        f"Task T{task_id}: pickup={pickup}, "
        f"drop-off={dropoff}, priority={task.priority}"
    )


# ==========================================
# TASK GENERATOR AND QUEUE
# ==========================================

task_generator = TaskGenerator(start_id=len(tasks) + 1)
task_queue = TaskQueue()

for task in tasks:
    task_queue.add_task(task)


# ==========================================
# SELECTED ROBOT
# ==========================================

selected_robot = 1


# ==========================================
# FIND NEAREST AVAILABLE ROBOT
# ==========================================

def calculate_distance(robot, location):
    return (
        abs(robot.row - location[0])
        + abs(robot.col - location[1])
    )


def find_nearest_available_robot(task):
    available_robots = [
        (calculate_distance(robot, task.pickup), robot)
        for robot in robots
        if robot.current_task is None
    ]

    if not available_robots:
        return None

    available_robots.sort(key=lambda item: item[0])
    return available_robots[0][1]


# ==========================================
# ASSIGN TASK
# ==========================================

def assign_task(task):
    robot = find_nearest_available_robot(task)

    if robot is None:
        print("No available robot for this task.")
        return False

    robot.current_task = task
    robot.task_stage = "GOING_TO_PICKUP"

    task.assign_robot(robot.robot_id)

    pickup_row, pickup_col = task.pickup
    robot.set_destination(pickup_row, pickup_col)

    # A path is empty if the robot is already at the target,
    # or if pathfinding cannot find a route.
    if (
        (robot.row, robot.col) != task.pickup
        and not robot.path
    ):
        robot.current_task = None
        robot.task_stage = "IDLE"
        task.status = "WAITING"

        print(
            f"No route to pickup for Task T{task.task_id}. "
            "Task remains waiting."
        )
        return False

    print(
        f"Task T{task.task_id} assigned to Robot R{robot.robot_id}"
    )

    return True


def assign_next_task():
    task = task_queue.get_next_task()

    if task is None:
        print("No waiting tasks.")
        return

    assign_task(task)


# ==========================================
# AUTOMATIC TASK EXECUTION
# ==========================================

def update_robot_tasks():
    for robot in robots:
        task = robot.current_task

        if task is None or robot.path:
            continue

        current_position = (robot.row, robot.col)

        # Stage 1: Reach pickup
        if robot.task_stage == "GOING_TO_PICKUP":

            if current_position == task.pickup:
                robot.task_stage = "GOING_TO_DROPOFF"

                drop_row, drop_col = task.dropoff
                robot.set_destination(drop_row, drop_col)

                if (
                    current_position != task.dropoff
                    and not robot.path
                ):
                    print(
                        f"No route to drop-off for Task T{task.task_id}."
                    )
                    robot.task_stage = "DROP_OFF_BLOCKED"
                    continue

                print(
                    f"Robot R{robot.robot_id} picked up "
                    f"Task T{task.task_id}"
                )

        # Stage 2: Reach drop-off
        elif robot.task_stage == "GOING_TO_DROPOFF":

            if current_position == task.dropoff:
                task.complete()

                print(
                    f"Task T{task.task_id} completed by "
                    f"Robot R{robot.robot_id}"
                )

                robot.current_task = None
                robot.task_stage = "IDLE"


# ==========================================
# DRAW WAREHOUSE
# ==========================================

def draw_warehouse():
    for row in range(ROWS):
        for col in range(COLS):
            x = OFFSET_X + col * CELL_SIZE
            y = OFFSET_Y + row * CELL_SIZE

            if warehouse[row][col] == 1:
                color = (100, 100, 100)
            else:
                color = (45, 45, 45)

            pygame.draw.rect(
                screen,
                color,
                (x, y, CELL_SIZE, CELL_SIZE)
            )

            pygame.draw.rect(
                screen,
                (65, 65, 65),
                (x, y, CELL_SIZE, CELL_SIZE),
                1
            )


# ==========================================
# MAIN LOOP
# ==========================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if pygame.K_1 <= event.key <= pygame.K_5:
                selected_robot = event.key - pygame.K_0
                print(f"Selected Robot R{selected_robot}")

            elif event.key == pygame.K_a:
                assign_next_task()

            elif event.key == pygame.K_t:
                new_task = task_generator.generate_task()

                tasks.append(new_task)
                task_queue.add_task(new_task)

                print(
                    f"Generated Task T{new_task.task_id}: "
                    f"{new_task.pickup} -> {new_task.dropoff}, "
                    f"priority={new_task.priority}"
                )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos

                col = (mouse_x - OFFSET_X) // CELL_SIZE
                row = (mouse_y - OFFSET_Y) // CELL_SIZE

                if (
                    0 <= row < ROWS
                    and 0 <= col < COLS
                ):
                    robot = robots[selected_robot - 1]

                    # Do not interrupt an assigned task.
                    if robot.current_task is None:
                        robot.set_destination(row, col)


    # Update movement and task stages
    for robot in robots:
        robot.update()

    update_robot_tasks()


    # ==========================================
    # DRAW
    # ==========================================

    screen.fill((25, 25, 30))

    draw_warehouse()

    for task in tasks:
        if task.status != "COMPLETED":
            task.draw(screen, OFFSET_X, OFFSET_Y)

    for robot in robots:
        robot.draw(screen)


    # ==========================================
    # INFORMATION PANEL
    # ==========================================

    font = pygame.font.Font(None, 23)
    small_font = pygame.font.Font(None, 20)

    info_lines = [
        f"Selected Robot: R{selected_robot}",
        "1-5: Select | Mouse: Move idle robot",
        "A: Assign next task | T: Generate task",
        f"Waiting tasks: {len(task_queue.get_waiting_tasks())}",
        f"Completed tasks: {sum(t.status == 'COMPLETED' for t in tasks)}"
    ]

    for index, line in enumerate(info_lines):
        text = font.render(line, True, (240, 240, 240))
        screen.blit(text, (20, 18 + index * 27))

    info_y = 160

    for robot in robots:
        if robot.current_task is not None:
            status = (
                f"R{robot.robot_id}: T{robot.current_task.task_id} "
                f"| {robot.task_stage}"
            )
        else:
            status = f"R{robot.robot_id}: IDLE"

        text = small_font.render(status, True, (220, 220, 220))
        screen.blit(text, (20, info_y))
        info_y += 23

    pygame.display.flip()
    clock.tick(60)


pygame.quit()
sys.exit()

