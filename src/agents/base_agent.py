"""
Base Agent Class - Provides common functionality for all NPC agents with animation support
"""

import pygame
from utils.constants import *
from utils.helpers import tile_center, grid_to_px
from utils.animation import Animation


class Agent:
    """Base class for all NPC agents with animation and pathfinding support"""

    def __init__(
        self,
        col,
        row,
        color,
        speed=2.5,
        name="Agent",
        sprite_sheet_path=None,
        frame_size=(48, 48),
        animation_rows=4,
        animation_cols=4,
        scale=1,
    ):
        self.col = col
        self.row = row
        self.color = color
        self.name = name
        self.speed = speed

        # Animation
        self.animation = None
        self.last_direction = 0
        self.last_pos = (col, row)

        if sprite_sheet_path:
            try:
                import os

                if os.path.exists(sprite_sheet_path):
                    self.animation = Animation(
                        sprite_sheet_path,
                        frame_size[0],
                        frame_size[1],
                        animation_rows,
                        animation_cols,
                        scale,
                    )
            except Exception:
                self.animation = None

        # Position (pixel coordinates)
        cx, cy = tile_center(col, row)
        self.x = float(cx)
        self.y = float(cy)

        # Pathfinding
        self.path = []
        self.path_idx = 0
        self.explored = set()
        self.moving = False

        # Stats
        self.score = 0
        self.state = "idle"

    # ============================================================
    # ANIMATION
    # ============================================================

    def update_animation_direction(self):
        """Update animation frame based on movement direction"""
        if not self.animation:
            return

        dx = self.col - self.last_pos[0]
        dy = self.row - self.last_pos[1]

        if dx > 0:
            self.animation.set_direction(3)  # Right
        elif dx < 0:
            self.animation.set_direction(2)  # Left
        elif dy > 0:
            self.animation.set_direction(0)  # Down
        elif dy < 0:
            self.animation.set_direction(1)  # Up

        self.last_pos = (self.col, self.row)

        if self.moving:
            self.animation.update()
        else:
            if self.animation:
                self.animation.current_frame = 0
                self.animation.animation_timer = 0

    # ============================================================
    # MOVEMENT & PATHFINDING
    # ============================================================

    def set_path(self, path, explored=None):
        """
        Set the path to follow (excluding the start node).
        A* returns path including start node - we strip it here.
        """
        if path and len(path) > 1:
            # Strip the start node (agent is already there)
            self.path = path[1:]
        else:
            self.path = []

        self.path_idx = 0
        self.explored = explored or set()
        self.moving = len(self.path) > 0

        if self.animation and self.moving:
            self.animation.reset()

    def _move_along_path(self, grid=None):
        """Move one step toward the next tile in the path"""
        # No path to follow
        if not self.path or self.path_idx >= len(self.path):
            self.moving = False
            self.path = []
            self.path_idx = 0
            return

        target_col, target_row = self.path[self.path_idx]

        # Check if tile became impassable (e.g., winter freeze)
        if grid is not None and not self._can_step(grid, target_col, target_row):
            self.moving = False
            self.path = []
            self.path_idx = 0
            return

        tx, ty = tile_center(target_col, target_row)
        dx = tx - self.x
        dy = ty - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist <= self.speed:
            # Snap to tile center and advance
            self.x = float(tx)
            self.y = float(ty)
            self.col = target_col
            self.row = target_row
            self.path_idx += 1

            if self.path_idx >= len(self.path):
                self.moving = False
                self.path = []
                self.path_idx = 0
        else:
            # Move toward target
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def _can_step(self, grid, col, row):
        """Check if agent can move to (col, row). Override in subclass."""
        tile = grid.get(col, row)
        return tile is not None

    # ============================================================
    # UPDATE & DRAW
    # ============================================================

    def update(self, grid, agents, season_mgr=None):
        """Update agent state each frame"""
        self._move_along_path(grid)

    def draw(self, surface, font=None):
        """Draw agent sprite or fallback circle"""
        self.update_animation_direction()

        if self.animation and self.animation.get_frame():
            sprite = self.animation.get_frame()
            if sprite:
                sprite_rect = sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(sprite, sprite_rect)
            else:
                self._draw_circle_fallback(surface)
        else:
            self._draw_circle_fallback(surface)

        # Draw name label
        if font:
            label = font.render(self.name, True, C_TEXT_MAIN)
            surface.blit(
                label,
                (
                    int(self.x) - label.get_width() // 2,
                    int(self.y) - TILE_SIZE // 2 - 16,
                ),
            )

    def _draw_circle_fallback(self, surface):
        """Draw colored circle as fallback when sprite is unavailable"""
        radius = TILE_SIZE // 2 - 4
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), radius, 2)

    def draw_path_overlay(self, surface, path_color):
        """Draw explored nodes and path overlay on grid"""
        if not self.path and not self.explored:
            return

        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Draw explored nodes
        if self.explored:
            overlay.fill(C_EXPLORED)
            for col, row in self.explored:
                x, y = grid_to_px(col, row)
                surface.blit(overlay, (x, y))

        # Draw path nodes
        if self.path:
            overlay.fill((*path_color[:3], 160))
            for col, row in self.path[self.path_idx :]:
                x, y = grid_to_px(col, row)
                surface.blit(overlay, (x, y))
