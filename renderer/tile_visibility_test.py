import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ursina import *
from warehouse import ROWS, COLS, warehouse

app = Ursina()
window.title = "Warehouse - Actual Map 3D Test"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

# Display a small section of the REAL benchmark map.
MAP_ROWS = min(12, ROWS)
MAP_COLS = min(12, COLS)

tile_count = 0
wall_count = 0

for row in range(MAP_ROWS):
    for col in range(MAP_COLS):
        # Center the map around the origin so the camera can see it.
        x = col - MAP_COLS / 2
        z = row - MAP_ROWS / 2

        if warehouse[row][col] == 0:
            tile_color = color.rgb(70, 150, 90)
            tile_count += 1
        else:
            tile_color = color.rgb(220, 125, 55)
            wall_count += 1

        Entity(
            model="cube",
            position=(x, 0, z),
            scale=(0.95, 0.2, 0.95),
            color=tile_color
        )

# A blue 3D marker confirms the camera's view of the scene.
Entity(
    model="cube",
    position=(0, 1.0, 0),
    scale=(0.8, 1.8, 0.8),
    color=color.azure
)

Text(
    text="REAL WAREHOUSE MAP - 3D TEST",
    position=(-0.78, 0.44),
    scale=1.2,
    color=color.yellow
)

camera.position = (0, 11, -15)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("Actual benchmark map loaded.")
print("Map dimensions:", ROWS, "rows x", COLS, "columns")
print("Tiles created:", tile_count)
print("Obstacle cells:", wall_count)
print("Blue marker created at the map centre.")

app.run()
