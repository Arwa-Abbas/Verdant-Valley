"""
game_ui/csp_popup.py — CSP Layout Generation Popup (Wood Theme)
- Left side: Large farm layout preview
- Right side: Statistics panel with tile counts + progress bars
"""

import pygame
from utils.constants import *


class CSPPopup:
    def __init__(self, screen, grid, csp_solver):
        self.screen = screen
        self.grid = grid
        self.csp_solver = csp_solver
        self.visible = True
        self.confirmed = False

        self.width = 1020
        self.height = 720
        self.x = (SCREEN_W - self.width) // 2
        self.y = (SCREEN_H - self.height) // 2

        self.grid_area_width = int(self.width * 0.60)
        self.stats_area_width = self.width - self.grid_area_width - 50

        btn_width = 170
        btn_height = 46
        btn_x = self.x + self.width - btn_width - 22
        self.regenerate_button = pygame.Rect(
            btn_x, self.y + self.height - 118, btn_width, btn_height
        )
        self.confirm_button = pygame.Rect(
            btn_x, self.y + self.height - 62, btn_width, btn_height
        )

        self.font_title = pygame.font.Font(None, 38)
        self.font_sec = pygame.font.Font(None, 22)
        self.font_stat = pygame.font.Font(None, 20)
        self.font_btn = pygame.font.Font(None, 22)
        self.font_legend = pygame.font.Font(None, 16)

        self.wood_base = (139, 90, 43)
        self.wood_dark = (100, 65, 30)
        self.wood_light = (170, 115, 55)
        self.panel_bg = (28, 22, 16)
        self.inner_bg = (38, 30, 20)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _draw_section_header(self, text, x, y, width):
        """Draws a section label with a divider line."""
        label = self.font_sec.render(text, True, (255, 215, 0))
        self.screen.blit(label, (x, y))
        line_y = y + label.get_height() + 4
        pygame.draw.line(
            self.screen, self.wood_base, (x, line_y), (x + width, line_y), 1
        )
        return line_y + 8

    def _draw_bar(self, x, y, w, h, fraction, bar_color, bg_color=(60, 50, 40)):
        """Draws a simple horizontal progress bar."""
        pygame.draw.rect(self.screen, bg_color, (x, y, w, h), border_radius=3)
        fill_w = max(2, int(w * min(fraction, 1.0)))
        pygame.draw.rect(self.screen, bar_color, (x, y, fill_w, h), border_radius=3)

    def regenerate_everything(self):
        print("\n🔄 Regenerating entire farm layout...")
        self.grid._build_map()
        self.grid._bake_all()
        self.csp_solver.vars = self.grid.field_tiles()
        self.csp_solver.water = self.grid.water_sources()
        self.csp_solver.assign = {}
        self.csp_solver.log = []
        self.csp_solver.solve()
        self.csp_solver.apply_to_grid()
        print("✅ New layout generated!\n")

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = pygame.mouse.get_pos()
            if self.confirm_button.collidepoint(mp):
                self.visible = False
                self.confirmed = True
                return True
            if self.regenerate_button.collidepoint(mp):
                self.regenerate_everything()
                return True
        return False

    def draw_wood_button(self, rect, text, is_hover=False, accent=False):
        if accent:
            base = (60, 140, 80) if not is_hover else (75, 165, 95)
            dark = (35, 90, 50)
        else:
            base = self.wood_light if is_hover else self.wood_base
            dark = self.wood_dark

        pygame.draw.rect(self.screen, base, rect, border_radius=10)
        # subtle grain lines
        for i in range(3):
            ly = rect.y + 11 + i * 14
            pygame.draw.line(
                self.screen, dark, (rect.x + 10, ly), (rect.x + rect.width - 10, ly), 1
            )
        pygame.draw.rect(self.screen, dark, rect, 2, border_radius=10)
        surf = self.font_btn.render(text, True, (255, 255, 255))
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    # ── main draw ────────────────────────────────────────────────────────────

    def draw(self):
        if not self.visible:
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        # Outer frame
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.screen, self.wood_dark, panel, border_radius=18)
        pygame.draw.rect(
            self.screen, self.wood_light, panel.inflate(-4, -4), border_radius=16
        )
        pygame.draw.rect(
            self.screen, self.panel_bg, panel.inflate(-10, -10), border_radius=13
        )

        # Title bar strip
        title_strip = pygame.Rect(self.x + 5, self.y + 5, self.width - 10, 52)
        pygame.draw.rect(self.screen, self.wood_dark, title_strip, border_radius=13)
        title = self.font_title.render("FARM LAYOUT GENERATOR", True, (255, 215, 0))
        self.screen.blit(
            title, title.get_rect(center=(self.x + self.width // 2, self.y + 32))
        )

        content_y = self.y + 64
        content_h = self.height - 74

        # ── LEFT: grid preview ────────────────────────────────────────────
        gx = self.x + 12
        gy = content_y
        gw = self.grid_area_width - 18
        gh = content_h - 10

        pygame.draw.rect(self.screen, self.inner_bg, (gx, gy, gw, gh), border_radius=10)
        pygame.draw.rect(
            self.screen, self.wood_dark, (gx, gy, gw, gh), 1, border_radius=10
        )
        self.draw_grid_preview(gx + 6, gy + 6, gw - 12, gh - 12)

        # ── RIGHT: stats panel ────────────────────────────────────────────
        sx = self.x + self.grid_area_width + 8
        sy = content_y
        sw = self.stats_area_width
        sh = content_h - 10

        pygame.draw.rect(self.screen, self.inner_bg, (sx, sy, sw, sh), border_radius=10)
        pygame.draw.rect(
            self.screen, self.wood_dark, (sx, sy, sw, sh), 1, border_radius=10
        )

        cx = sx + 14
        cy = sy + 14

        # --- Crop counts ---
        cy = self._draw_section_header("CROPS", cx, cy, sw - 28)

        crop_counts = {CROP_WHEAT: 0, CROP_SUNFLOWER: 0, CROP_CORN: 0}
        for crop in self.csp_solver.assign.values():
            if crop in crop_counts:
                crop_counts[crop] += 1
        total_crops = sum(crop_counts.values())
        total_fields = max(len(self.csp_solver.vars), 1)

        crop_meta = {
            CROP_WHEAT: ("Wheat", (230, 200, 60)),
            CROP_SUNFLOWER: ("Sunflower", (255, 180, 0)),
            CROP_CORN: ("Corn", (160, 210, 60)),
        }
        bar_w = sw - 28

        for crop_type, (cname, ccolor) in crop_meta.items():
            count = crop_counts[crop_type]
            # color swatch + name + count
            pygame.draw.rect(self.screen, ccolor, (cx, cy + 2, 14, 14), border_radius=3)
            label = self.font_stat.render(f"{cname}", True, (210, 210, 200))
            count_surf = self.font_stat.render(str(count), True, (255, 215, 0))
            self.screen.blit(label, (cx + 20, cy))
            self.screen.blit(count_surf, (cx + bar_w - count_surf.get_width(), cy))
            cy += 20
            self._draw_bar(cx, cy, bar_w, 7, count / total_fields, ccolor)
            cy += 16

        # total fill rate
        fill_pct = int(100 * total_crops / total_fields)
        total_surf = self.font_stat.render(
            f"Fill rate  {total_crops}/{total_fields}  ({fill_pct}%)",
            True,
            (100, 220, 120),
        )
        self.screen.blit(total_surf, (cx, cy + 2))
        cy += 24
        self._draw_bar(
            cx, cy, bar_w, 9, total_crops / total_fields, (80, 200, 100), (50, 45, 35)
        )
        cy += 22

        # --- Terrain counts ---
        cy += 10
        cy = self._draw_section_header("TERRAIN", cx, cy, sw - 28)

        terrain_meta = {
            TILE_WATER: ("Water", (40, 90, 160)),
            TILE_FIELD: ("Field", (101, 67, 33)),
            TILE_GRASS: ("Grass", (56, 95, 40)),
            TILE_DIRT: ("Dirt", (94, 68, 42)),
            TILE_STONE: ("Stone", (100, 100, 110)),
            TILE_MUD: ("Mud", (85, 62, 40)),
        }
        terrain_counts = {t: 0 for t in terrain_meta}
        total_tiles = 0
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                tile = self.grid.get(c, r)
                if tile and tile.type in terrain_counts:
                    terrain_counts[tile.type] += 1
                    total_tiles += 1
        total_tiles = max(total_tiles, 1)

        for tile_type, (tname, tcolor) in terrain_meta.items():
            count = terrain_counts[tile_type]
            pygame.draw.rect(self.screen, tcolor, (cx, cy + 2, 14, 14), border_radius=3)
            label = self.font_stat.render(tname, True, (210, 210, 200))
            cnt_s = self.font_stat.render(str(count), True, (200, 200, 180))
            self.screen.blit(label, (cx + 20, cy))
            self.screen.blit(cnt_s, (cx + bar_w - cnt_s.get_width(), cy))
            cy += 20
            self._draw_bar(cx, cy, bar_w, 5, count / total_tiles, tcolor)
            cy += 13

        # --- Buttons ---
        mp = pygame.mouse.get_pos()
        self.draw_wood_button(
            self.regenerate_button,
            "REGENERATE",
            self.regenerate_button.collidepoint(mp),
        )
        self.draw_wood_button(
            self.confirm_button,
            "START FARMING",
            self.confirm_button.collidepoint(mp),
            accent=True,
        )

    # ── grid preview ─────────────────────────────────────────────────────────

    def draw_grid_preview(self, start_x, start_y, area_w, area_h):
        cell_size = min(area_w // GRID_COLS, area_h // GRID_ROWS, 20)
        total_w = GRID_COLS * cell_size
        total_h = GRID_ROWS * cell_size
        gx = start_x + (area_w - total_w) // 2
        gy = start_y + (area_h - total_h) // 2

        terrain_colors = {
            TILE_WATER: (40, 90, 160),
            TILE_FIELD: (101, 67, 33),
            TILE_GRASS: (56, 95, 40),
            TILE_DIRT: (94, 68, 42),
            TILE_STONE: (100, 100, 110),
            TILE_MUD: (85, 62, 40),
        }
        crop_colors = {
            CROP_WHEAT: (230, 200, 60),
            CROP_SUNFLOWER: (255, 180, 0),
            CROP_CORN: (160, 210, 60),
        }

        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                x = gx + c * cell_size
                y = gy + r * cell_size
                crop = self.csp_solver.assign.get((c, r), CROP_NONE)
                if crop in crop_colors:
                    color = crop_colors[crop]
                else:
                    tile = self.grid.get(c, r)
                    color = (
                        terrain_colors.get(tile.type, (80, 80, 80))
                        if tile
                        else (80, 80, 80)
                    )

                pygame.draw.rect(
                    self.screen, color, (x, y, cell_size - 1, cell_size - 1)
                )

        # thin border around entire preview
        pygame.draw.rect(self.screen, self.wood_dark, (gx, gy, total_w, total_h), 1)

    def is_confirmed(self):
        return self.confirmed
