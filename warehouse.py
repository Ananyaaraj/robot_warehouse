
# ==========================================
# WAREHOUSE SETTINGS
# ==========================================

from benchmark_loader import MAP_FILE, load_map


# ==========================================
# LOAD BENCHMARK MAP
# ==========================================

benchmark = load_map(MAP_FILE)

# The benchmark loader uses (x, y).
# Our existing simulation uses (row, col).

ROWS = benchmark.height
COLS = benchmark.width

# Temporary display size.
# We will adjust the Pygame layout in the next step.
CELL_SIZE = 5


# ==========================================
# CONVERT MAP TO EXISTING FORMAT
# ==========================================

# 0 = FREE
# 1 = OBSTACLE

warehouse = [
    [
        0 if benchmark.grid[row][col] else 1
        for col in range(COLS)
    ]
    for row in range(ROWS)
]


# ==========================================
# VALIDATE ROBOT POSITIONS
# ==========================================

def is_valid_cell(row, col):
    """Return True if the cell is inside the map and walkable."""

    if not (0 <= row < ROWS and 0 <= col < COLS):
        return False

    return warehouse[row][col] == 0
