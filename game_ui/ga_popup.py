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

        # Fonts
        self.font_title  = pygame.font.Font(None, 36)
        self.font_header = pygame.font.Font(None, 26)
        self.font_label  = pygame.font.Font(None, 22)
        self.font_text   = pygame.font.Font(None, 20)
        self.font_small  = pygame.font.Font(None, 18)

        # Row heights derived from fonts (used for card sizing)
        self._RH_LABEL  = 26   # font_label row height
        self._RH_TEXT   = 22   # font_text row height
        self._RH_SMALL  = 20   # font_small row height
        self._CARD_PAD  = 10   # inner top/bottom padding per card
        self._SEC_GAP   = 8    # gap between cards

        # ── Color palette: dark teal/slate with amber + electric accents ──
        self.bg_color       = (12, 16, 22)          # near-black blue-slate
        self.card_color     = (20, 28, 38)           # slightly lighter slate
        self.card_color2    = (16, 24, 32)           # alternate card shade
        self.border_color   = (45, 120, 160)         # steel blue border
        self.accent_color   = (0, 180, 220)          # cyan accent
        self.title_color    = (255, 200, 60)         # warm amber
        self.fox_color      = (255, 120, 50)         # vivid orange
        self.rabbit_color   = (160, 110, 255)        # electric violet
        self.text_color     = (210, 218, 228)        # cool off-white
        self.dim_color      = (100, 112, 130)        # muted blue-grey
        self.success_color  = (60, 210, 140)         # teal green
        self.warning_color  = (255, 185, 50)         # amber warning
        self.divider_color  = (35, 55, 75)           # subtle divider

        # Panel — sized dynamically in draw(), set initial values here
        self.width  = 800
        self.height = 700       # will be recalculated
        self.x = (SCREEN_W - self.width) // 2
        self.y = (SCREEN_H - self.height) // 2


    # ============================================================
    # DATA MANAGEMENT
    # ============================================================

    def toggle(self):
        """Show/hide the popup"""
        self.visible = not self.visible
        if self.visible:
            self._refresh_fitness()

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

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _draw_card(self, x, y, w, h, alt=False):
        """Rounded card with border"""
        col = self.card_color2 if alt else self.card_color
        pygame.draw.rect(self.screen, col, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, self.divider_color, (x, y, w, h), 1, border_radius=8)

    def _draw_bar(self, x, y, w, h, value, max_value, color, show_pct=False):
        """Polished progress bar; optionally show % label inside"""
        if max_value <= 0:
            max_value = 1
        pct    = min(1.0, max(0.0, value / max_value))
        filled = int(w * pct)
        # track
        pygame.draw.rect(self.screen, (25, 38, 52), (x, y, w, h), border_radius=h // 2)
        # fill
        if filled > 0:
            pygame.draw.rect(self.screen, color, (x, y, filled, h), border_radius=h // 2)
            # subtle highlight strip
            hl = pygame.Surface((filled, max(1, h // 3)), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 30))
            self.screen.blit(hl, (x, y))
        # border
        pygame.draw.rect(self.screen, self.divider_color, (x, y, w, h), 1, border_radius=h // 2)
        if show_pct and h >= 12:
            lbl = self.font_small.render(f"{int(pct*100)}%", True, (200, 210, 220))
            self.screen.blit(lbl, (x + w + 6, y - 1))
        return filled

    def _draw_section_header(self, x, y, w, text):
        """Header with left-side accent pip and bottom divider"""
        pygame.draw.rect(self.screen, self.accent_color, (x, y + 2, 4, 20), border_radius=2)
        surf = self.font_header.render(text, True, self.title_color)
        self.screen.blit(surf, (x + 12, y))
        line_y = y + 28
        pygame.draw.line(self.screen, self.divider_color, (x, line_y), (x + w, line_y), 1)
        return line_y + 6   # return y-cursor below divider

    def _draw_kv_row(self, x, y, key, value, val_color=None, font_key=None, font_val=None):
        """Draw  KEY:  VALUE  on one row, returns row height used"""
        fk = font_key  or self.font_small
        fv = font_val  or self.font_label
        vc = val_color or self.text_color
        ks = fk.render(key + ":", True, self.dim_color)
        vs = fv.render(str(value), True, vc)
        self.screen.blit(ks, (x, y + 2))
        self.screen.blit(vs, (x + ks.get_width() + 8, y))
        return max(ks.get_height(), vs.get_height()) + 4

    def _draw_trait_bars(self, x, y, w, chromosome, color):
        """4 trait bars that fit exactly inside width w"""
        traits = [
            ("Crop Attr",   "crop_attraction", 0.5, 2.0),
            ("Guard Avoid", "guard_avoidance", 0.5, 2.0),
            ("Speed",       "speed",           1.0, 3.0),
            ("Boldness",    "boldness",         0.5, 2.0),
        ]
        LABEL_W = 76
        VAL_W   = 36
        bar_w   = w - LABEL_W - VAL_W - 10
        bar_w   = max(bar_w, 40)

        for label, key, lo, hi in traits:
            val  = chromosome.get(key, 1.0)
            norm = max(0.0, min(1.0, (val - lo) / (hi - lo)))

            lbl = self.font_small.render(label + ":", True, self.dim_color)
            self.screen.blit(lbl, (x, y + 2))

            self._draw_bar(x + LABEL_W, y + 4, bar_w, 13, norm, 1.0, color)

            vs = self.font_small.render(f"{val:.2f}", True, self.text_color)
            self.screen.blit(vs, (x + LABEL_W + bar_w + 6, y + 2))
            y += self._RH_SMALL + 2
        return y

    # ============================================================
    # SECTION HEIGHT CALCULATORS  (no drawing — just arithmetic)
    # ============================================================

    def _h_fitness(self):
        """Height needed: header(34) + 2 rows(label) + pad"""
        return 34 + 2 * (self._RH_LABEL + 4) + self._CARD_PAD * 2

    def _h_stats(self):
        """Height for the two side-by-side stat cards"""
        # header(22) + 3 kv-rows + pad
        return 22 + 3 * (self._RH_SMALL + 4) + self._CARD_PAD * 2 + 4

    def _h_chromosomes(self):
        """Height for DNA section: header + sub-header + 4 trait rows + pad"""
        return 34 + self._RH_LABEL + 4 * (self._RH_SMALL + 2) + self._CARD_PAD * 2

    def _h_evolution(self):
        """Height for evolution history card (only shown if data exists)"""
        return 34 + 2 * (self._RH_SMALL + 2) + self._CARD_PAD

    def _h_season(self):
        return self._RH_SMALL + self._CARD_PAD * 2

    # ============================================================
    # MAIN DRAW METHOD
    # ============================================================

    def draw(self):
        """Render the GA popup window"""
        if not self.visible:
            return

        # ── compute total panel height bottom-up ────────────────
        TITLE_H  = 82    # title bar + subtitle + divider
        CLOSE_H  = 34    # close hint at bottom
        PAD      = 16    # left/right inner padding

        sec_heights = [
            self._h_fitness(),
            self._h_stats(),
            self._h_chromosomes(),
        ]
        if self.evolution_history:
            sec_heights.append(self._h_evolution())
        if self.season:
            sec_heights.append(self._h_season())

        inner_h = sum(sec_heights) + self._SEC_GAP * len(sec_heights)
        total_h = TITLE_H + inner_h + CLOSE_H + 10

        # clamp to screen
        total_h = min(total_h, SCREEN_H - 20)
        self.height = total_h
        self.y      = (SCREEN_H - self.height) // 2

        # ── dim overlay ─────────────────────────────────────────
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # ── main panel ──────────────────────────────────────────
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.screen, self.bg_color,     panel, border_radius=14)
        pygame.draw.rect(self.screen, self.border_color, panel, 2, border_radius=14)

        # ── title bar ───────────────────────────────────────────
        tbar = pygame.Rect(self.x, self.y, self.width, 52)
        pygame.draw.rect(self.screen, (10, 18, 30), tbar,
                         border_top_left_radius=14, border_top_right_radius=14)
        pygame.draw.rect(self.screen, self.border_color, tbar, 2,
                         border_top_left_radius=14, border_top_right_radius=14)

        # cyan side-pips on title
        pygame.draw.rect(self.screen, self.accent_color,
                         (self.x + 12, self.y + 16, 4, 22), border_radius=2)
        pygame.draw.rect(self.screen, self.accent_color,
                         (self.x + self.width - 16, self.y + 16, 4, 22), border_radius=2)

        title = self.font_title.render("GENETIC ALGORITHM  —  ANIMAL EVOLUTION",
                                       True, self.title_color)
        self.screen.blit(title, title.get_rect(
            center=(self.x + self.width // 2, self.y + 26)))

        # subtitle
        sub = self.font_small.render(
            "Animals evolve every Winter  ·  Fitness accumulates across the entire year",
            True, self.dim_color)
        self.screen.blit(sub, sub.get_rect(
            center=(self.x + self.width // 2, self.y + 64)))
        pygame.draw.line(self.screen, self.divider_color,
                         (self.x + PAD, self.y + 76),
                         (self.x + self.width - PAD, self.y + 76), 1)

        cx = self.x + PAD
        cw = self.width - PAD * 2
        y  = self.y + TITLE_H

        # ══════════════════════════════════════════════════════════
        # SECTION 1 — FITNESS SCORES
        # ══════════════════════════════════════════════════════════
        sh = self._h_fitness()
        self._draw_card(cx, y, cw, sh)
        hy = self._draw_section_header(cx + 8, y + self._CARD_PAD, cw - 16, "FITNESS SCORES  (Lifetime)")

        fox_fit    = self.fox.fitness    if self.fox    else 0
        rabbit_fit = self.rabbit.fitness if self.rabbit else 0
        max_fit    = max(fox_fit, rabbit_fit, 1)
        bar_w      = cw - 180

        # Fox row
        fox_lbl = self.font_label.render("FOX", True, self.fox_color)
        self.screen.blit(fox_lbl, (cx + 10, hy))
        self._draw_bar(cx + 78, hy + 5, bar_w, 16, fox_fit, max_fit, self.fox_color)
        self.screen.blit(
            self.font_label.render(f"{fox_fit:.0f} pts", True, self.text_color),
            (cx + 78 + bar_w + 10, hy))
        hy += self._RH_LABEL + 4

        # Rabbit row
        rab_lbl = self.font_label.render("RABBIT", True, self.rabbit_color)
        self.screen.blit(rab_lbl, (cx + 10, hy))
        self._draw_bar(cx + 78, hy + 5, bar_w, 16, rabbit_fit, max_fit, self.rabbit_color)
        self.screen.blit(
            self.font_label.render(f"{rabbit_fit:.0f} pts", True, self.text_color),
            (cx + 78 + bar_w + 10, hy))

        y += sh + self._SEC_GAP

        # ══════════════════════════════════════════════════════════
        # SECTION 2 — SEASON STATISTICS (side-by-side)
        # ══════════════════════════════════════════════════════════
        sh   = self._h_stats()
        half = (cw - 8) // 2

        # Fox card
        self._draw_card(cx, y, half, sh)
        pygame.draw.rect(self.screen, self.fox_color,
                         (cx + 8, y + 10, 4, 20), border_radius=2)
        self.screen.blit(self.font_header.render("FOX", True, self.fox_color),
                         (cx + 20, y + 8))
        sy = y + 8 + 22 + 4
        if self.fox:
            fox_stats = [
                ("Generation",    self.fox.generation),
                ("Crops Eaten",   self.fox.lifetime_crops),
                ("Survival Time", f"{self.fox.lifetime_survival // 60}s"),
            ]
            for k, v in fox_stats:
                sy += self._draw_kv_row(cx + 12, sy, k, v)

        # Rabbit card
        rx = cx + half + 8
        self._draw_card(rx, y, half, sh)
        pygame.draw.rect(self.screen, self.rabbit_color,
                         (rx + 8, y + 10, 4, 20), border_radius=2)
        self.screen.blit(self.font_header.render("RABBIT", True, self.rabbit_color),
                         (rx + 20, y + 8))
        sy = y + 8 + 22 + 4
        if self.rabbit:
            rab_stats = [
                ("Generation",    self.rabbit.generation),
                ("Crops Eaten",   self.rabbit.lifetime_crops),
                ("Survival Time", f"{self.rabbit.lifetime_survival // 60}s"),
            ]
            for k, v in rab_stats:
                sy += self._draw_kv_row(rx + 12, sy, k, v)

        y += sh + self._SEC_GAP

        # ══════════════════════════════════════════════════════════
        # SECTION 3 — CHROMOSOMES / DNA TRAITS
        # ══════════════════════════════════════════════════════════
        sh = self._h_chromosomes()
        self._draw_card(cx, y, cw, sh, alt=True)
        hy = self._draw_section_header(cx + 8, y + self._CARD_PAD, cw - 16, "CHROMOSOMES  (DNA Traits)")

        dna_w    = (cw - 20) // 2   # width available per column
        dna_bar  = dna_w - 130       # bar width inside each column

        # Fox DNA col
        self.screen.blit(self.font_label.render("FOX  DNA", True, self.fox_color),
                         (cx + 10, hy))
        if self.fox:
            self._draw_trait_bars(cx + 10, hy + self._RH_LABEL + 2,
                                  dna_w - 10, self.fox.chromosome, self.fox_color)

        # vertical divider
        div_x = cx + dna_w + 10
        pygame.draw.line(self.screen, self.divider_color,
                         (div_x, y + 10), (div_x, y + sh - 10), 1)

        # Rabbit DNA col
        self.screen.blit(self.font_label.render("RABBIT  DNA", True, self.rabbit_color),
                         (div_x + 10, hy))
        if self.rabbit:
            self._draw_trait_bars(div_x + 10, hy + self._RH_LABEL + 2,
                                  dna_w - 10, self.rabbit.chromosome, self.rabbit_color)

        y += sh + self._SEC_GAP

        # ══════════════════════════════════════════════════════════
        # SECTION 4 — EVOLUTION HISTORY  (only if data exists)
        # ══════════════════════════════════════════════════════════
        if self.evolution_history:
            sh = self._h_evolution()
            self._draw_card(cx, y, cw, sh)
            hy = self._draw_section_header(cx + 8, y + self._CARD_PAD,
                                           cw - 16, "EVOLUTION HISTORY")
            n       = len(self.evolution_history)
            spacing = min((cw - 30) // max(n, 1), 120)
            dot_x   = cx + 16
            for rec in self.evolution_history:
                gen = rec["generation"]
                ff  = rec["fox_fitness"]
                rf  = rec["rabbit_fitness"]
                pygame.draw.circle(self.screen, self.fox_color,    (dot_x + 5, hy + 5),  5)
                self.screen.blit(
                    self.font_small.render(f"G{gen}:{ff:.0f}", True, self.fox_color),
                    (dot_x, hy + 13))
                pygame.draw.circle(self.screen, self.rabbit_color, (dot_x + 5, hy + 27), 5)
                self.screen.blit(
                    self.font_small.render(f"{rf:.0f}", True, self.rabbit_color),
                    (dot_x, hy + 35))
                dot_x += spacing
            y += sh + self._SEC_GAP

        # ══════════════════════════════════════════════════════════
        # SECTION 5 — CURRENT SEASON STATUS
        # ══════════════════════════════════════════════════════════
        if self.season:
            sh = self._h_season()
            self._draw_card(cx, y, cw, sh)
            seasons      = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]
            season_icons = [">> Spring", ">> Summer", ">> Autumn", ">> WINTER"]
            idx       = self.season.index
            is_winter = idx == 3
            color     = self.warning_color if is_winter else self.dim_color
            msg = (
                f"{season_icons[idx]}  —  Evolution triggers NOW at end of this season!  Fitness uses ALL crops from entire year."
                if is_winter else
                f"{season_icons[idx]}  —  Evolution happens at end of Winter.  Fitness accumulates all year."
            )
            lbl = self.font_small.render(msg, True, color)
            self.screen.blit(lbl, (cx + 12,
                                   y + (sh - lbl.get_height()) // 2))

        # ── close hint ──────────────────────────────────────────
        hint = self.font_label.render("Press  G  to close", True, self.title_color)
        hr   = hint.get_rect(center=(self.x + self.width // 2, self.y + self.height - 18))
        pygame.draw.rect(self.screen, (15, 28, 42),   hr.inflate(28, 12), border_radius=8)
        pygame.draw.rect(self.screen, self.border_color, hr.inflate(28, 12), 1, border_radius=8)
        self.screen.blit(hint, hr)

    # ============================================================
    # EVENT HANDLING
    # ============================================================

    def handle_event(self, event):
        """Toggle popup on G key press"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            self.toggle()
            return True
        return False
