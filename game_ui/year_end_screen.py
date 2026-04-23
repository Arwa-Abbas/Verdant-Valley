"""
Year End Screen - Shows after completing 4 seasons (1 year)
Options: CONTINUE (next year), RESTART (fresh game), MAIN MENU
"""

import pygame
from utils.constants import SCREEN_W, SCREEN_H


class YearEndScreen:
    """End of year summary screen showing scores and evolution results"""

    def __init__(
        self,
        screen,
        farmer_score,
        guard_score,
        animal_score,
        year,
        fox_fitness_before,
        rabbit_fitness_before,
        fox_chromo_before,
        rabbit_chromo_before,
        fox_fitness_after,
        rabbit_fitness_after,
        fox_chromo_after,
        rabbit_chromo_after,
    ):
        self.screen = screen
        self.farmer_score = farmer_score
        self.guard_score = guard_score
        self.animal_score = animal_score
        self.year = year

        # Evolution data (fitness before/after evolution)
        self.fox_before = fox_fitness_before
        self.rabbit_before = rabbit_fitness_before
        self.fox_after = fox_fitness_after
        self.rabbit_after = rabbit_fitness_after
        self.fox_chromo_after = fox_chromo_after
        self.rabbit_chromo_after = rabbit_chromo_after

        # Fonts
        self.font_title = pygame.font.Font(None, 44)
        self.font_large = pygame.font.Font(None, 30)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.font_tiny = pygame.font.Font(None, 14)

        # Colors
        self.bg_color = (18, 26, 18)
        self.panel_bg = (25, 35, 30)
        self.border_color = (100, 150, 100)
        self.title_color = (255, 215, 0)
        self.success_color = (100, 255, 100)
        self.warning_color = (255, 100, 100)
        self.text_color = (220, 220, 220)

        # Button dimensions
        btn_width = 160
        btn_height = 45
        spacing = 25
        total_width = btn_width * 3 + spacing * 2
        start_x = (SCREEN_W - total_width) // 2
        btn_y = SCREEN_H - 90

        self.continue_btn = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        self.restart_btn = pygame.Rect(
            start_x + btn_width + spacing, btn_y, btn_width, btn_height
        )
        self.menu_btn = pygame.Rect(
            start_x + (btn_width + spacing) * 2, btn_y, btn_width, btn_height
        )

    # ============================================================
    # DRAWING METHODS
    # ============================================================

    def draw(self):
        """Render the year end screen"""
        self.screen.fill(self.bg_color)

        # Title
        title = self.font_title.render(
            f"YEAR {self.year} COMPLETE!", True, self.title_color
        )
        title_rect = title.get_rect(center=(SCREEN_W // 2, 50))
        self.screen.blit(title, title_rect)

        subtitle = self.font_small.render(
            "Four seasons passed. Your farm continues...", True, self.text_color
        )
        sub_rect = subtitle.get_rect(center=(SCREEN_W // 2, 85))
        self.screen.blit(subtitle, sub_rect)

        # Scores Panel
        self._draw_scores_panel()

        # Evolution Panel
        self._draw_evolution_panel()

        # Buttons
        self._draw_buttons()

        # Year info
        year_info = self.font_small.render(
            f"Year {self.year} → Year {self.year + 1}", True, self.text_color
        )
        self.screen.blit(
            year_info, (SCREEN_W // 2 - year_info.get_width() // 2, SCREEN_H - 38)
        )

    def _draw_scores_panel(self):
        """Draw final scores panel with farmer, guard, and animal scores"""
        panel_rect = pygame.Rect(50, 110, SCREEN_W - 100, 85)
        pygame.draw.rect(self.screen, self.panel_bg, panel_rect, border_radius=12)
        pygame.draw.rect(
            self.screen, self.border_color, panel_rect, 2, border_radius=12
        )

        scores_title = self.font_medium.render("FINAL SCORES", True, self.title_color)
        self.screen.blit(
            scores_title, (SCREEN_W // 2 - scores_title.get_width() // 2, 120)
        )

        # Score cards
        card_w = 180
        card_h = 45
        card_y = 148
        cards_x = [
            SCREEN_W // 2 - card_w - 15,
            SCREEN_W // 2 - card_w // 2,
            SCREEN_W // 2 + 15,
        ]

        farmer_rect = pygame.Rect(cards_x[0], card_y, card_w, card_h)
        guard_rect = pygame.Rect(cards_x[1], card_y, card_w, card_h)
        animal_rect = pygame.Rect(cards_x[2], card_y, card_w, card_h)

        pygame.draw.rect(self.screen, (35, 45, 40), farmer_rect, border_radius=8)
        pygame.draw.rect(self.screen, (35, 45, 40), guard_rect, border_radius=8)
        pygame.draw.rect(self.screen, (35, 45, 40), animal_rect, border_radius=8)

        farmer_text = self.font_small.render(
            f"{self.farmer_score}", True, (100, 200, 100)
        )
        guard_text = self.font_small.render(
            f"{self.guard_score}", True, (255, 100, 100)
        )
        animal_text = self.font_small.render(
            f"{self.animal_score}", True, (255, 180, 100)
        )

        self.screen.blit(farmer_text, (farmer_rect.x + 15, farmer_rect.y + 12))
        self.screen.blit(guard_text, (guard_rect.x + 15, guard_rect.y + 12))
        self.screen.blit(animal_text, (animal_rect.x + 15, animal_rect.y + 12))

    def _draw_evolution_panel(self):
        """Draw evolution summary showing fitness changes for Fox and Rabbit"""
        panel_rect = pygame.Rect(50, 210, SCREEN_W - 100, 155)
        pygame.draw.rect(self.screen, self.panel_bg, panel_rect, border_radius=12)
        pygame.draw.rect(
            self.screen, self.border_color, panel_rect, 2, border_radius=12
        )

        evo_title = self.font_medium.render("EVOLUTION SUMMARY", True, self.title_color)
        self.screen.blit(evo_title, (SCREEN_W // 2 - evo_title.get_width() // 2, 222))

        # Fox fitness change
        fox_change = self.fox_after - self.fox_before
        fox_color = self.success_color if fox_change > 0 else self.warning_color
        fox_sign = "+" if fox_change > 0 else ""

        self.screen.blit(
            self.font_small.render("FOX:", True, (255, 130, 60)), (80, 258)
        )
        self.screen.blit(
            self.font_small.render(
                f"Fitness: {self.fox_before:.0f}", True, self.text_color
            ),
            (160, 258),
        )
        self.screen.blit(
            self.font_small.render("→", True, self.title_color), (280, 258)
        )
        self.screen.blit(
            self.font_small.render(f"{self.fox_after:.0f}", True, self.success_color),
            (310, 258),
        )
        self.screen.blit(
            self.font_small.render(f"({fox_sign}{fox_change:.0f})", True, fox_color),
            (380, 258),
        )

        # Rabbit fitness change
        rabbit_change = self.rabbit_after - self.rabbit_before
        rabbit_color = self.success_color if rabbit_change > 0 else self.warning_color
        rabbit_sign = "+" if rabbit_change > 0 else ""

        self.screen.blit(
            self.font_small.render("RABBIT:", True, (190, 140, 255)), (80, 285)
        )
        self.screen.blit(
            self.font_small.render(
                f"Fitness: {self.rabbit_before:.0f}", True, self.text_color
            ),
            (160, 285),
        )
        self.screen.blit(
            self.font_small.render("→", True, self.title_color), (280, 285)
        )
        self.screen.blit(
            self.font_small.render(
                f"{self.rabbit_after:.0f}", True, self.success_color
            ),
            (310, 285),
        )
        self.screen.blit(
            self.font_small.render(
                f"({rabbit_sign}{rabbit_change:.0f})", True, rabbit_color
            ),
            (380, 285),
        )

        # New chromosomes (Fox)
        if self.fox_chromo_after:
            c = self.fox_chromo_after
            self.screen.blit(
                self.font_tiny.render(
                    f"New Fox: Attr:{c.get('crop_attraction',0):.2f}  Avoid:{c.get('guard_avoidance',0):.2f}",
                    True,
                    (200, 200, 200),
                ),
                (80, 318),
            )
            self.screen.blit(
                self.font_tiny.render(
                    f"        Speed:{c.get('speed',0):.2f}  Bold:{c.get('boldness',0):.2f}",
                    True,
                    (200, 200, 200),
                ),
                (80, 335),
            )

    def _draw_buttons(self):
        """Draw interactive buttons (Continue, Restart, Main Menu)"""
        mouse_pos = pygame.mouse.get_pos()

        # Continue button
        continue_hover = self.continue_btn.collidepoint(mouse_pos)
        continue_color = (60, 140, 80) if continue_hover else (40, 100, 60)
        pygame.draw.rect(
            self.screen, continue_color, self.continue_btn, border_radius=10
        )
        pygame.draw.rect(
            self.screen, self.border_color, self.continue_btn, 2, border_radius=10
        )
        continue_text = self.font_medium.render("CONTINUE", True, self.title_color)
        self.screen.blit(
            continue_text, continue_text.get_rect(center=self.continue_btn.center)
        )

        # Restart button
        restart_hover = self.restart_btn.collidepoint(mouse_pos)
        restart_color = (140, 80, 60) if restart_hover else (100, 60, 40)
        pygame.draw.rect(self.screen, restart_color, self.restart_btn, border_radius=10)
        pygame.draw.rect(
            self.screen, self.border_color, self.restart_btn, 2, border_radius=10
        )
        restart_text = self.font_medium.render("RESTART", True, self.text_color)
        self.screen.blit(
            restart_text, restart_text.get_rect(center=self.restart_btn.center)
        )

        # Menu button
        menu_hover = self.menu_btn.collidepoint(mouse_pos)
        menu_color = (80, 80, 100) if menu_hover else (60, 60, 80)
        pygame.draw.rect(self.screen, menu_color, self.menu_btn, border_radius=10)
        pygame.draw.rect(
            self.screen, self.border_color, self.menu_btn, 2, border_radius=10
        )
        menu_text = self.font_medium.render("MAIN MENU", True, self.text_color)
        self.screen.blit(menu_text, menu_text.get_rect(center=self.menu_btn.center))

    # ============================================================
    # EVENT HANDLING
    # ============================================================

    def handle_event(self, event):
        """Process mouse clicks on buttons"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.continue_btn.collidepoint(event.pos):
                return "continue"
            if self.restart_btn.collidepoint(event.pos):
                return "restart"
            if self.menu_btn.collidepoint(event.pos):
                return "menu"
        return None
