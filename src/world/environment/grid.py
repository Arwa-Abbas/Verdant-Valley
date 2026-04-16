import random
import pygame
from utils.constants import *
from utils.helpers import grid_to_px, draw_rounded_rect


class Tile:
    def __init__(self, col, row, tile_type=TILE_GRASS):
        self.col = col
        self.row = row
        self.type = tile_type
        self.crop = CROP_NONE
        self.crop_stage = 0  # 0-3 growth stages
        self.wet = False  # rain effect

    @property
    def cost(self):
        return TILE_COST[self.type]

    @property
    def walkable(self):
        return self.cost < 500

    def rect(self):
        x, y = grid_to_px(self.col, self.row)
        return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)


class Grid:
    def __init__(self):
        self.cols = GRID_COLS
        self.rows = GRID_ROWS
        self.tiles = [[Tile(c, r) for r in range(self.rows)] for c in range(self.cols)]
        self._build_map()

    # ── Map generation ────────────────────────────────────────────────────────

    def _build_map(self):
        """Hand-crafted terrain: a river, stone path, mud patches, field zone."""
        # Field zone — columns 4-13, rows 2-11
        for c in range(4, 14):
            for r in range(2, 12):
                if c < self.cols and r < self.rows:
                    self.tiles[c][r].type = TILE_FIELD

        # River — column 0-1, full height
        for r in range(self.rows):
            if 0 < self.cols:
                self.tiles[0][r].type = TILE_WATER
            if 1 < self.cols:
                self.tiles[1][r].type = TILE_WATER

        # Stone path — row 12-13 (bottom border)
        for c in range(2, self.cols):
            if 12 < self.rows:
                self.tiles[c][12].type = TILE_STONE
            if 13 < self.rows:
                self.tiles[c][13].type = TILE_STONE

        # Mud patches
        mud_coords = [
            (3, 4),
            (3, 5),
            (3, 6),
            (14, 3),
            (14, 4),
            (14, 8),
            (14, 9),
            (15, 5),
        ]
        for c, r in mud_coords:
            if 0 <= c < self.cols and 0 <= r < self.rows:
                self.tiles[c][r].type = TILE_MUD

        # Dirt border around field
        for r in range(1, 13):
            if 2 < self.cols and r < self.rows:
                self.tiles[2][r].type = TILE_DIRT
            if 3 < self.cols and r < self.rows:
                self.tiles[3][r].type = TILE_DIRT
        for c in range(4, 16):
            if c < self.cols and 1 < self.rows:
                self.tiles[c][1].type = TILE_DIRT

        # Stone sprinkled in the field
        for _ in range(8):
            c = random.randint(4, min(13, self.cols - 1))
            r = random.randint(2, min(11, self.rows - 1))
            self.tiles[c][r].type = TILE_STONE

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.tiles[col][row]
        return None

    def water_sources(self):
        """Return list of (col,row) tiles that are water."""
        return [
            (c, r)
            for c in range(self.cols)
            for r in range(self.rows)
            if self.tiles[c][r].type == TILE_WATER
        ]

    def field_tiles(self):
        return [
            (c, r)
            for c in range(self.cols)
            for r in range(self.rows)
            if self.tiles[c][r].type == TILE_FIELD
        ]

    def crop_tiles(self):
        return [
            (c, r)
            for c in range(self.cols)
            for r in range(self.rows)
            if self.tiles[c][r].crop != CROP_NONE
        ]

    # ── Rain event ────────────────────────────────────────────────────────────

    def apply_rain(self):
        """Expand mud tiles by one, wet adjacent field tiles."""
        new_mud = []
        for c in range(self.cols):
            for r in range(self.rows):
                t = self.tiles[c][r]
                if t.type == TILE_MUD:
                    for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nc, nr = c + dc, r + dr
                        n = self.get(nc, nr)
                        if n and n.type in (TILE_DIRT, TILE_GRASS):
                            new_mud.append((nc, nr))
                if t.type in (TILE_FIELD, TILE_GRASS):
                    t.wet = True
        for c, r in new_mud:
            if 0 <= c < self.cols and 0 <= r < self.rows:
                self.tiles[c][r].type = TILE_MUD

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self, surface, font_tiny=None):
        for c in range(self.cols):
            for r in range(self.rows):
                t = self.tiles[c][r]
                x, y = grid_to_px(c, r)
                base_color = TILE_COLOR[t.type]

                # Darken mud when wet
                if t.wet and t.type != TILE_WATER:
                    base_color = tuple(max(0, v - 20) for v in base_color)

                pygame.draw.rect(surface, base_color, (x, y, TILE_SIZE, TILE_SIZE))

                # Crop overlay on field tile
                if t.type == TILE_FIELD and t.crop != CROP_NONE:
                    cc = CROP_COLOR[t.crop]
                    growth = (t.crop_stage + 1) / 4  # 0.25 – 1.0
                    size = int(TILE_SIZE * 0.55 * growth)
                    ox = x + (TILE_SIZE - size) // 2
                    oy = y + (TILE_SIZE - size) // 2
                    pygame.draw.rect(surface, cc, (ox, oy, size, size), border_radius=3)

                # Thin grid line
                pygame.draw.rect(
                    surface, (0, 0, 0, 40), (x, y, TILE_SIZE, TILE_SIZE), 1
                )
