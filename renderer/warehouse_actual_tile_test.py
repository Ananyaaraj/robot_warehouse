import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ursina import *
from warehouse import warehouse

app = Ursina()
window.title = "Warehouse Tile Debug"
window.color = color.rgb(20, 25, 40)

# Known working reference position
Entity(
    model="cube",
    position=(-12, 1.5, -11),
    scale=(1, 3, 1),
    color=color.azure,
)

# Three tiles derived from actual warehouse cells
for i in range(3):
    value = warehouse[2][i + 1]
    tile_color = color.green if value == 0 else color.orange

    tile = Entity(
        model="cube",
        position=(-11 + i, 0, -11),
        scale=(0.9, 0.5, 0.9),
        color=tile_color,
    )

    print(
        "Cell:", (2, i + 1),
        "value:", value,
        "position:", tile.position,
        "enabled:", tile.enabled,
    )

camera.position = (-12, 8, -20)
camera.look_at(Vec3(-12, 0, -11))
camera.fov = 60

app.run()
