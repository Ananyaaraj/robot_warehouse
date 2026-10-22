from ursina import *

app = Ursina()
window.title = "Multi-Robot Warehouse - 3D Stage 2"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

SIZE = 6
TILE = 1.5
HALF = (SIZE - 1) * TILE / 2

# 1. Warehouse floor
for r in range(SIZE):
    for c in range(SIZE):
        Entity(
            model="cube",
            position=(c * TILE - HALF, -0.3, r * TILE - HALF),
            scale=(1.3, 0.5, 1.3),
            color=(
                color.rgb(50, 190, 100)
                if (r + c) % 2 == 0
                else color.rgb(30, 120, 70)
            ),
        )

# 2. Two storage racks, each with two shelves.
for rack_x in (-1.5, 1.5):
    for level in range(2):
        Entity(
            model="cube",
            position=(rack_x, 0.75 + level * 1.1, 0),
            scale=(1.1, 0.16, 2.7),
            color=color.rgb(235, 130, 45),
        )

    # Vertical rack supports
    for z in (-1.25, 1.25):
        Entity(
            model="cube",
            position=(rack_x, 1.05, z),
            scale=(0.14, 2.2, 0.14),
            color=color.rgb(190, 90, 30),
        )

    # Storage boxes on the shelves
    for level in range(2):
        Entity(
            model="cube",
            position=(rack_x, 0.95 + level * 1.1, -0.55),
            scale=(0.65, 0.55, 0.65),
            color=color.rgb(190, 145, 95),
        )
        Entity(
            model="cube",
            position=(rack_x, 0.95 + level * 1.1, 0.45),
            scale=(0.65, 0.55, 0.65),
            color=color.rgb(150, 110, 75),
        )

# 3. Blue robot placeholder with a raised sensor.
Entity(
    model="cube",
    position=(0, 0.35, -3.5),
    scale=(0.75, 0.7, 0.75),
    color=color.azure,
)
Entity(
    model="cube",
    position=(0, 0.85, -3.5),
    scale=(0.18, 0.35, 0.18),
    color=color.white,
)

# 4. Lighting
DirectionalLight(rotation=(45, -45, 45), color=color.white)
AmbientLight(color=color.rgba(120, 120, 120, 255))

# 5. Camera
camera.position = (0, 7, -11)
camera.look_at(Vec3(0, 0.5, 0))
camera.fov = 60

print("Stage 2 loaded.")
print("Floor tiles:", SIZE * SIZE)
print("Storage racks: 2")
print("Shelf levels per rack: 2")
print("Robot markers: 1")

app.run()
