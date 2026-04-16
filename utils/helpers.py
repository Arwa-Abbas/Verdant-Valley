import pygame
import math
from utils.constants import *


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def grid_to_px(col, row):
    return (GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE)


def tile_center(col, row):
    x, y = grid_to_px(col, row)
    return x + TILE_SIZE // 2, y + TILE_SIZE // 2


def neighbors_4(col, row, cols, rows):
    for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nc, nr = col + dc, row + dr
        if 0 <= nc < cols and 0 <= nr < rows:
            yield nc, nr


def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def draw_text(surface, text, font, color, x, y, anchor="topleft"):
    surf = font.render(text, True, color)
    r = surf.get_rect()
    setattr(r, anchor, (x, y))
    surface.blit(surf, r)
    return r


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
