"""
Game UI Components - Loading screen, main menu, HUD, sidebar, and CSP overlay
"""

import pygame
import math
import random
from utils.helpers import grid_to_px
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text, lerp_color


# ============================================================
# BLOCKED TILE INDICATOR
# ============================================================


def draw_blocked_tile_cross(
    surface, col, row, grid, color=(220, 40, 40), size=32, thickness=4
):
    """Draw a red cross on the specified tile (blocked movement indicator)"""
    x, y = grid_to_px(col, row)
    cx = x + grid.tiles[col][row].rect().width // 2
    cy = y + grid.tiles[col][row].rect().height // 2
    half = size // 2

    pygame.draw.line(
        surface, color, (cx - half, cy - half), (cx + half, cy + half), thickness
    )
    pygame.draw.line(
        surface, color, (cx - half, cy + half), (cx + half, cy - half), thickness
    )


# ============================================================
# FONT CACHE
# ============================================================


class FontCache:
    """Cache pygame fonts for performance"""

    _cache = {}

    @classmethod
    def get(cls, size, bold=False):
        key = (size, bold)
        if key not in cls._cache:
            try:
                cls._cache[key] = pygame.font.Font(None, size)
            except Exception:
                cls._cache[key] = pygame.font.SysFont("monospace", size, bold=bold)
        return cls._cache[key]


# ============================================================
# LOADING SCREEN
# ============================================================


class LoadingScreen:
    """Loading screen with animated particles and progress bar"""

    def __init__(self, screen):
        self.screen = screen
        self.progress = 0.0
        self.done = False
        self._tick = 0

        # Floating leaf particles
        rng = random.Random(42)
        self.particles = [
            {
                "x": rng.randint(0, SCREEN_W),
                "y": rng.randint(0, SCREEN_H),
                "vx": rng.uniform(-0.3, 0.3),
                "vy": rng.uniform(-0.5, -0.15),
                "alpha": rng.randint(60, 160),
            }
            for _ in range(60)
        ]

    def update(self, dt=1):
        """Update loading progress and particle positions"""
        self._tick += 1
        self.progress = min(1.0, self._tick / 120)

        if self.progress >= 1.0:
            self.done = True

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -20:
                p["y"] = SCREEN_H + 10
                p["x"] = random.randint(0, SCREEN_W)

    def draw(self):
        """Render loading screen"""
        screen = self.screen
        screen.fill(C_BG_DARK)

        # Floating particles
        leaf_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        for p in self.particles:
            leaf_surf.fill((0, 0, 0, 0))
            pygame.draw.ellipse(leaf_surf, (*C_GRASS, p["alpha"]), (0, 4, 12, 8))
            screen.blit(leaf_surf, (int(p["x"]), int(p["y"])))

        # Title
        font_title = FontCache.get(FONT_HUGE, bold=True)
        font_sub = FontCache.get(FONT_LARGE)
        draw_text(
            screen,
            "VERDANT VALLEY",
            font_title,
            C_TEXT_GOLD,
            SCREEN_W // 2,
            SCREEN_H // 2 - 80,
            "center",
        )
        draw_text(
            screen,
            "Multi-Agent AI Farming Simulation",
            font_sub,
            C_TEXT_DIM,
            SCREEN_W // 2,
            SCREEN_H // 2,
            "center",
        )

        # Progress bar
        bar_w, bar_h = 400, 10
        bar_x = SCREEN_W // 2 - bar_w // 2
        bar_y = SCREEN_H // 2 + 60

        pygame.draw.rect(
            screen, C_BG_MID, (bar_x, bar_y, bar_w, bar_h), border_radius=5
        )

        fill = int(bar_w * self.progress)
        if fill > 0:
            pygame.draw.rect(
                screen, C_GRASS, (bar_x, bar_y, fill, bar_h), border_radius=5
            )

        pygame.draw.rect(
            screen, C_PANEL_BORD, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5
        )

        # Percentage text
        percent_font = FontCache.get(FONT_SMALL)
        draw_text(
            screen,
            f"Loading... {int(self.progress * 100)}%",
            percent_font,
            C_TEXT_DIM,
            SCREEN_W // 2,
            bar_y + 20,
            "center",
        )


# ============================================================
# BUTTON
# ============================================================


class Button:
    """Interactive button with hover effect"""

    def __init__(self, label, rect, color_normal, color_hover, color_text=None):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.color_text = color_text or C_TEXT_MAIN
        self.hovered = False

    def handle(self, event):
        """Process mouse events, return True when clicked"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        color = self.color_hover if self.hovered else self.color_normal
        draw_rounded_rect(
            surface, color, self.rect, radius=10, border=1, border_color=C_PANEL_BORD
        )

        font = FontCache.get(FONT_MEDIUM)
        draw_text(
            surface,
            self.label,
            font,
            self.color_text,
            self.rect.centerx,
            self.rect.centery,
            "center",
        )


# ============================================================
# MAIN MENU
# ============================================================


class MainMenu:
    """Main menu with animated background and buttons"""

    def __init__(self, screen):
        self.screen = screen
        self._tick = 0
        center_x = SCREEN_W // 2
        btn_w, btn_h = 260, 52
        gap = 16
        start_y = SCREEN_H // 2 + 20

        self.btn_start = Button(
            "Start Game",
            (center_x - btn_w // 2, start_y, btn_w, btn_h),
            (38, 70, 38),
            (55, 100, 55),
        )
        self.btn_how = Button(
            "How to Play",
            (center_x - btn_w // 2, start_y + btn_h + gap, btn_w, btn_h),
            (30, 50, 60),
            (40, 75, 90),
        )
        self.btn_quit = Button(
            "Quit",
            (center_x - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h),
            (60, 30, 30),
            (90, 45, 45),
        )

        self.buttons = [self.btn_start, self.btn_how, self.btn_quit]

        # Decorative drifting leaves
        rng = random.Random(7)
        self.leaves = [
            {
                "x": rng.randint(0, SCREEN_W),
                "y": rng.randint(0, SCREEN_H),
                "r": rng.uniform(0, math.pi * 2),
                "s": rng.uniform(1.5, 4),
            }
            for _ in range(80)
        ]

    def handle(self, event):
        """Return 'start', 'howto', 'quit', or None"""
        for btn in self.buttons:
            if btn.handle(event):
                if btn is self.btn_start:
                    return "start"
                if btn is self.btn_how:
                    return "howto"
                if btn is self.btn_quit:
                    return "quit"
        return None

    def update(self):
        """Animate drifting leaves"""
        self._tick += 1
        for leaf in self.leaves:
            leaf["r"] += 0.008
            leaf["y"] -= leaf["s"] * 0.4
            if leaf["y"] < -30:
                leaf["y"] = SCREEN_H + 10
                leaf["x"] = random.randint(0, SCREEN_W)

    def draw(self):
        """Render main menu"""
        screen = self.screen
        screen.fill(C_BG_DARK)

        # Drifting leaves
        for leaf in self.leaves:
            alpha = int(abs(math.sin(leaf["r"])) * 100 + 30)
            pygame.draw.ellipse(
                screen,
                (*C_GRASS, min(255, alpha)),
                (int(leaf["x"]), int(leaf["y"]), 12, 7),
            )

        # Vignette effect
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i in range(6):
            alpha = 12
            margin = i * 60
            pygame.draw.rect(
                vignette,
                (0, 0, 0, alpha),
                (margin, margin, SCREEN_W - 2 * margin, SCREEN_H - 2 * margin),
                margin,
            )
        screen.blit(vignette, (0, 0))

        # Title with pulse glow
        pulse = 0.5 + 0.5 * math.sin(self._tick * 0.04)
        glow_color = lerp_color(C_TEXT_GOLD, (255, 255, 255), pulse * 0.3)

        font_huge = FontCache.get(FONT_HUGE, bold=True)
        font_med = FontCache.get(FONT_MEDIUM)
        font_tiny = FontCache.get(FONT_SMALL)

        draw_text(
            screen,
            "VERDANT VALLEY",
            font_huge,
            glow_color,
            SCREEN_W // 2,
            SCREEN_H // 2 - 130,
            "center",
        )
        draw_text(
            screen,
            "Multi-Agent AI Farming Simulation",
            font_med,
            C_TEXT_DIM,
            SCREEN_W // 2,
            SCREEN_H // 2 - 60,
            "center",
        )

        # Feature tags
        tags = ["A* Pathfinding", "CSP Layout", "Genetic Evolution"]
        total_w = (
            sum(FontCache.get(FONT_TINY).size(f"  {t}  ")[0] + 10 for t in tags) + 20
        )
        tag_x = SCREEN_W // 2 - total_w // 2
        tag_y = SCREEN_H // 2 - 25

        for tag in tags:
            label = f"  {tag}  "
            tw, th = FontCache.get(FONT_TINY).size(label)
            draw_rounded_rect(
                screen,
                C_BG_MID,
                (tag_x, tag_y, tw + 8, th + 8),
                radius=5,
                border=1,
                border_color=C_PANEL_BORD,
            )
            draw_text(
                screen,
                label,
                FontCache.get(FONT_TINY),
                C_TEXT_DIM,
                tag_x + 4,
                tag_y + 4,
            )
            tag_x += tw + 18

        # Buttons
        for btn in self.buttons:
            btn.draw(screen)

        # Footer
        draw_text(
            screen,
            "FAST-NUCES  ·  Spring 2026  ·  BCS-6C",
            font_tiny,
            C_TEXT_DIM,
            SCREEN_W // 2,
            SCREEN_H - 30,
            "center",
        )


# ============================================================
# HUD (TOP BAR)
# ============================================================


def draw_hud(surface, season_mgr, agents, paused=False):
    """Draw top HUD bar with season info, scores, and rain indicator"""
    pygame.draw.rect(surface, C_HUD_BG, (0, 0, SCREEN_W, GRID_OFFSET_Y))
    pygame.draw.line(
        surface, C_HUD_BORD, (0, GRID_OFFSET_Y - 1), (SCREEN_W, GRID_OFFSET_Y - 1)
    )

    font_med = FontCache.get(FONT_MEDIUM)
    font_small = FontCache.get(FONT_SMALL)

    # Season and time
    draw_text(surface, f"{season_mgr.name}", font_med, C_TEXT_GOLD, 16, 18)
    draw_text(surface, season_mgr.time_label(), font_small, C_TEXT_DIM, 16, 38)

    # Season progress bar
    bar_x, bar_y, bar_w, bar_h = 130, 22, 100, 8
    pygame.draw.rect(surface, C_BG_MID, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    fill = int(bar_w * season_mgr.progress)
    pygame.draw.rect(surface, C_TEXT_GOLD, (bar_x, bar_y, fill, bar_h), border_radius=3)
    pygame.draw.rect(
        surface, C_PANEL_BORD, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3
    )

    # Agent scores
    score_x = 280
    for agent in agents:
        if hasattr(agent, "alive") and not agent.alive:
            continue

        if "Farmer" in agent.name:
            icon, color = "●", C_FARMER
        elif "Guard" in agent.name:
            icon, color = "●", C_GUARD
        else:
            icon, color = "●", C_ANIMAL

        draw_text(
            surface,
            f"{icon} {agent.name}: {agent.score}",
            font_small,
            color,
            score_x,
            22,
        )
        score_x += 180

    # Rain indicator
    if season_mgr.rain_active:
        draw_text(surface, "Rain!", font_med, C_TEXT_WARN, SCREEN_W // 2 - 40, 16)

    # Pause overlay
    if paused:
        draw_text(
            surface,
            "PAUSED — press P to resume",
            font_med,
            C_TEXT_GOLD,
            SCREEN_W // 2,
            SCREEN_H // 2,
            "center",
        )


# ============================================================
# SIDEBAR PANEL
# ============================================================


def draw_sidebar(surface, grid, season_mgr, agents, selected_agent=None):
    """Draw right-side info panel with stats, agents, and controls"""
    panel_x = SCREEN_W - SIDEBAR_W
    panel_y = GRID_OFFSET_Y
    panel_w = SIDEBAR_W
    panel_h = SCREEN_H - panel_y

    draw_rounded_rect(
        surface,
        C_BG_PANEL,
        (panel_x, panel_y, panel_w, panel_h),
        radius=0,
        border=1,
        border_color=C_PANEL_BORD,
    )

    font_med = FontCache.get(FONT_MEDIUM)
    font_small = FontCache.get(FONT_SMALL)
    font_tiny = FontCache.get(FONT_TINY)

    y = panel_y + 14
    draw_text(surface, "SIMULATION INFO", font_med, C_TEXT_GOLD, panel_x + 12, y)
    y += 28
    pygame.draw.line(
        surface, C_PANEL_BORD, (panel_x + 8, y), (panel_x + panel_w - 8, y)
    )
    y += 10

    # Season
    draw_text(
        surface, f"Season: {season_mgr.name}", font_small, C_TEXT_MAIN, panel_x + 12, y
    )
    y += 22

    prog_pct = int(season_mgr.progress * 100)
    draw_text(surface, f"Progress: {prog_pct}%", font_tiny, C_TEXT_DIM, panel_x + 12, y)
    y += 20

    # Progress bar
    bar_w = panel_w - 24
    pygame.draw.rect(surface, C_BG_MID, (panel_x + 12, y, bar_w, 6), border_radius=3)
    pygame.draw.rect(
        surface,
        C_TEXT_GOLD,
        (panel_x + 12, y, int(bar_w * season_mgr.progress), 6),
        border_radius=3,
    )
    y += 20

    # Agents section
    pygame.draw.line(
        surface, C_PANEL_BORD, (panel_x + 8, y), (panel_x + panel_w - 8, y)
    )
    y += 8
    draw_text(surface, "AGENTS", font_med, C_TEXT_GOLD, panel_x + 12, y)
    y += 26

    for agent in agents:
        if hasattr(agent, "alive") and not agent.alive:
            continue

        name = agent.__class__.__name__
        color_map = {"Farmer": C_FARMER, "Guard": C_GUARD, "Animal": C_ANIMAL}
        agent_color = color_map.get(name, C_TEXT_DIM)

        pygame.draw.circle(surface, agent_color, (panel_x + 22, y + 8), 7)
        draw_text(surface, f"{agent.name}", font_small, C_TEXT_MAIN, panel_x + 36, y)
        draw_text(
            surface,
            f"({agent.col},{agent.row}) state: {agent.state}",
            font_tiny,
            C_TEXT_DIM,
            panel_x + 36,
            y + 16,
        )
        draw_text(
            surface,
            f"score: {agent.score}",
            font_tiny,
            C_TEXT_DIM,
            panel_x + 36,
            y + 30,
        )
        y += 52

    # A* stats
    pygame.draw.line(
        surface, C_PANEL_BORD, (panel_x + 8, y), (panel_x + panel_w - 8, y)
    )
    y += 8
    draw_text(surface, "A* LIVE", font_med, C_TEXT_GOLD, panel_x + 12, y)
    y += 26

    for agent in agents:
        if hasattr(agent, "explored") and agent.explored:
            draw_text(
                surface,
                f"{agent.name}: {len(agent.explored)} nodes",
                font_tiny,
                C_TEXT_DIM,
                panel_x + 12,
                y,
            )
            y += 18

    # Crop counts
    pygame.draw.line(
        surface, C_PANEL_BORD, (panel_x + 8, y), (panel_x + panel_w - 8, y)
    )
    y += 8
    draw_text(surface, "CROPS", font_med, C_TEXT_GOLD, panel_x + 12, y)
    y += 26

    counts = {
        crop: 0
        for crop in [
            CROP_WHEAT,
            CROP_SUNFLOWER,
            CROP_CORN,
            CROP_TOMATO,
            CROP_CARROT,
            CROP_NONE,
        ]
    }

    for col in range(grid.cols):
        for row in range(grid.rows):
            tile = grid.tiles[col][row]
            if tile.crop in counts:
                counts[tile.crop] += 1

    for crop_id, count in counts.items():
        if crop_id == CROP_NONE:
            continue
        color = CROP_COLOR[crop_id]
        pygame.draw.rect(surface, color, (panel_x + 12, y + 2, 10, 10), border_radius=2)
        draw_text(
            surface,
            f"{CROP_NAMES[crop_id]}: {count}",
            font_small,
            C_TEXT_MAIN,
            panel_x + 28,
            y,
        )
        y += 20

    # Controls
    y = SCREEN_H - 90
    pygame.draw.line(
        surface, C_PANEL_BORD, (panel_x + 8, y), (panel_x + panel_w - 8, y)
    )
    y += 8

    controls = ["P — Pause/Resume", "R — Restart", "ESC — Menu"]
    for control in controls:
        draw_text(surface, control, font_tiny, C_TEXT_DIM, panel_x + 12, y)
        y += 16


# ============================================================
# CSP OVERLAY PANEL
# ============================================================


def draw_csp_overlay(surface, log_entry, all_vars, assignment):
    """Show CSP solving progress during farm layout generation"""
    panel_w, panel_h = 600, 400
    panel_x = SCREEN_W // 2 - panel_w // 2
    panel_y = SCREEN_H // 2 - panel_h // 2

    # Panel background
    draw_rounded_rect(
        surface,
        C_BG_PANEL,
        (panel_x, panel_y, panel_w, panel_h),
        radius=12,
        border=2,
        border_color=C_PANEL_BORD,
    )

    font_large = FontCache.get(FONT_LARGE)
    font_small = FontCache.get(FONT_SMALL)
    font_tiny = FontCache.get(FONT_TINY)

    # Title
    draw_text(
        surface,
        "CSP FARM LAYOUT PLANNER",
        font_large,
        C_TEXT_GOLD,
        SCREEN_W // 2,
        panel_y + 20,
        "center",
    )
    draw_text(
        surface,
        "Assigning crops via Backtracking + Forward Checking",
        font_small,
        C_TEXT_DIM,
        SCREEN_W // 2,
        panel_y + 48,
        "center",
    )

    # Grid preview
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
                surface,
                color,
                (
                    grid_x + col * cell_size,
                    grid_y + row * cell_size,
                    cell_size - 1,
                    cell_size - 1,
                ),
                border_radius=1,
            )

    # Legend
    legend_x = panel_x + 20
    legend_y = grid_y + rows_shown * cell_size + 12

    for crop_id, name in CROP_NAMES.items():
        if crop_id == CROP_NONE:
            continue
        pygame.draw.rect(
            surface, CROP_COLOR[crop_id], (legend_x, legend_y, 12, 12), border_radius=2
        )
        draw_text(surface, name, font_tiny, C_TEXT_MAIN, legend_x + 16, legend_y)
        legend_x += 80

    # Last action log
    if log_entry:
        col, row, crop, action = log_entry
        action_colors = {
            "assign": C_FARMER,
            "backtrack": C_TEXT_WARN,
            "final": C_TEXT_GOLD,
        }
        message = f"{action.upper()}  ({col},{row}) → {CROP_NAMES[crop]}"
        draw_text(
            surface,
            message,
            font_small,
            action_colors.get(action, C_TEXT_MAIN),
            SCREEN_W // 2,
            panel_y + panel_h - 40,
            "center",
        )

    # Progress
    assigned = len([c for c in assignment.values() if c != CROP_NONE])
    draw_text(
        surface,
        f"Assigned {assigned} / {len(all_vars)} tiles",
        font_tiny,
        C_TEXT_DIM,
        SCREEN_W // 2,
        panel_y + panel_h - 20,
        "center",
    )
