"""
Genetic Algorithm Popup - Shows fitness, chromosomes, and evolution progress
Press G to view - displays both Fox and Rabbit data with lifetime fitness tracking
"""

import pygame
from utils.constants import SCREEN_W, SCREEN_H


class GAPopup:
    """Popup window displaying Genetic Algorithm evolution data for both animals"""

    def __init__(self, screen, animal_fox, animal_rabbit, season_manager):
        self.screen = screen
        self.fox = animal_fox
        self.rabbit = animal_rabbit
        self.season = season_manager
        self.visible = False
        self.evolution_history = []

        # Fonts (smaller to prevent text overlap)
        self.font_title = pygame.font.Font(None, 28)
        self.font_header = pygame.font.Font(None, 22)
        self.font_text = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 14)
        self.font_tiny = pygame.font.Font(None, 12)

        # Colors
        self.bg_color = (20, 28, 24)
        self.border_color = (120, 200, 90)
        self.title_color = (255, 215, 0)
        self.fox_color = (255, 130, 60)
        self.rabbit_color = (190, 140, 255)
        self.text_color = (210, 210, 210)
        self.success_color = (90, 230, 90)
        self.warning_color = (255, 190, 80)
        self.dim_color = (130, 130, 130)

        # Panel dimensions (centered)
        self.width = 700
        self.height = 580
        self.x = (SCREEN_W - self.width) // 2
        self.y = (SCREEN_H - self.height) // 2

        print(f"GA Popup ready ({self.width}x{self.height}) — press G to open")

    # ============================================================
    # DATA MANAGEMENT
    # ============================================================

    def toggle(self):
        """Show/hide the popup"""
        self.visible = not self.visible
        if self.visible:
            self._refresh_fitness()
            print("GA Popup opened")
        else:
            print("GA Popup closed")

    def _refresh_fitness(self):
        """Update fitness values from both animals"""
        if self.fox:
            self.fox.update_fitness()
        if self.rabbit:
            self.rabbit.update_fitness()

    def add_evolution_record(
        self, generation, fox_fitness, rabbit_fitness, fox_chromo, rabbit_chromo
    ):
        """Store evolution history for display"""
        self.evolution_history.append(
            {
                "generation": generation,
                "fox_fitness": fox_fitness,
                "rabbit_fitness": rabbit_fitness,
            }
        )
        if len(self.evolution_history) > 6:
            self.evolution_history.pop(0)
        print(f"Evolution record added — Generation {generation}")

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _draw_bar(self, x, y, w, h, value, max_value, color):
        """Draw a progress bar"""
        if max_value <= 0:
            max_value = 1
        filled = int(w * min(1.0, max(0.0, value / max_value)))
        pygame.draw.rect(self.screen, (55, 55, 65), (x, y, w, h), border_radius=4)
        if filled > 0:
            pygame.draw.rect(self.screen, color, (x, y, filled, h), border_radius=4)
        return filled

    def _draw_trait_bars(self, x, y, chromosome, color):
        """Draw 4 chromosome trait bars in compact format"""
        traits = [
            ("Crop Attr", "crop_attraction", 0.5, 2.0),
            ("Guard Avoid", "guard_avoidance", 0.5, 2.0),
            ("Speed", "speed", 1.0, 3.0),
            ("Boldness", "boldness", 0.5, 2.0),
        ]
        bar_w = 120

        for label, key, lo, hi in traits:
            val = chromosome.get(key, 1.0)
            norm = (val - lo) / (hi - lo)

            label_surf = self.font_tiny.render(label + ":", True, self.text_color)
            self.screen.blit(label_surf, (x, y))

            self._draw_bar(x + 75, y + 2, bar_w, 10, norm, 1.0, color)

            val_surf = self.font_tiny.render(f"{val:.2f}", True, self.title_color)
            self.screen.blit(val_surf, (x + 75 + bar_w + 5, y + 1))

            y += 18
        return y

    # ============================================================
    # MAIN DRAW METHOD
    # ============================================================

    def draw(self):
        """Render the GA popup window"""
        if not self.visible:
            return

        # Dim background
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Main panel
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.screen, self.bg_color, panel, border_radius=15)
        pygame.draw.rect(self.screen, self.border_color, panel, 2, border_radius=15)

        # Title
        title = self.font_title.render(
            "GENETIC ALGORITHM - ANIMAL EVOLUTION", True, self.title_color
        )
        self.screen.blit(
            title, title.get_rect(center=(self.x + self.width // 2, self.y + 28))
        )

        # Subtitle
        sub = self.font_small.render(
            "Animals evolve every Winter — fitness tracks ALL crops across entire year",
            True,
            self.dim_color,
        )
        self.screen.blit(
            sub, sub.get_rect(center=(self.x + self.width // 2, self.y + 52))
        )

        # Separator line
        pygame.draw.line(
            self.screen,
            self.border_color,
            (self.x + 15, self.y + 68),
            (self.x + self.width - 15, self.y + 68),
            1,
        )

        y = self.y + 78
        pad = 15
        inner_w = self.width - pad * 2

        # ===== SECTION 1: FITNESS SCORES =====
        bg1 = pygame.Rect(self.x + pad - 4, y - 4, inner_w + 8, 75)
        pygame.draw.rect(self.screen, (32, 42, 36), bg1, border_radius=8)

        header = self.font_header.render(
            "FITNESS SCORES (Lifetime)", True, self.title_color
        )
        self.screen.blit(header, (self.x + pad, y))
        y += 28

        fox_fit = self.fox.fitness if self.fox else 0
        rabbit_fit = self.rabbit.fitness if self.rabbit else 0
        max_fit = max(fox_fit, rabbit_fit, 1)
        bar_w = inner_w - 150

        # Fox fitness bar
        self.screen.blit(
            self.font_text.render("FOX:", True, self.fox_color), (self.x + pad, y)
        )
        self._draw_bar(
            self.x + pad + 70, y + 3, bar_w, 14, fox_fit, max_fit, self.fox_color
        )
        self.screen.blit(
            self.font_text.render(f"{fox_fit:.0f} pts", True, self.text_color),
            (self.x + pad + 70 + bar_w + 8, y),
        )
        y += 22

        # Rabbit fitness bar
        self.screen.blit(
            self.font_text.render("RABBIT:", True, self.rabbit_color), (self.x + pad, y)
        )
        self._draw_bar(
            self.x + pad + 70, y + 3, bar_w, 14, rabbit_fit, max_fit, self.rabbit_color
        )
        self.screen.blit(
            self.font_text.render(f"{rabbit_fit:.0f} pts", True, self.text_color),
            (self.x + pad + 70 + bar_w + 8, y),
        )
        y += 28

        # ===== SECTION 2: SEASON STATISTICS =====
        bg2 = pygame.Rect(self.x + pad - 4, y - 4, inner_w + 8, 80)
        pygame.draw.rect(self.screen, (32, 42, 36), bg2, border_radius=8)

        header = self.font_header.render("SEASON STATISTICS", True, self.title_color)
        self.screen.blit(header, (self.x + pad, y))
        y += 24

        if self.fox:
            self.screen.blit(
                self.font_small.render(
                    f"FOX - Gen: {self.fox.generation}  |  Lifetime Crops: {self.fox.lifetime_crops}  |  Survival: {self.fox.lifetime_survival//60}s",
                    True,
                    self.fox_color,
                ),
                (self.x + pad, y),
            )
            y += 18

        if self.rabbit:
            self.screen.blit(
                self.font_small.render(
                    f"RABBIT - Gen: {self.rabbit.generation}  |  Lifetime Crops: {self.rabbit.lifetime_crops}  |  Survival: {self.rabbit.lifetime_survival//60}s",
                    True,
                    self.rabbit_color,
                ),
                (self.x + pad, y),
            )
            y += 24

        # ===== SECTION 3: CHROMOSOMES (DNA Traits) =====
        bg3 = pygame.Rect(self.x + pad - 4, y - 4, inner_w + 8, 100)
        pygame.draw.rect(self.screen, (32, 42, 36), bg3, border_radius=8)

        header = self.font_header.render(
            "CHROMOSOMES (DNA Traits)", True, self.title_color
        )
        self.screen.blit(header, (self.x + pad, y))
        y += 22

        col_w = inner_w // 2 - 10

        # Fox DNA
        self.screen.blit(
            self.font_small.render("FOX DNA:", True, self.fox_color), (self.x + pad, y)
        )
        if self.fox:
            self._draw_trait_bars(
                self.x + pad + 10, y + 18, self.fox.chromosome, self.fox_color
            )

        # Rabbit DNA (right column)
        self.screen.blit(
            self.font_small.render("RABBIT DNA:", True, self.rabbit_color),
            (self.x + pad + col_w + 10, y),
        )
        if self.rabbit:
            self._draw_trait_bars(
                self.x + pad + col_w + 20,
                y + 18,
                self.rabbit.chromosome,
                self.rabbit_color,
            )

        y = self.y + self.height - 55

        # ===== SECTION 4: EVOLUTION INFO =====
        bg4 = pygame.Rect(self.x + pad - 4, y - 4, inner_w + 8, 48)
        pygame.draw.rect(self.screen, (32, 42, 36), bg4, border_radius=8)

        if self.season:
            seasons = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]
            season_icons = ["🌱", "☀️", "🍂", "❄️"]
            idx = self.season.index

            if idx == 3:
                self.screen.blit(
                    self.font_small.render(
                        f"{season_icons[idx]} {seasons[idx]} - Evolution at end of this season! Fitness uses ALL crops from whole year",
                        True,
                        self.warning_color,
                    ),
                    (self.x + pad, y),
                )
            else:
                self.screen.blit(
                    self.font_small.render(
                        f"{season_icons[idx]} {seasons[idx]} - Evolution happens at end of Winter. Fitness tracks ALL crops across entire year",
                        True,
                        self.dim_color,
                    ),
                    (self.x + pad, y),
                )

        # Close hint
        hint = self.font_text.render("Press G to close", True, self.title_color)
        hint_rect = hint.get_rect(
            center=(self.x + self.width // 2, self.y + self.height - 22)
        )
        pygame.draw.rect(
            self.screen, (40, 52, 44), hint_rect.inflate(20, 10), border_radius=8
        )
        self.screen.blit(hint, hint_rect)

    # ============================================================
    # EVENT HANDLING
    # ============================================================

    def handle_event(self, event):
        """Toggle popup on G key press"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            self.toggle()
            return True
        return False
