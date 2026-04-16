"""
CSP Panel - Visualization for Constraint Satisfaction Problem solving
"""

import pygame
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text
from game_ui.fonts import FontCache


class CSPPanel:
    def __init__(self, screen):
        self.screen = screen

    def draw(self, log_entry, all_vars, assignment):
        """Draw CSP visualization overlay"""
        ow, oh = 600, 400
        ox = SCREEN_W // 2 - ow // 2
        oy = SCREEN_H // 2 - oh // 2

        # Panel background
        draw_rounded_rect(
            self.screen,
            C_BG_PANEL,
            (ox, oy, ow, oh),
            radius=12,
            border=2,
            border_color=C_PANEL_BORD,
        )

        f = FontCache.get(FONT_LARGE)
        fs = FontCache.get(FONT_SMALL)
        ft = FontCache.get(FONT_TINY)

        draw_text(
            self.screen,
            "CSP FARM LAYOUT PLANNER",
            f,
            C_TEXT_GOLD,
            SCREEN_W // 2,
            oy + 20,
            "center",
        )
        draw_text(
            self.screen,
            "Assigning crops via Backtracking + Forward Checking",
            fs,
            C_TEXT_DIM,
            SCREEN_W // 2,
            oy + 48,
            "center",
        )

        # Assignment grid mini-view
        cell = 14
        cols_shown = min(GRID_COLS, 18)
        rows_shown = min(GRID_ROWS, 14)
        gx = ox + 20
        gy = oy + 75
        for c in range(cols_shown):
            for r in range(rows_shown):
                color = C_BG_MID
                crop = assignment.get((c, r))
                if crop is not None and crop != CROP_NONE:
                    color = CROP_COLOR[crop]
                pygame.draw.rect(
                    self.screen,
                    color,
                    (gx + c * cell, gy + r * cell, cell - 1, cell - 1),
                    border_radius=1,
                )

        # Legend
        lx = ox + 20
        ly = gy + rows_shown * cell + 12
        for crop_id, name in CROP_NAMES.items():
            if crop_id == CROP_NONE:
                continue
            pygame.draw.rect(
                self.screen, CROP_COLOR[crop_id], (lx, ly, 12, 12), border_radius=2
            )
            draw_text(self.screen, name, ft, C_TEXT_MAIN, lx + 16, ly)
            lx += 80

        # Last action log
        if log_entry:
            c, r, crop, action = log_entry
            col_map = {
                "assign": C_FARMER,
                "backtrack": C_TEXT_WARN,
                "final": C_TEXT_GOLD,
            }
            msg = f"{action.upper()}  ({c},{r}) → {CROP_NAMES[crop]}"
            draw_text(
                self.screen,
                msg,
                fs,
                col_map.get(action, C_TEXT_MAIN),
                SCREEN_W // 2,
                oy + oh - 40,
                "center",
            )

        assigned = len([v for v, cr in assignment.items() if cr != CROP_NONE])
        draw_text(
            self.screen,
            f"Assigned {assigned} / {len(all_vars)} tiles",
            ft,
            C_TEXT_DIM,
            SCREEN_W // 2,
            oy + oh - 20,
            "center",
        )
