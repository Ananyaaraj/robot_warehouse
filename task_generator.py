import random

from task import Task

from warehouse import (
    ROWS,
    COLS,
    warehouse
)


class TaskGenerator:

    def __init__(self, start_id=1):

        self.task_counter = start_id

    # ==========================================
    # GET RANDOM FREE CELL
    # ==========================================

    def get_random_free_cell(self):

        while True:

            row = random.randint(0, ROWS - 1)
            col = random.randint(0, COLS - 1)

            if warehouse[row][col] == 0:

                return (row, col)

    # ==========================================
    # GENERATE TASK
    # ==========================================

    def generate_task(self):

        task_id = self.task_counter

        self.task_counter += 1

        pickup = self.get_random_free_cell()

        dropoff = self.get_random_free_cell()

        # Make sure pickup and drop-off are different
        while dropoff == pickup:

            dropoff = self.get_random_free_cell()

        priority = random.choice(
            ["LOW", "MEDIUM", "HIGH"]
        )

        return Task(
            task_id,
            pickup,
            dropoff,
            priority
        )