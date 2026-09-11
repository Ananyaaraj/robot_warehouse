import pygame
import sys

from warehouse import (
    ROWS,
    COLS,
    CELL_SIZE,
    warehouse
)

from robot import Robot

from task import Task

from task_generator import TaskGenerator

from task_queue import TaskQueue


# ==========================================
# INITIALIZE PYGAME
# ==========================================

pygame.init()


# ==========================================
# WINDOW
# ==========================================

WIDTH = 1000
HEIGHT = 700

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Multi-Robot Warehouse"
)

clock = pygame.time.Clock()


# ==========================================
# WAREHOUSE SIZE
# ==========================================

GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE

OFFSET_X = (
    WIDTH - GRID_WIDTH
) // 2

OFFSET_Y = (
    HEIGHT - GRID_HEIGHT
) // 2


# ==========================================
# CREATE 5 ROBOTS
# ==========================================

robots = [

    Robot(
        0,
        0,
        1,
        OFFSET_X,
        OFFSET_Y
    ),

    Robot(
        0,
        13,
        2,
        OFFSET_X,
        OFFSET_Y
    ),

    Robot(
        4,
        2,
        3,
        OFFSET_X,
        OFFSET_Y
    ),

    Robot(
        6,
        10,
        4,
        OFFSET_X,
        OFFSET_Y
    ),

    Robot(
        9,
        7,
        5,
        OFFSET_X,
        OFFSET_Y
    )
]


# ==========================================
# CREATE INITIAL TASKS
# ==========================================

tasks = [

    Task(
        1,
        (2, 4),
        (7, 12),
        "HIGH"
    ),

    Task(
        2,
        (6, 1),
        (3, 10),
        "MEDIUM"
    ),

    Task(
        3,
        (7, 8),
        (1, 10),
        "LOW"
    )
]


# ==========================================
# TASK GENERATOR
# ==========================================

task_generator = TaskGenerator(
    start_id=len(tasks) + 1
)

# ==========================================
# TASK QUEUE
# ==========================================

task_queue = TaskQueue()


# Add initial tasks to queue
for task in tasks:

    task_queue.add_task(task)


# ==========================================
# SELECTED ROBOT
# ==========================================

selected_robot = 1


# ==========================================
# FIND DISTANCE BETWEEN ROBOT AND TASK
# ==========================================

def calculate_distance(robot, location):

    robot_position = (
        robot.row,
        robot.col
    )

    task_position = location

    return (
        abs(robot_position[0] - task_position[0])
        + abs(robot_position[1] - task_position[1])
    )


# ==========================================
# FIND NEAREST AVAILABLE ROBOT
# ==========================================

def find_nearest_available_robot(task):

    available_robots = []

    for robot in robots:

        # Robot is available if it has no task
        if robot.current_task is None:

            distance = calculate_distance(
                robot,
                task.pickup
            )

            available_robots.append(
                (distance, robot)
            )

    if not available_robots:

        return None

    # Sort by distance
    available_robots.sort(
        key=lambda item: item[0]
    )

    return available_robots[0][1]


# ==========================================
# ASSIGN TASK TO ROBOT
# ==========================================

def assign_task(task):

    robot = find_nearest_available_robot(task)

    if robot is None:

        print(
            "No available robot for this task."
        )

        return False

    # Assign task to robot
    robot.current_task = task

    robot.task_stage = "GOING_TO_PICKUP"

    task.assign_robot(
        robot.robot_id
    )

    # Move robot to pickup location
    pickup_row, pickup_col = task.pickup

    robot.set_destination(
        pickup_row,
        pickup_col
    )

    print(
        f"Task T{task.task_id} "
        f"assigned to Robot R{robot.robot_id}"
    )

    print(
        f"Robot R{robot.robot_id} "
        f"is going to pickup location "
        f"{task.pickup}"
    )

    return True


# ==========================================
# ASSIGN NEXT TASK
# ==========================================

def assign_next_task():

    task = task_queue.get_next_task()

    if task is None:

        print("No waiting tasks.")

        return

    success = assign_task(task)

    if success:

        print(
            f"Priority: {task.priority}"
        )


# ==========================================
# DRAW WAREHOUSE
# ==========================================

def draw_warehouse():

    for row in range(ROWS):

        for col in range(COLS):

            x = (
                OFFSET_X
                + col * CELL_SIZE
            )

            y = (
                OFFSET_Y
                + row * CELL_SIZE
            )

            # Obstacle
            if warehouse[row][col] == 1:

                pygame.draw.rect(
                    screen,
                    (120, 120, 120),
                    (
                        x,
                        y,
                        CELL_SIZE,
                        CELL_SIZE
                    )
                )

            # Grid lines
            pygame.draw.rect(
                screen,
                (80, 80, 80),
                (
                    x,
                    y,
                    CELL_SIZE,
                    CELL_SIZE
                ),
                1
            )


# ==========================================
# MAIN LOOP
# ==========================================

running = True

while running:

    # ======================================
    # EVENTS
    # ======================================

    for event in pygame.event.get():

        # ==================================
        # CLOSE WINDOW
        # ==================================

        if event.type == pygame.QUIT:

            running = False


        # ==================================
        # KEYBOARD
        # ==================================

        if event.type == pygame.KEYDOWN:

            # ------------------------------
            # SELECT ROBOT
            # ------------------------------

            if event.key == pygame.K_1:

                selected_robot = 1

            elif event.key == pygame.K_2:

                selected_robot = 2

            elif event.key == pygame.K_3:

                selected_robot = 3

            elif event.key == pygame.K_4:

                selected_robot = 4

            elif event.key == pygame.K_5:

                selected_robot = 5


            # ------------------------------
            # ASSIGN NEXT TASK
            # ------------------------------

            elif event.key == pygame.K_a:

                assign_next_task()


            # ------------------------------
            # GENERATE NEW TASK
            # ------------------------------

            elif event.key == pygame.K_t:

                new_task = task_generator.generate_task()

                tasks.append(new_task)

                task_queue.add_task(new_task)

                print(
                    f"New Task T{new_task.task_id} generated"
                )

                print(
                    f"Pickup: {new_task.pickup}"
                )

                print(
                    f"Dropoff: {new_task.dropoff}"
                )

                print(
                    f"Priority: {new_task.priority}"
                )


        # ==================================
        # MOUSE
        # ==================================

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                mouse_x, mouse_y = (
                    pygame.mouse.get_pos()
                )

                col = (
                    mouse_x - OFFSET_X
                ) // CELL_SIZE

                row = (
                    mouse_y - OFFSET_Y
                ) // CELL_SIZE

                # Move selected robot manually
                robots[
                    selected_robot - 1
                ].set_destination(
                    row,
                    col
                )


    # ======================================
    # UPDATE ROBOTS
    # ======================================

    for robot in robots:

        robot.update()


    # ======================================
    # DRAW
    # ======================================

    screen.fill(
        (30, 30, 30)
    )


    # Warehouse
    draw_warehouse()


    # ======================================
    # DRAW TASKS
    # ======================================

    for task in tasks:

        task.draw(
            screen,
            OFFSET_X,
            OFFSET_Y
        )


    # ======================================
    # DRAW ROBOTS
    # ======================================

    for robot in robots:

        robot.draw(screen)


    # ======================================
    # INFORMATION PANEL
    # ======================================

    font = pygame.font.Font(
        None,
        25
    )


    # Selected robot
    selected_text = font.render(
        f"Selected Robot: R{selected_robot}",
        True,
        (255, 255, 255)
    )

    screen.blit(
        selected_text,
        (20, 20)
    )


    # Instructions
    instruction_text = font.render(
        "1-5: Select Robot | "
        "Mouse: Move | "
        "A: Assign Task | "
        "T: Generate Task",
        True,
        (255, 255, 255)
    )

    screen.blit(
        instruction_text,
        (20, 50)
    )


    # ======================================
    # TASK QUEUE INFORMATION
    # ======================================

    queue_text = font.render(
        f"Tasks in Queue: {len(task_queue)}",
        True,
        (255, 255, 255)
    )

    screen.blit(
        queue_text,
        (20, 85)
    )


    # ======================================
    # ROBOT TASK INFORMATION
    # ======================================

    info_y = 120

    small_font = pygame.font.Font(
        None,
        22
    )

    for robot in robots:

        if robot.current_task is not None:

            task_info = (
                f"R{robot.robot_id}: "
                f"T{robot.current_task.task_id} | "
                f"{robot.task_stage}"
            )

        else:

            task_info = (
                f"R{robot.robot_id}: IDLE"
            )

        robot_text = small_font.render(
            task_info,
            True,
            (255, 255, 255)
        )

        screen.blit(
            robot_text,
            (20, info_y)
        )

        info_y += 25


    # ======================================
    # UPDATE SCREEN
    # ======================================

    pygame.display.flip()

    clock.tick(60)


# ==========================================
# EXIT
# ==========================================

pygame.quit()

sys.exit()