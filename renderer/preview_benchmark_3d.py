import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import warehouse as warehouse_data
from ursina import *

app = Ursina()
window.title = "Warehouse 3D - Real Obstacles"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

SIZE = 6
TILE = 1.5
grid = warehouse_data.warehouse

# Find the 6x6 area with the most obstacles.
best_row = 0
best_col = 0
best_obstacles = -1

for start_r in range(warehouse_data.ROWS - SIZE + 1):
    for start_c in range(warehouse_data.COLS - SIZE + 1):
        count = sum(
            grid[r][c] == 1
            for r in range(start_r, start_r + SIZE)
            for c in range(start_c, start_c + SIZE)
        )
        if count > best_obstacles:
            best_obstacles = count
            best_row = start_r
            best_col = start_c

floor_count = 0
obstacle_count = 0

for r in range(SIZE):
    for c in range(SIZE):
        value = grid[best_row + r][best_col + c]

        if value == 1:
            tile_color = color.rgb(235, 115, 40)
            obstacle_count += 1
        else:
            tile_color = (
                color.rgb(50, 190, 100)
                if (r + c) % 2 == 0
                else color.rgb(30, 120, 70)
            )
            floor_count += 1

        Entity(
            model="cube",
            position=(
                c * TILE - (SIZE - 1) * TILE / 2,
                0,
                r * TILE - (SIZE - 1) * TILE / 2,
            ),
            scale=(1.3, 0.5, 1.3),
            color=tile_color,
        )

Entity(
    model="cube",
    position=(-4, 1, 0),
    scale=(0.8, 2, 0.8),
    color=color.azure,
)

# Preserve the camera from the working preview.
camera.position = (0, 7, -11)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("Full benchmark:", warehouse_data.ROWS, "x", warehouse_data.COLS)
print("Selected map origin (row, col):", best_row, best_col)
print("Displayed area:", SIZE, "x", SIZE)
print("Walkable tiles:", floor_count)
print("Obstacle tiles:", obstacle_count)

app.run()
