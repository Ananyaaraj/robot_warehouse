import pygame
from warehouse import ROWS, COLS, CELL_SIZE, warehouse
from pathfinding import a_star


class Robot:
    """
    Mobile warehouse robot model with battery accounting, heading,
    path tracking, and status metrics.
    """

    def __init__(self, row, col, robot_id, offset_x=0, offset_y=0, max_battery=100.0):
        self.row = row
        self.col = col
        self.robot_id = robot_id
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.path = []
        self.move_timer = 0
        self.current_task = None
        self.task_stage = "IDLE"  # IDLE, GOING_TO_PICKUP, GOING_TO_DROPOFF, CHARGING, FAULT

        # Enhanced dynamics & status
        self.heading = 0  # 0: East, 1: South, 2: West, 3: North
        self.heading_degrees = 90.0  # Facing East in standard Godot degrees
        self.battery = float(max_battery)
        self.max_battery = float(max_battery)
        self.is_faulty = False
        self.is_charging = False
        self.blocked_steps = 0
        self.total_distance = 0
        self.total_wait_time = 0

        self.battery_drain_per_move = 0.08
        self.battery_drain_idle = 0.01
        self.charge_rate = 1.5

        # Performance & historical metrics
        self.tasks_completed = 0
        self.total_mission_steps = 0
        self.efficiency_score = 100.0

    def set_destination(self, row, col, blocked_positions=None):
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return False

        if warehouse[row][col] != 0:
            return False

        start = (self.row, self.col)
        goal = (row, col)

        self.path = a_star(start, goal, blocked_positions=blocked_positions)

        if not self.path:
            self.path = []
            return False

        return True

    def update_heading_from_step(self, next_row, next_col):
        """Update robot heading based on movement vector."""
        dr = next_row - self.row
        dc = next_col - self.col
        if dr > 0:
            self.heading = 1  # South
            self.heading_degrees = 180.0
        elif dr < 0:
            self.heading = 3  # North
            self.heading_degrees = 0.0
        elif dc > 0:
            self.heading = 0  # East
            self.heading_degrees = 90.0
        elif dc < 0:
            self.heading = 2  # West
            self.heading_degrees = 270.0

    def drain_move(self):
        self.battery = max(0.0, self.battery - self.battery_drain_per_move)
        self.total_distance += 1
        if self.battery <= 0.0:
            self.is_faulty = True
            self.task_stage = "FAULT"

    def drain_idle(self):
        self.battery = max(0.0, self.battery - self.battery_drain_idle)
        self.total_wait_time += 1
        if self.battery <= 0.0:
            self.is_faulty = True
            self.task_stage = "FAULT"

    def charge(self, amount=None):
        rate = amount if amount is not None else self.charge_rate
        self.battery = min(self.max_battery, self.battery + rate)
        self.is_charging = True
        if self.battery >= self.max_battery * 0.98:
            self.is_charging = False

    def inject_fault(self):
        self.is_faulty = True
        self.task_stage = "FAULT"

    def recover_fault(self):
        self.is_faulty = False
        if self.battery <= 0.0:
            self.battery = 20.0  # Emergency minimum charge to reach dock
        self.task_stage = "IDLE"

    def update(self):
        """Standard step for Pygame mode."""
        if not self.path:
            self.drain_idle()
            return

        if self.is_faulty:
            return

        self.move_timer += 1

        if self.move_timer >= 10:
            self.move_timer = 0

            # Remove current position if it is the first path cell
            if self.path and self.path[0] == (self.row, self.col):
                self.path.pop(0)

            if self.path:
                next_row, next_col = self.path.pop(0)
                self.update_heading_from_step(next_row, next_col)
                self.row = next_row
                self.col = next_col
                self.drain_move()

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

        # Body color based on status
        if self.is_faulty:
            body_color = (255, 60, 60)  # Red for fault
        elif self.is_charging:
            body_color = (255, 215, 0)  # Yellow for charging
        elif self.battery < 25.0:
            body_color = (255, 140, 0)  # Orange for low battery
        elif self.current_task is not None:
            body_color = (50, 200, 255)  # Cyan for active delivery
        else:
            body_color = (50, 150, 255)  # Blue for idle

        # Main robot body
        pygame.draw.circle(
            screen,
            body_color,
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