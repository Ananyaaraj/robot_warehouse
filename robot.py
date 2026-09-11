import pygame

from warehouse import (
    ROWS,
    COLS,
    CELL_SIZE,
    warehouse
)

from pathfinding import a_star


class Robot:

    def __init__(self, row, col, robot_id, offset_x, offset_y):

        self.row = row
        self.col = col

        self.robot_id = robot_id

        self.path = []

        self.move_timer = 0

        # ==========================================
        # TASK INFORMATION
        # ==========================================

        self.current_task = None

        self.task_stage = "IDLE"

        # Screen offset
        self.offset_x = offset_x
        self.offset_y = offset_y

    # ==========================================
    # DRAW ROBOT
    # ==========================================

    def draw(self, screen):

        x = (
            self.offset_x
            + self.col * CELL_SIZE
            + CELL_SIZE // 2
        )

        y = (
            self.offset_y
            + self.row * CELL_SIZE
            + CELL_SIZE // 2
        )

        # Robot body
        pygame.draw.circle(
            screen,
            (50, 150, 255),
            (x, y),
            18
        )

        # Robot center
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (x, y),
            6
        )

        # Robot label
        font = pygame.font.Font(None, 22)

        text = font.render(
            f"R{self.robot_id}",
            True,
            (255, 255, 255)
        )

        screen.blit(
            text,
            (x - 10, y + 22)
        )

    # ==========================================
    # SET DESTINATION
    # ==========================================

    def set_destination(self, row, col):

        if row < 0 or row >= ROWS:
            return

        if col < 0 or col >= COLS:
            return

        if warehouse[row][col] == 1:
            return

        start = (self.row, self.col)
        goal = (row, col)

        self.path = a_star(start, goal)

        self.move_timer = 0

    # ==========================================
    # UPDATE ROBOT MOVEMENT
    # ==========================================

    def update(self):

        if not self.path:
            return

        self.move_timer += 1

        if self.move_timer >= 10:

            self.move_timer = 0

            # Remove current position
            self.path.pop(0)

            if self.path:

                next_position = self.path[0]

                self.row = next_position[0]
                self.col = next_position[1]