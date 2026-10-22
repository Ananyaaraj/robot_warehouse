import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ursina import *

app = Ursina()
window.title = "Warehouse Tile Position Test"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

# Three large cubes at the same coordinate scale as the warehouse preview.
tile_size = 1.0
origin_x = -14.0
origin_z = -11.0

for i, tile_color in enumerate([color.green, color.orange, color.azure]):
    x = origin_x + i * tile_size
    z = origin_z
    tile = Entity(
        model="cube",
        position=(x, 0, z),
        scale=(0.96, 0.12, 0.96),
        color=tile_color,
    )
    print(
        "Tile", i,
        "position:", tile.position,
        "scale:", tile.scale,
        "enabled:", tile.enabled
    )

# Put a large upright cube beside the tiles as a reference.
Entity(
    model="cube",
    position=(-11, 1, -11),
    scale=(1, 2, 1),
    color=color.red,
)

camera.position = (-12, 8, -20)
camera.look_at(Vec3(-12, 0, -11))
camera.fov = 60

print("Tile position test started.")
app.run()
