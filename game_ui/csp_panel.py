"""
CSP Panel - Visualization for Constraint Satisfaction Problem solving
Shows grid preview, crop legend, and real-time assignment progress
"""

import pygame
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text
from game_ui.fonts import FontCache


class CSPPanel:
    """Displays CSP solving progress during farm layout generation"""

    def __init__(self, screen):
        self.screen = screen

    def draw(self, log_entry, all_vars, assignment):
        """
        Draw CSP visualization overlay.

        Args:
            log_entry: Tuple (col, row, crop, action) - most recent step
            all_vars: List of all variable coordinates (field tiles)
            assignment: Dict mapping (col,row) -> crop type
        """
        panel_w, panel_h = 600, 400
        panel_x = SCREEN_W // 2 - panel_w // 2
        panel_y = SCREEN_H // 2 - panel_h // 2

        # Panel background
        draw_rounded_rect(
            self.screen,
            C_BG_PANEL,
            (panel_x, panel_y, panel_w, panel_h),
            radius=12,
            border=2,
            border_color=C_PANEL_BORD,
        )

        # Fonts
        font_large = FontCache.get(FONT_LARGE)
        font_small = FontCache.get(FONT_SMALL)
        font_tiny = FontCache.get(FONT_TINY)

        # Title
        draw_text(
            self.screen,
            "CSP FARM LAYOUT PLANNER",
            font_large,
            C_TEXT_GOLD,
            SCREEN_W // 2,
            panel_y + 20,
            "center",
        )
        draw_text(
            self.screen,
            "Assigning crops via Backtracking + Forward Checking",
            font_small,
            C_TEXT_DIM,
            SCREEN_W // 2,
            panel_y + 48,
            "center",
        )

        # Grid preview (mini-map showing assigned crops)
        cell_size = 14
        cols_shown = min(GRID_COLS, 18)
        rows_shown = min(GRID_ROWS, 14)
        grid_x = panel_x + 20
        grid_y = panel_y + 75

        for col in range(cols_shown):
            for row in range(rows_shown):
                crop = assignment.get((col, row))
                if crop is not None and crop != CROP_NONE:
                    color = CROP_COLOR[crop]
                else:
                    color = C_BG_MID

                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        grid_x + col * cell_size,
                        grid_y + row * cell_size,
                        cell_size - 1,
                        cell_size - 1,
                    ),
                    border_radius=1,
                )

        # Crop legend
        legend_x = panel_x + 20
        legend_y = grid_y + rows_shown * cell_size + 12

        for crop_id, name in CROP_NAMES.items():
            if crop_id == CROP_NONE:
                continue

            pygame.draw.rect(
                self.screen,
                CROP_COLOR[crop_id],
                (legend_x, legend_y, 12, 12),
                border_radius=2,
            )
            draw_text(
                self.screen, name, font_tiny, C_TEXT_MAIN, legend_x + 16, legend_y
            )
            legend_x += 80

        # Latest action log (assignment or backtrack)
        if log_entry:
            col, row, crop, action = log_entry
            action_colors = {
                "assign": C_FARMER,
                "backtrack": C_TEXT_WARN,
                "final": C_TEXT_GOLD,
            }
            message = f"{action.upper()}  ({col},{row}) → {CROP_NAMES[crop]}"
            draw_text(
                self.screen,
                message,
                font_small,
                action_colors.get(action, C_TEXT_MAIN),
                SCREEN_W // 2,
                panel_y + panel_h - 40,
                "center",
            )

        # Progress counter
        assigned_count = len([c for c in assignment.values() if c != CROP_NONE])
        draw_text(
            self.screen,
            f"Assigned {assigned_count} / {len(all_vars)} tiles",
            font_tiny,
            C_TEXT_DIM,
            SCREEN_W // 2,
            panel_y + panel_h - 20,
            "center",
        )
