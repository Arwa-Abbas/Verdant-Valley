"""
UIManager - Enhanced UI with better visuals
"""

import pygame
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text
from game_ui.fonts import FontCache


class UIManager:
    def __init__(self, screen):
        self.screen = screen

    def draw_hud(self, season_mgr, agents, paused=False):
        # Draw HUD background with gradient
        for i in range(GRID_OFFSET_Y):
            ratio = i / GRID_OFFSET_Y
            color = (
                int(C_HUD_BG[0] * (1 - ratio) + 20 * ratio),
                int(C_HUD_BG[1] * (1 - ratio) + 30 * ratio),
                int(C_HUD_BG[2] * (1 - ratio) + 20 * ratio),
            )
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_W, i))

        pygame.draw.line(
            self.screen,
            C_HUD_BORD,
            (0, GRID_OFFSET_Y - 1),
            (SCREEN_W, GRID_OFFSET_Y - 1),
            2,
        )

        f_title = FontCache.get(FONT_MEDIUM, bold=True)
        f_normal = FontCache.get(FONT_SMALL)

        # Season display with icon
        season_icon = season_mgr.name
        season_text = f_title.render(season_icon, True, C_TEXT_GOLD)
        self.screen.blit(season_text, (20, 15))

        # Time remaining
        time_text = f_normal.render(
            f"Time: {season_mgr.time_label()}", True, C_TEXT_DIM
        )
        self.screen.blit(time_text, (20, 45))

        # Season progress bar
        bar_x, bar_y, bar_w, bar_h = 20, 65, 200, 8
        pygame.draw.rect(
            self.screen, C_PROGRESS_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4
        )
        fill_w = int(bar_w * season_mgr.progress)
        if fill_w > 0:
            pygame.draw.rect(
                self.screen,
                C_PROGRESS_FILL,
                (bar_x, bar_y, fill_w, bar_h),
                border_radius=4,
            )
        pygame.draw.rect(
            self.screen, C_PANEL_BORD, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4
        )

        # Agent scores with custom cards
        score_x = 250
        for i, agent in enumerate(agents):
            if hasattr(agent, "alive") and not agent.alive:
                continue

            # Determine color
            if "Farmer" in agent.name:
                color = C_FARMER
                icon = "🌾"
            elif "Guard" in agent.name:
                color = C_GUARD
                icon = "🛡️"
            else:
                color = C_ANIMAL
                icon = "🐮"

            # Score card background
            card_rect = pygame.Rect(score_x, 10, 180, 60)
            pygame.draw.rect(self.screen, C_BG_PANEL, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, color, card_rect, 2, border_radius=8)

            # Agent info
            name_text = f_normal.render(f"{icon} {agent.name}", True, C_TEXT_MAIN)
            self.screen.blit(name_text, (score_x + 10, 18))

            score_text = f_title.render(f"{agent.score}", True, C_TEXT_GOLD)
            self.screen.blit(score_text, (score_x + 10, 38))

            score_x += 190

        # Rain effect indicator
        if season_mgr.rain_active:
            rain_text = f_title.render("🌧 RAINING!", True, C_TEXT_WARN)
            rain_rect = rain_text.get_rect(center=(SCREEN_W // 2, 40))
            self.screen.blit(rain_text, rain_rect)

            # Rain particles
            for _ in range(50):
                x = random.randint(0, SCREEN_W)
                y = random.randint(0, GRID_OFFSET_Y)
                pygame.draw.line(self.screen, (100, 150, 200), (x, y), (x, y + 5), 2)

        # Pause overlay
        if paused:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            pause_text = f_title.render("⏸ GAME PAUSED", True, C_TEXT_GOLD)
            pause_rect = pause_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            self.screen.blit(pause_text, pause_rect)

            resume_text = f_normal.render("Press P to resume", True, C_TEXT_DIM)
            resume_rect = resume_text.get_rect(
                center=(SCREEN_W // 2, SCREEN_H // 2 + 50)
            )
            self.screen.blit(resume_text, resume_rect)

    def draw_sidebar(self, grid, season_mgr, agents):
        """Enhanced right-hand info panel"""
        sx = SCREEN_W - SIDEBAR_W
        sy = GRID_OFFSET_Y
        sw = SIDEBAR_W
        sh = SCREEN_H - sy

        # Panel background with gradient
        for i in range(sh):
            ratio = i / sh
            color = (
                int(C_BG_PANEL[0] * (1 - ratio) + 30 * ratio),
                int(C_BG_PANEL[1] * (1 - ratio) + 40 * ratio),
                int(C_BG_PANEL[2] * (1 - ratio) + 30 * ratio),
            )
            pygame.draw.line(self.screen, color, (sx, sy + i), (sx + sw, sy + i))

        pygame.draw.rect(self.screen, C_PANEL_BORD, (sx, sy, sw, sh), 2)

        f_title = FontCache.get(FONT_MEDIUM, bold=True)
        f_normal = FontCache.get(FONT_SMALL)
        f_tiny = FontCache.get(FONT_TINY)

        y = sy + 15

        # Section headers with icons
        sections = [
            ("📊 STATISTICS", C_TEXT_GOLD),
            ("👥 AGENTS", C_TEXT_GOLD),
            ("🌾 CROP STATUS", C_TEXT_GOLD),
            ("🎮 CONTROLS", C_TEXT_GOLD),
        ]

        for section, color in sections:
            section_text = f_title.render(section, True, color)
            self.screen.blit(section_text, (sx + 15, y))
            y += 30
            pygame.draw.line(
                self.screen, C_PANEL_BORD, (sx + 10, y), (sx + sw - 10, y), 1
            )
            y += 15

            if section == "📊 STATISTICS":
                # Season stats
                season_text = f_normal.render(
                    f"Season: {season_mgr.name}", True, C_TEXT_MAIN
                )
                self.screen.blit(season_text, (sx + 15, y))
                y += 22

                progress = int(season_mgr.progress * 100)
                progress_text = f_tiny.render(
                    f"Progress: {progress}%", True, C_TEXT_DIM
                )
                self.screen.blit(progress_text, (sx + 15, y))
                y += 15

                # Mini progress bar
                bar_w = sw - 30
                pygame.draw.rect(
                    self.screen, C_PROGRESS_BG, (sx + 15, y, bar_w, 6), border_radius=3
                )
                fill_w = int(bar_w * season_mgr.progress)
                pygame.draw.rect(
                    self.screen,
                    C_PROGRESS_FILL,
                    (sx + 15, y, fill_w, 6),
                    border_radius=3,
                )
                y += 25

                # Rain status
                if season_mgr.rain_active:
                    rain_text = f_tiny.render("🌧 Rain active!", True, C_TEXT_WARN)
                    self.screen.blit(rain_text, (sx + 15, y))
                    y += 20

            elif section == "👥 AGENTS":
                for ag in agents:
                    if hasattr(ag, "alive") and not ag.alive:
                        continue

                    # Agent card background
                    card_rect = pygame.Rect(sx + 10, y, sw - 20, 65)
                    pygame.draw.rect(
                        self.screen, (30, 40, 30), card_rect, border_radius=6
                    )

                    # Determine icon and color
                    if "Farmer" in ag.name:
                        icon = "🌾"
                        color = C_FARMER
                    elif "Guard" in ag.name:
                        icon = "🛡️"
                        color = C_GUARD
                    else:
                        icon = "🐮"
                        color = C_ANIMAL

                    # Agent icon
                    icon_text = f_title.render(icon, True, color)
                    self.screen.blit(icon_text, (sx + 20, y + 10))

                    # Agent name and state
                    name_text = f_normal.render(ag.name, True, C_TEXT_MAIN)
                    self.screen.blit(name_text, (sx + 50, y + 10))

                    state_text = f_tiny.render(f"State: {ag.state}", True, C_TEXT_DIM)
                    self.screen.blit(state_text, (sx + 50, y + 30))

                    pos_text = f_tiny.render(
                        f"Position: ({ag.col},{ag.row})", True, C_TEXT_DIM
                    )
                    self.screen.blit(pos_text, (sx + 50, y + 45))

                    # Score
                    score_text = f_title.render(f"{ag.score}", True, C_TEXT_GOLD)
                    self.screen.blit(score_text, (sx + sw - 60, y + 25))

                    y += 75

            elif section == "🌾 CROP STATUS":
                counts = {CROP_WHEAT: 0, CROP_SUNFLOWER: 0, CROP_CORN: 0}
                for c in range(grid.cols):
                    for r in range(grid.rows):
                        t = grid.tiles[c][r]
                        if t.crop in counts:
                            counts[t.crop] += 1

                crop_icons = {CROP_WHEAT: "🌾", CROP_SUNFLOWER: "🌻", CROP_CORN: "🌽"}
                for crop_id, cnt in counts.items():
                    icon = crop_icons.get(crop_id, "❓")
                    crop_text = f_normal.render(
                        f"{icon} {CROP_NAMES[crop_id]}: {cnt}", True, C_TEXT_MAIN
                    )
                    self.screen.blit(crop_text, (sx + 15, y))
                    y += 25

            elif section == "🎮 CONTROLS":
                controls = [
                    "P - Pause/Resume",
                    "R - Restart Game",
                    "ESC - Main Menu",
                    "SPACE - Skip CSP",
                ]
                for control in controls:
                    control_text = f_tiny.render(control, True, C_TEXT_DIM)
                    self.screen.blit(control_text, (sx + 15, y))
                    y += 20

        # Version info
        version_text = f_tiny.render("v1.0 | AI Simulation", True, C_TEXT_DIM)
        self.screen.blit(version_text, (sx + 15, SCREEN_H - 25))
