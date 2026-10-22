import pygame
from warehouse import CELL_SIZE


class Task:
    """
    Delivery/transport task with lifecycle tracking, priority levels,
    and timing metrics.
    """

    def __init__(self, task_id, pickup, dropoff, priority=1, creation_step=0):
        self.task_id = task_id
        self.pickup = tuple(pickup)
        self.dropoff = tuple(dropoff)

        # Normalize priority (can be "HIGH", "MEDIUM", "LOW" or int 1..3)
        if isinstance(priority, str):
            p_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            self.priority_name = priority.upper()
            self.priority = p_map.get(self.priority_name, 1)
        else:
            self.priority = int(priority)
            p_rev = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}
            self.priority_name = p_rev.get(self.priority, "MEDIUM")

        self.status = "WAITING"  # WAITING, ASSIGNED, PICKED_UP, COMPLETED, CANCELLED
        self.assigned_robot = None

        # Timing and metric tracking
        self.creation_step = creation_step
        self.assignment_step = None
        self.pickup_step = None
        self.completion_step = None

    def assign_robot(self, robot_id, step=None):
        self.assigned_robot = robot_id
        self.status = "ASSIGNED"
        if step is not None:
            self.assignment_step = step

    def mark_picked_up(self, step=None):
        self.status = "PICKED_UP"
        if step is not None:
            self.pickup_step = step

    def complete(self, step=None):
        self.status = "COMPLETED"
        if step is not None:
            self.completion_step = step

    def cancel(self):
        self.status = "WAITING"
        self.assigned_robot = None

    @property
    def total_duration(self):
        if self.completion_step is not None and self.creation_step is not None:
            return self.completion_step - self.creation_step
        return None

    @property
    def wait_time(self):
        if self.assignment_step is not None and self.creation_step is not None:
            return self.assignment_step - self.creation_step
        return None

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
            f"Task {self.task_id} [{self.priority_name}]: "
            f"{self.pickup} -> {self.dropoff} "
            f"[{self.status}]"
        )
