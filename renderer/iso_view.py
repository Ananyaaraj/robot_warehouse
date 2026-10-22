import math
import pygame


class IsometricView:
    """Convert warehouse grid coordinates to isometric screen coordinates."""

    def __init__(
        self,
        tile_width=24,
        tile_height=12,
        origin_x=550,
        origin_y=100
    ):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.origin_x = origin_x
        self.origin_y = origin_y

    def grid_to_screen(self, row, col):
        """Return the screen center of a warehouse grid cell."""
        x = self.origin_x + (col - row) * self.tile_width / 2
        y = self.origin_y + (col + row) * self.tile_height / 2
        return round(x), round(y)

    def screen_to_grid(self, x, y):
        """Convert screen coordinates back to grid row and column."""
        dx = (x - self.origin_x) / self.tile_width
        dy = (y - self.origin_y) / self.tile_height

        col = dx + dy
        row = dy - dx

        return round(row), round(col)

    def draw_tile(self, screen, row, col, color):
        """Draw a diamond-shaped isometric floor tile."""
        x, y = self.grid_to_screen(row, col)

        points = [
            (x, y - self.tile_height / 2),
            (x + self.tile_width / 2, y),
            (x, y + self.tile_height / 2),
            (x - self.tile_width / 2, y),
        ]

        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(
            screen,
            (48, 55, 62),
            points,
            width=1
        )
