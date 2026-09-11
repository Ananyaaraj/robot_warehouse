class TaskQueue:

    def __init__(self):

        self.tasks = []

    # ==========================================
    # ADD TASK
    # ==========================================

    def add_task(self, task):

        self.tasks.append(task)

    # ==========================================
    # REMOVE TASK
    # ==========================================

    def remove_task(self, task):

        if task in self.tasks:

            self.tasks.remove(task)

    # ==========================================
    # WAITING TASKS
    # ==========================================

    def get_waiting_tasks(self):

        return [
            task
            for task in self.tasks
            if task.status == "WAITING"
        ]

    # ==========================================
    # PRIORITY ORDER
    # ==========================================

    def get_tasks_by_priority(self):

        priority_value = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }

        waiting_tasks = self.get_waiting_tasks()

        return sorted(
            waiting_tasks,
            key=lambda task: priority_value[task.priority],
            reverse=True
        )

    # ==========================================
    # GET NEXT TASK
    # ==========================================

    def get_next_task(self):

        sorted_tasks = self.get_tasks_by_priority()

        if sorted_tasks:

            return sorted_tasks[0]

        return None

    # ==========================================
    # QUEUE LENGTH
    # ==========================================

    def __len__(self):

        return len(self.tasks)