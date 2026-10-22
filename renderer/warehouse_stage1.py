from ursina import *

app = Ursina()
window.title = "Multi-Robot Warehouse - 3D Prototype"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

SIZE = 6
TILE = 1.5

# Warehouse floor: preserve the proven grid layout.
for r in range(SIZE):
    for c in range(SIZE):
        tile_color = (
            color.rgb(50, 190, 100)
            if (r + c) % 2 == 0
            else color.rgb(30, 120, 70)
        )

        Entity(
            model="cube",
            position=(
                c * TILE - (SIZE - 1) * TILE / 2,
                -0.3,
                r * TILE - (SIZE - 1) * TILE / 2,
            ),
            scale=(1.3, 0.5, 1.3),
            color=tile_color,
        )

# Build two raised storage racks from 3D blocks.
for rack_x in (-1.5, 1.5):
    for level in range(2):
        Entity(
            model="cube",
            position=(rack_x, 0.8 + level * 1.2, 0),
            scale=(1.0, 0.9, 2.8),
            color=color.rgb(225, 115, 40),
        )

    # Upright supports.
    for z in (-1.2, 1.2):
        Entity(
            model="cube",
            position=(rack_x, 1.1, z),
            scale=(0.12, 2.6, 0.12),
            color=color.rgb(190, 95, 35),
        )

# Blue robot placeholder.
Entity(
    model="cube",
    position=(0, 0.45, -3.5),
    scale=(0.8, 0.9, 0.8),
    color=color.azure,
)

# Lighting for depth and 3D appearance.
DirectionalLight(
    rotation=(45, -45, 45),
    color=color.white,
)
AmbientLight(color=color.rgba(120, 120, 120, 255))

# Keep the camera settings close to the working preview.
camera.position = (0, 9, -14)
camera.look_at(Vec3(0, 0.5, 0))
camera.fov = 60

print("3D warehouse prototype loaded.")
print("Floor tiles:", SIZE * SIZE)
print("Storage racks: 2")
print("Robot markers: 1")

app.run()
