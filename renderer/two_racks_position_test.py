from ursina import *

app = Ursina()
window.title = "Warehouse 3D - Rack Position Test"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

# Proven floor.
for r in range(6):
    for c in range(6):
        Entity(
            model="cube",
            position=(c * 1.5 - 3.75, 0, r * 1.5 - 3.75),
            scale=(1.3, 0.5, 1.3),
            color=color.green if (r + c) % 2 == 0 else color.rgb(30, 120, 70),
        )

# First rack.
Entity(
    model="cube",
    position=(0, 1.5, 0),
    scale=(1.5, 2.5, 1.5),
    color=color.orange,
)

# Second rack: moved toward the front-right of the scene.
Entity(
    model="cube",
    position=(2.0, 1.5, 2.5),
    scale=(1.0, 2.0, 1.0),
    color=color.rgb(220, 100, 35),
)

# Blue robot marker.
Entity(
    model="cube",
    position=(-4, 1, 0),
    scale=(0.8, 2, 0.8),
    color=color.azure,
)

camera.position = (0, 7, -11)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

app.run()
