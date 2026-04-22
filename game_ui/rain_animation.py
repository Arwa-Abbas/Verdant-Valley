import pygame
import random
from utils.constants import (
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
    SCREEN_W,
    SCREEN_H,
)


class RainAnimation:
    def __init__(self, grid):
        self.grid = grid
        self.raindrops = []
        self.active = False
        self.timer = 0
        self.duration = 10 * 60
        self.num_raindrops = 150

    def start(self):
        """Start the rain animation"""
        self.active = True
        self.timer = self.duration
        self.raindrops = []

        grid_start_x = GRID_OFFSET_X
        grid_end_x = GRID_OFFSET_X + (GRID_COLS * TILE_SIZE)
        grid_start_y = GRID_OFFSET_Y
        grid_end_y = GRID_OFFSET_Y + (GRID_ROWS * TILE_SIZE)

        for _ in range(self.num_raindrops):
            self.raindrops.append(
                {
                    "x": random.randint(grid_start_x, grid_end_x),
                    "y": random.randint(grid_start_y - 50, grid_start_y),
                    "length": random.randint(8, 20),
                    "speed": random.randint(5, 12),
                    "color": (150, 200, 255),
                }
            )

    def update(self):
        """Update raindrop positions. Returns True when animation finishes."""
        if not self.active:
            return False

        self.timer -= 1

        if self.timer <= 0:
            self.active = False
            return True

        grid_bottom = GRID_OFFSET_Y + (GRID_ROWS * TILE_SIZE)

        for drop in self.raindrops:
            drop["y"] += drop["speed"]

            if drop["y"] > grid_bottom:
                drop["y"] = GRID_OFFSET_Y - 20
                drop["x"] = random.randint(
                    GRID_OFFSET_X, GRID_OFFSET_X + (GRID_COLS * TILE_SIZE)
                )

        return False

    def draw(self, surface):
        """Draw all raindrops"""
        if not self.active:
            return

        for drop in self.raindrops:
            end_y = drop["y"] + drop["length"]
            pygame.draw.line(
                surface,
                drop["color"],
                (int(drop["x"]), int(drop["y"])),
                (int(drop["x"]), int(end_y)),
                2,
            )
