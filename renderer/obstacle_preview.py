import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import warehouse as warehouse_data
from ursina import *

SIZE = 6
TILE = 1.5
map_cells = warehouse_data.warehouse

# Find a 6x6 area with the greatest number of obstacles.
best_row, best_col, best_count = 0, 0, -1

for sr in range(warehouse_data.ROWS - SIZE + 1):
    for sc in range(warehouse_data.COLS - SIZE + 1):
        count = sum(
            map_cells[r][c] == 1
            for r in range(sr, sr + SIZE)
            for c in range(sc, sc + SIZE)
        )
        if count > best_count:
            best_row, best_col, best_count = sr, sc, count

app = Ursina()
window.title = "Warehouse 3D - Obstacle Section"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

floor_count = 0
obstacle_count = 0

for r in range(SIZE):
    for c in range(SIZE):
        value = map_cells[best_row + r][best_col + c]

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

camera.position = (0, 7, -11)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("Selected benchmark origin:", best_row, best_col)
print("Walkable tiles:", floor_count)
print("Obstacle tiles:", obstacle_count)
print("Total tiles:", floor_count + obstacle_count)

app.run()
