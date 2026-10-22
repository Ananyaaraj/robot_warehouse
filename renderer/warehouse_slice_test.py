import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ursina import *
from warehouse import ROWS, COLS, warehouse

app = Ursina()
window.title = "Warehouse Scene Diagnostic"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(22, 30, 42)

# Render a small section of the REAL benchmark map.
CELL = 0.7
REGION_ROWS = min(20, ROWS)
REGION_COLS = min(20, COLS)

# Find a region with as many walkable cells as possible.
best_score = -1
start_row, start_col = 0, 0

for r in range(ROWS - REGION_ROWS + 1):
    for c in range(COLS - REGION_COLS + 1):
        score = sum(
            1 for rr in range(r, r + REGION_ROWS)
            for cc in range(c, c + REGION_COLS)
            if warehouse[rr][cc] == 0
        )
        if score > best_score:
            best_score = score
            start_row, start_col = r, c

print(
    f"Testing rows {start_row}-{start_row + REGION_ROWS - 1}, "
    f"columns {start_col}-{start_col + REGION_COLS - 1}"
)

W = REGION_COLS * CELL
D = REGION_ROWS * CELL
OX = -W / 2
OZ = -D / 2

# Large visible base
Entity(
    model="cube",
    name="Diagnostic floor",
    position=(0, -0.2, 0),
    scale=(W + 1, 0.3, D + 1),
    color=color.rgb(65, 78, 91)
)

walkable = 0
blocked = 0

for rr in range(REGION_ROWS):
    for cc in range(REGION_COLS):
        actual_row = start_row + rr
        actual_col = start_col + cc

        x = OX + (cc + 0.5) * CELL
        z = OZ + (rr + 0.5) * CELL

        if warehouse[actual_row][actual_col] == 0:
            walkable += 1
            Entity(
                model="cube",
                name="Walkable floor tile",
                position=(x, 0, z),
                scale=(CELL * 0.94, 0.06, CELL * 0.94),
                color=color.rgb(55, 180, 125)
            )
        else:
            blocked += 1
            Entity(
                model="cube",
                name="Raised obstacle",
                position=(x, 0.45, z),
                scale=(CELL * 0.9, 0.9, CELL * 0.9),
                color=color.rgb(240, 145, 55)
            )

# A bright reference object at the centre
Entity(
    model="cube",
    position=(0, 1.1, 0),
    scale=(0.8, 1.5, 0.8),
    color=color.rgb(70, 160, 255)
)

Text(
    text="WAREHOUSE MAP TEST",
    position=(-0.85, 0.44),
    scale=1.5,
    color=color.yellow
)

Text(
    text=f"Walkable: {walkable}   Obstacles: {blocked}",
    position=(-0.85, 0.39),
    scale=0.9,
    color=color.white
)

# Use the same known-working camera style as the cube test.
camera.position = (0, 17, -22)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60
camera.clip_plane_near = 0.1
camera.clip_plane_far = 200

print(f"Walkable cells: {walkable}; blocked cells: {blocked}")
print("Expected: green floor tiles, orange raised blocks, blue centre cube.")

app.run()
