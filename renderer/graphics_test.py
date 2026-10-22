from ursina import *

app = Ursina()
window.title = "Ursina Graphics Test"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(20, 25, 40)

# A large, bright cube should be immediately visible.
cube = Entity(
    model="cube",
    color=color.red,
    scale=3,
    position=(0, 0, 0)
)

# Add a second object so the test has visible depth.
Entity(
    model="cube",
    color=color.azure,
    scale=1,
    position=(3, 0, 0)
)

Text(
    text="3D GRAPHICS TEST",
    position=(-0.85, 0.42),
    scale=1.5,
    color=color.yellow
)

camera.position = (0, 3, -12)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 60

print("If rendering works, you should see red and blue cubes.")
app.run()
