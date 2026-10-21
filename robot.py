import pygame
from warehouse import ROWS, COLS, CELL_SIZE, warehouse
from pathfinding import a_star


class Robot:
    def __init__(self, row, col, robot_id, offset_x, offset_y):
        self.row = row
        self.col = col
        self.robot_id = robot_id
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.path = []
        self.move_timer = 0
        self.current_task = None
        self.task_stage = "IDLE"

    def set_destination(self, row, col):
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return False

        if warehouse[row][col] != 0:
            return False

        start = (self.row, self.col)
        goal = (row, col)

        self.path = a_star(start, goal)

        if self.path is None:
            self.path = []
            return False

        return True

    def update(self):
        if not self.path:
            return

        self.move_timer += 1

        if self.move_timer >= 10:
            self.move_timer = 0

            # Remove the current position if it is the first path cell.
            if self.path and self.path[0] == (self.row, self.col):
                self.path.pop(0)

            if self.path:
                next_row, next_col = self.path.pop(0)

                self.row = next_row
                self.col = next_col

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

        radius = max(3, CELL_SIZE // 2)
        center_radius = max(1, radius // 2)

        # Main robot body
        pygame.draw.circle(
            screen,
            (50, 150, 255),
            (x, y),
            radius
        )

        # White center
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (x, y),
            center_radius
        )

        # Robot label
        if CELL_SIZE >= 5:
            font = pygame.font.Font(None, 18)
            label = font.render(
                f"R{self.robot_id}",
                True,
                (255, 255, 255)
            )
            screen.blit(label, (x + radius, y - radius))