import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ursina import *
from warehouse import ROWS, COLS, warehouse

app = Ursina()
window.title = "Warehouse Rendering Test"
window.color = color.rgb(20, 25, 40)

# Use a small section of the real benchmark map.
SIZE = 10
CELL = 0.5
start_row, start_col = 1, 1

# Create a large, unmistakable red cube like the working test.
Entity(
    model="cube",
    position=(0, 1, 0),
    scale=(1, 1, 1),
    color=color.red
)

# Create a simple 10x10 floor around the red cube.
for r in range(SIZE):
    for c in range(SIZE):
        actual_row = start_row + r
        actual_col = start_col + c

        x = (c - SIZE / 2) * CELL
        z = (r - SIZE / 2) * CELL

        if warehouse[actual_row][actual_col] == 0:
            tint = color.rgb(50, 210, 100)
        else:
            tint = color.rgb(245, 145, 40)

        Entity(
            model="cube",
            position=(x, -0.1, z),
            scale=(CELL * 0.95, 0.15, CELL * 0.95),
            color=tint
        )

Text(
    text="10x10 WAREHOUSE TEST",
    position=(-0.85, 0.42),
    scale=1.5,
    color=color.yellow
)

# Same general camera setup as the successful cube test.
camera.position = (0, 5, -10)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("Expected: a red cube surrounded by green and orange tiles.")
app.run()
