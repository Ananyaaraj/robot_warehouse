import pygame
from warehouse import CELL_SIZE


class Task:
    def __init__(self, task_id, pickup, dropoff, priority=1):
        self.task_id = task_id
        self.pickup = pickup
        self.dropoff = dropoff
        self.priority = priority
        self.status = "WAITING"
        self.assigned_robot = None

    def assign_robot(self, robot_id):
        self.assigned_robot = robot_id
        self.status = "ASSIGNED"

    def complete(self):
        self.status = "COMPLETED"

    def draw(self, screen, offset_x, offset_y):
        pickup_row, pickup_col = self.pickup
        dropoff_row, dropoff_col = self.dropoff

        radius = max(3, CELL_SIZE // 2)

        # Draw pickup marker
        pickup_x = (
            offset_x + pickup_col * CELL_SIZE + CELL_SIZE // 2
        )
        pickup_y = (
            offset_y + pickup_row * CELL_SIZE + CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            (50, 220, 100),
            (pickup_x, pickup_y),
            radius
        )

        # Draw drop-off marker
        dropoff_x = (
            offset_x + dropoff_col * CELL_SIZE + CELL_SIZE // 2
        )
        dropoff_y = (
            offset_y + dropoff_row * CELL_SIZE + CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            (255, 80, 80),
            (dropoff_x, dropoff_y),
            radius
        )

        # Display labels when cells are large enough
        if CELL_SIZE >= 8:
            font = pygame.font.Font(None, 18)

            pickup_text = font.render(
                f"T{self.task_id} PICKUP",
                True,
                (50, 220, 100)
            )
            dropoff_text = font.render(
                f"T{self.task_id} DROP",
                True,
                (255, 80, 80)
            )

            screen.blit(
                pickup_text,
                (pickup_x + radius, pickup_y)
            )
            screen.blit(
                dropoff_text,
                (dropoff_x + radius, dropoff_y)
            )

    def __str__(self):
        return (
            f"Task {self.task_id}: "
            f"{self.pickup} -> {self.dropoff} "
            f"[{self.status}]"
        )
