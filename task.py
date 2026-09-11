import pygame

from warehouse import CELL_SIZE


class Task:

    def __init__(
        self,
        task_id,
        pickup,
        dropoff,
        priority
    ):

        self.task_id = task_id

        self.pickup = pickup
        self.dropoff = dropoff

        # LOW / MEDIUM / HIGH
        self.priority = priority

        self.status = "WAITING"

        self.assigned_robot = None

    # ==========================================
    # ASSIGN ROBOT
    # ==========================================

    def assign_robot(self, robot_id):

        self.assigned_robot = robot_id
        self.status = "ASSIGNED"

    # ==========================================
    # COMPLETE TASK
    # ==========================================

    def complete(self):

        self.status = "COMPLETED"

    # ==========================================
    # DRAW TASK
    # ==========================================

    def draw(self, screen, offset_x, offset_y):

        font = pygame.font.Font(None, 22)

        # ======================================
        # PICKUP
        # ======================================

        pickup_row, pickup_col = self.pickup

        pickup_x = (
            offset_x
            + pickup_col * CELL_SIZE
            + CELL_SIZE // 2
        )

        pickup_y = (
            offset_y
            + pickup_row * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            (0, 255, 0),
            (pickup_x, pickup_y),
            14
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (pickup_x, pickup_y),
            5
        )

        pickup_text = font.render(
            f"T{self.task_id} PICKUP",
            True,
            (0, 255, 0)
        )

        screen.blit(
            pickup_text,
            (pickup_x + 15, pickup_y - 25)
        )

        # ======================================
        # DROP-OFF
        # ======================================

        drop_row, drop_col = self.dropoff

        drop_x = (
            offset_x
            + drop_col * CELL_SIZE
            + CELL_SIZE // 2
        )

        drop_y = (
            offset_y
            + drop_row * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            (255, 50, 50),
            (drop_x, drop_y),
            14
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (drop_x, drop_y),
            5
        )

        drop_text = font.render(
            f"T{self.task_id} DROP",
            True,
            (255, 80, 80)
        )

        screen.blit(
            drop_text,
            (drop_x + 15, drop_y - 25)
        )

    # ==========================================
    # STRING REPRESENTATION
    # ==========================================

    def __str__(self):

        return (
            f"Task {self.task_id} | "
            f"Pickup: {self.pickup} | "
            f"Dropoff: {self.dropoff} | "
            f"Priority: {self.priority} | "
            f"Status: {self.status}"
        )