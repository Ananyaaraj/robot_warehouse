import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import warehouse as warehouse_data
from ursina import *

app = Ursina()
window.title = "Warehouse 3D - Visibility Diagnostic"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

SIZE = 6
TILE = 1.5
grid = warehouse_data.warehouse

# Use the same known-working grid coordinates and camera.
tiles = []

for r in range(SIZE):
    for c in range(SIZE):
        value = grid[r + 1][c + 1]

        tile = Entity(
            model="cube",
            position=(
                c * TILE - (SIZE - 1) * TILE / 2,
                0,
                r * TILE - (SIZE - 1) * TILE / 2,
            ),
            scale=(1.3, 0.5, 1.3),
            color=color.green if value == 0 else color.orange,
        )
        tiles.append(tile)

marker = Entity(
    model="cube",
    position=(-4, 1, 0),
    scale=(0.8, 2, 0.8),
    color=color.azure,
)

camera.position = (0, 7, -11)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("Tile count:", len(tiles))
print("First tile position:", tiles[0].position)
print("Last tile position:", tiles[-1].position)
print("First tile enabled:", tiles[0].enabled)
print("First tile visible:", tiles[0].visible)
print("Marker enabled:", marker.enabled)
print("Camera position:", camera.position)
print("Map values in selected area:")
for r in range(1, SIZE + 1):
    print("".join("#" if grid[r][c] == 1 else "." for c in range(1, SIZE + 1)))

app.run()
