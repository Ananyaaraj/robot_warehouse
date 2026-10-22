import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the existing simulation module, but do not use its map.
from warehouse import ROWS, COLS, warehouse

from ursina import *

app = Ursina()
window.title = "Warehouse 3D - Import Isolation Test"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

SIZE = 6
TILE = 1.5

for r in range(SIZE):
    for c in range(SIZE):
        tile_color = (
            color.green if (r + c) % 2 == 0
            else color.orange
        )

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

print("Warehouse import successful.")
print("Benchmark dimensions:", ROWS, "x", COLS)
print("Static test grid: 36 tiles")
app.run()
