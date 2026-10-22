import sys
from pathlib import Path

# Add the project root so the preview can import existing modules.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from warehouse import ROWS, COLS, warehouse
from renderer.iso_view import IsometricView


pygame.init()

WIDTH = 1400
HEIGHT = 900

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Isometric Warehouse Preview")
clock = pygame.time.Clock()

tile_width = 12
tile_height = 6

view = IsometricView(
    tile_width=tile_width,
    tile_height=tile_height,
    origin_x=WIDTH // 2,
    origin_y=45
)

background = (25, 30, 37)
floor_color = (105, 116, 124)
obstacle_color = (63, 72, 82)
grid_color = (85, 95, 103)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(background)

    # Draw the warehouse from back to front.
    for row in range(ROWS):
        for col in range(COLS):
            x, y = view.grid_to_screen(row, col)

            color = (
                floor_color
                if warehouse[row][col] == 0
                else obstacle_color
            )

            points = [
                (x, y - tile_height / 2),
                (x + tile_width / 2, y),
                (x, y + tile_height / 2),
                (x - tile_width / 2, y),
            ]

            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, grid_color, points, 1)

    font = pygame.font.Font(None, 28)
    title = font.render(
        "ISOMETRIC WAREHOUSE PREVIEW",
        True,
        (240, 245, 250)
    )
    screen.blit(title, (25, 20))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
