"""
UIManager - Enhanced UI with HUD, sidebar panels, and game overlays
"""

import pygame
import random
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text
from game_ui.fonts import FontCache


class UIManager:
    """Manages all game UI elements including HUD and sidebar"""

    def __init__(self, screen):
        self.screen = screen

    # ============================================================
    # HUD (Top Bar)
    # ============================================================

    def draw_hud(self, season_mgr, agents, paused=False, tick=0):
        """Draw glass-style HUD strip with season info, scores, and rain effects"""
        hud_surface = pygame.Surface((SCREEN_W, GRID_OFFSET_Y), pygame.SRCALPHA)
        hud_surface.fill((20, 28, 22, 210))

        # Glass panel
        pygame.draw.rect(
            hud_surface,
            (255, 255, 255, 30),
            (10, 10, SCREEN_W - 20, GRID_OFFSET_Y - 20),
            border_radius=18,
        )
        pygame.draw.rect(
            hud_surface,
            (255, 255, 255, 60),
            (10, 10, SCREEN_W - 20, GRID_OFFSET_Y - 20),
            1,
            border_radius=18,
        )
        self.screen.blit(hud_surface, (0, 0))

        # Fonts
        title_font = FontCache.get(FONT_MEDIUM, bold=True)
        normal_font = FontCache.get(FONT_SMALL)
        tiny_font = FontCache.get(FONT_TINY)

        # Season card
        card_rect = pygame.Rect(20, 15, 280, 70)
        draw_rounded_rect(
            self.screen,
            (18, 34, 28, 210),
            card_rect,
            radius=16,
            border=2,
            border_color=(120, 185, 110),
        )

        season_text = title_font.render(season_mgr.name, True, C_TEXT_GOLD)
        self.screen.blit(season_text, (card_rect.x + 16, card_rect.y + 12))

        time_text = normal_font.render(
            f"Time: {season_mgr.time_label()}", True, C_TEXT_MAIN
        )
        self.screen.blit(time_text, (card_rect.x + 16, card_rect.y + 42))

        # Seasonal bloom glow effect
        glow_radius = 28 + int(season_mgr.bloom * 6)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf, (255, 215, 120, 80), (glow_radius, glow_radius), glow_radius
        )
        self.screen.blit(
            glow_surf, (card_rect.right - glow_radius - 10, card_rect.y + 12)
        )

        # Season progress bar
        bar_x, bar_y, bar_w, bar_h = 320, 35, 260, 12
        pygame.draw.rect(
            self.screen, (20, 30, 24), (bar_x, bar_y, bar_w, bar_h), border_radius=6
        )

        fill_w = int(bar_w * season_mgr.progress)
        if fill_w > 0:
            fill_color = (
                min(255, C_PROGRESS_FILL[0] + 20),
                min(255, C_PROGRESS_FILL[1] + 20),
                min(255, C_PROGRESS_FILL[2] + 20),
            )
            pygame.draw.rect(
                self.screen, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6
            )

        pygame.draw.rect(
            self.screen,
            (255, 255, 255, 100),
            (bar_x, bar_y, bar_w, bar_h),
            1,
            border_radius=6,
        )

        progress_label = tiny_font.render(
            f"Season progress {int(season_mgr.progress * 100)}%", True, C_TEXT_DIM
        )
        self.screen.blit(progress_label, (bar_x, bar_y + bar_h + 6))

        # Rain animation in HUD
        if season_mgr.rain_active:
            rain_rect = pygame.Rect(580, 26, 200, 46)
            draw_rounded_rect(
                self.screen,
                (18, 30, 40, 220),
                rain_rect,
                radius=16,
                border=1,
                border_color=C_TEXT_WARN,
            )

            rain_text = normal_font.render("Rain active", True, C_TEXT_WARN)
            self.screen.blit(rain_text, (rain_rect.x + 18, rain_rect.y + 12))

            # Raindrop animation
            for i in range(12):
                rx = (rain_rect.x + 18 + i * 16 + tick * 3) % (
                    rain_rect.x + rain_rect.width - 8
                )
                ry = rain_rect.y + 26 + (i % 3) * 4
                pygame.draw.line(
                    self.screen, (150, 190, 220, 180), (rx, ry), (rx + 5, ry + 12), 2
                )

        # Agent cards
        card_x = 20
        card_y = 15

        for agent in agents:
            if hasattr(agent, "alive") and not agent.alive:
                continue

            if "Farmer" in agent.name:
                agent_color = C_FARMER
                icon = "🌾"
            elif "Guard" in agent.name:
                agent_color = C_GUARD
                icon = "🛡️"
            else:
                agent_color = C_ANIMAL
                icon = "🐮"

            card_rect = pygame.Rect(card_x, card_y, 190, 70)
            draw_rounded_rect(
                self.screen,
                (25, 35, 28, 220),
                card_rect,
                radius=14,
                border=1,
                border_color=(agent_color[0], agent_color[1], agent_color[2], 180),
            )

            # Color bar at bottom of card
            pygame.draw.rect(
                self.screen,
                (agent_color[0], agent_color[1], agent_color[2], 40),
                (card_rect.x + 10, card_rect.y + 42, 160, 18),
                border_radius=8,
            )

            # Icon
            icon_text = normal_font.render(icon, True, agent_color)
            self.screen.blit(icon_text, (card_x + 14, card_y + 12))

            # Name
            name_text = normal_font.render(agent.name, True, C_TEXT_MAIN)
            self.screen.blit(name_text, (card_x + 40, card_y + 10))

            # State
            state_text = tiny_font.render(agent.state, True, C_TEXT_DIM)
            self.screen.blit(state_text, (card_x + 40, card_y + 34))

            # Score
            score_text = title_font.render(str(agent.score), True, C_TEXT_GOLD)
            self.screen.blit(score_text, (card_x + 14, card_y + 46))

            card_x += 200

        # Pause overlay
        if paused:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            pause_text = title_font.render("GAME PAUSED", True, C_TEXT_GOLD)
            pause_rect = pause_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            self.screen.blit(pause_text, pause_rect)

            resume_text = normal_font.render("Press P to resume", True, C_TEXT_DIM)
            resume_rect = resume_text.get_rect(
                center=(SCREEN_W // 2, SCREEN_H // 2 + 50)
            )
            self.screen.blit(resume_text, resume_rect)

    # ============================================================
    # SIDEBAR
    # ============================================================

    def draw_sidebar(self, grid, season_mgr, agents):
        """Draw enhanced right-hand info panel with stats, agents, crops, and controls"""
        panel_x = SCREEN_W - SIDEBAR_W
        panel_y = GRID_OFFSET_Y
        panel_w = SIDEBAR_W
        panel_h = SCREEN_H - panel_y

        # Panel background with wood-like texture lines
        sidebar_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        sidebar_surface.fill((18, 28, 22, 220))

        draw_rounded_rect(
            sidebar_surface,
            (24, 38, 28, 220),
            pygame.Rect(4, 4, panel_w - 8, panel_h - 8),
            radius=18,
            border=2,
            border_color=(90, 120, 90),
        )

        # Texture lines
        for i in range(panel_h - 16):
            ratio = i / (panel_h - 16)
            color = (
                int(30 * (1 - ratio) + 20 * ratio),
                int(46 * (1 - ratio) + 30 * ratio),
                int(36 * (1 - ratio) + 28 * ratio),
                18,
            )
            pygame.draw.line(
                sidebar_surface, color, (14, 12 + i), (panel_w - 14, 12 + i)
            )

        self.screen.blit(sidebar_surface, (panel_x, panel_y))

        # Fonts
        title_font = FontCache.get(FONT_MEDIUM, bold=True)
        normal_font = FontCache.get(FONT_SMALL)
        tiny_font = FontCache.get(FONT_TINY)

        y = panel_y + 15

        # Sections
        sections = [
            ("STATISTICS", C_TEXT_GOLD),
            ("AGENTS", C_TEXT_GOLD),
            ("CROP STATUS", C_TEXT_GOLD),
            ("CONTROLS", C_TEXT_GOLD),
        ]

        for section, section_color in sections:
            section_text = title_font.render(section, True, section_color)
            self.screen.blit(section_text, (panel_x + 15, y))
            y += 30
            pygame.draw.line(
                self.screen,
                C_PANEL_BORD,
                (panel_x + 10, y),
                (panel_x + panel_w - 10, y),
                1,
            )
            y += 15

            if section == "STATISTICS":
                # Season info
                season_text = normal_font.render(
                    f"Season: {season_mgr.name}", True, C_TEXT_MAIN
                )
                self.screen.blit(season_text, (panel_x + 15, y))
                y += 22

                progress = int(season_mgr.progress * 100)
                progress_text = tiny_font.render(
                    f"Progress: {progress}%", True, C_TEXT_DIM
                )
                self.screen.blit(progress_text, (panel_x + 15, y))
                y += 15

                # Progress bar
                bar_w = panel_w - 30
                pygame.draw.rect(
                    self.screen,
                    C_PROGRESS_BG,
                    (panel_x + 15, y, bar_w, 6),
                    border_radius=3,
                )
                fill_w = int(bar_w * season_mgr.progress)
                pygame.draw.rect(
                    self.screen,
                    C_PROGRESS_FILL,
                    (panel_x + 15, y, fill_w, 6),
                    border_radius=3,
                )
                y += 25

                # Rain status
                if season_mgr.rain_active:
                    rain_text = tiny_font.render("Rain active!", True, C_TEXT_WARN)
                    self.screen.blit(rain_text, (panel_x + 15, y))
                    y += 20

            elif section == "AGENTS":
                for agent in agents:
                    if hasattr(agent, "alive") and not agent.alive:
                        continue

                    # Agent card background
                    card_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, 65)
                    pygame.draw.rect(
                        self.screen, (30, 40, 30), card_rect, border_radius=6
                    )

                    # Icon and color
                    if "Farmer" in agent.name:
                        icon = "🌾"
                        agent_color = C_FARMER
                    elif "Guard" in agent.name:
                        icon = "🛡️"
                        agent_color = C_GUARD
                    else:
                        icon = "🐮"
                        agent_color = C_ANIMAL

                    # Icon
                    icon_text = title_font.render(icon, True, agent_color)
                    self.screen.blit(icon_text, (panel_x + 20, y + 10))

                    # Name
                    name_text = normal_font.render(agent.name, True, C_TEXT_MAIN)
                    self.screen.blit(name_text, (panel_x + 50, y + 10))

                    # State
                    state_text = tiny_font.render(
                        f"State: {agent.state}", True, C_TEXT_DIM
                    )
                    self.screen.blit(state_text, (panel_x + 50, y + 30))

                    # Position
                    pos_text = tiny_font.render(
                        f"Position: ({agent.col},{agent.row})", True, C_TEXT_DIM
                    )
                    self.screen.blit(pos_text, (panel_x + 50, y + 45))

                    # Score
                    score_text = title_font.render(str(agent.score), True, C_TEXT_GOLD)
                    self.screen.blit(score_text, (panel_x + panel_w - 60, y + 25))

                    y += 75

            elif section == "CROP STATUS":
                counts = {
                    CROP_WHEAT: 0,
                    CROP_SUNFLOWER: 0,
                    CROP_CORN: 0,
                    CROP_TOMATO: 0,
                    CROP_CARROT: 0,
                }
                crop_icons = {
                    CROP_WHEAT: "🌾",
                    CROP_SUNFLOWER: "🌻",
                    CROP_CORN: "🌽",
                    CROP_TOMATO: "🍅",
                    CROP_CARROT: "🥕",
                }

                for col in range(grid.cols):
                    for row in range(grid.rows):
                        tile = grid.tiles[col][row]
                        if tile.crop in counts:
                            counts[tile.crop] += 1

                for crop_id, count in counts.items():
                    if count > 0:
                        icon = crop_icons.get(crop_id, "❓")
                        crop_text = normal_font.render(
                            f"{icon} {CROP_NAMES[crop_id]}: {count}", True, C_TEXT_MAIN
                        )
                        self.screen.blit(crop_text, (panel_x + 15, y))
                        y += 22

            elif section == "CONTROLS":
                controls = ["P - Pause/Resume", "R - Restart Game", "ESC - Main Menu"]
                for control in controls:
                    control_text = tiny_font.render(control, True, C_TEXT_DIM)
                    self.screen.blit(control_text, (panel_x + 15, y))
                    y += 18
