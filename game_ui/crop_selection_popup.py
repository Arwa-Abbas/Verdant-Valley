"""
Crop Selection Popup - Shown when all crops are harvested
Options: Auto Plant (CSP generates layout) or Manual Select (user chooses crop type and quantity)
"""

import pygame
from utils.constants import (
    SCREEN_W,
    SCREEN_H,
    CROP_WHEAT,
    CROP_SUNFLOWER,
    CROP_CORN,
    CROP_TOMATO,
    CROP_CARROT,
)

# Crop catalogue for manual selection mode
CROP_OPTIONS = [
    (CROP_WHEAT, "Wheat", "🌾", (220, 200, 100)),
    (CROP_SUNFLOWER, "Sunflower", "🌻", (255, 210, 50)),
    (CROP_CORN, "Corn", "🌽", (255, 230, 80)),
    (CROP_TOMATO, "Tomato", "🍅", (230, 70, 70)),
    (CROP_CARROT, "Carrot", "🥕", (255, 140, 40)),
]

MIN_CROPS = 1
MAX_CROPS = 12


class CropSelectionPopup:
    """
    Modal popup that appears when field is empty.
    Returns: None | "auto" | ("manual", crop_id, count)
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.result = None
        self._phase = "choose"  # "choose" or "manual"

        # Manual selection state
        self._selected_crop_idx = 0
        self._crop_count = 4

        # Fonts
        self._f_title = pygame.font.Font(None, 46)
        self._f_head = pygame.font.Font(None, 30)
        self._f_body = pygame.font.Font(None, 24)
        self._f_small = pygame.font.Font(None, 20)

        # Animation
        self._alpha = 0
        self._overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Panel dimensions
        self._pw = 560
        self._ph_choose = 260
        self._ph_manual = 420
        self._px = (SCREEN_W - self._pw) // 2

        # Button rects (recreated each draw)
        self._btn_auto = pygame.Rect(0, 0, 0, 0)
        self._btn_manual = pygame.Rect(0, 0, 0, 0)
        self._btn_confirm = pygame.Rect(0, 0, 0, 0)
        self._btn_back = pygame.Rect(0, 0, 0, 0)
        self._crop_rects = []
        self._btn_minus = pygame.Rect(0, 0, 0, 0)
        self._btn_plus = pygame.Rect(0, 0, 0, 0)

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def update(self) -> bool:
        """Called each frame. Returns True when popup is finished."""
        self._alpha = min(255, self._alpha + 18)
        return self.result is not None

    def handle_event(self, event: pygame.event.Event):
        """Process mouse and keyboard input."""
        if self.result is not None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_click(event.pos)

        if event.type == pygame.KEYDOWN:
            self._handle_keyboard(event)

    def draw(self):
        """Render the popup."""
        self._overlay.fill((0, 0, 0, min(160, self._alpha)))
        self.screen.blit(self._overlay, (0, 0))

        if self._phase == "choose":
            self._draw_choose_phase()
        else:
            self._draw_manual_phase()

    # ============================================================
    # EVENT HANDLERS
    # ============================================================

    def _handle_mouse_click(self, pos):
        """Process mouse clicks on buttons."""
        if self._phase == "choose":
            if self._btn_auto.collidepoint(pos):
                self.result = "auto"
            elif self._btn_manual.collidepoint(pos):
                self._phase = "manual"

        elif self._phase == "manual":
            # Crop selection cards
            for i, rect in enumerate(self._crop_rects):
                if rect.collidepoint(pos):
                    self._selected_crop_idx = i

            # Count adjustment buttons
            if self._btn_minus.collidepoint(pos):
                self._crop_count = max(MIN_CROPS, self._crop_count - 1)
            if self._btn_plus.collidepoint(pos):
                self._crop_count = min(MAX_CROPS, self._crop_count + 1)

            # Confirm/Back buttons
            if self._btn_confirm.collidepoint(pos):
                crop_id = CROP_OPTIONS[self._selected_crop_idx][0]
                self.result = ("manual", crop_id, self._crop_count)
            if self._btn_back.collidepoint(pos):
                self._phase = "choose"

    def _handle_keyboard(self, event):
        """Process keyboard input in manual mode."""
        if self._phase == "manual":
            if event.key == pygame.K_LEFT:
                self._crop_count = max(MIN_CROPS, self._crop_count - 1)
            if event.key == pygame.K_RIGHT:
                self._crop_count = min(MAX_CROPS, self._crop_count + 1)
            if event.key == pygame.K_RETURN:
                crop_id = CROP_OPTIONS[self._selected_crop_idx][0]
                self.result = ("manual", crop_id, self._crop_count)

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _panel_y(self, ph):
        return (SCREEN_H - ph) // 2

    def _draw_panel(self, ph):
        """Draw main panel background with shadow."""
        py = self._panel_y(ph)

        # Drop shadow
        shadow = pygame.Rect(self._px + 6, py + 6, self._pw, ph)
        pygame.draw.rect(self.screen, (0, 0, 0, 120), shadow, border_radius=18)

        # Main panel
        panel_rect = pygame.Rect(self._px, py, self._pw, ph)
        pygame.draw.rect(self.screen, (22, 30, 22), panel_rect, border_radius=18)
        pygame.draw.rect(self.screen, (90, 140, 90), panel_rect, 2, border_radius=18)
        return py

    def _draw_title(self, py, text, sub=None):
        """Draw title and optional subtitle."""
        t = self._f_title.render(text, True, (255, 215, 0))
        tr = t.get_rect(centerx=SCREEN_W // 2, top=py + 22)
        self.screen.blit(t, tr)

        if sub:
            s = self._f_small.render(sub, True, (160, 200, 160))
            sr = s.get_rect(centerx=SCREEN_W // 2, top=tr.bottom + 4)
            self.screen.blit(s, sr)
            return sr.bottom
        return tr.bottom

    def _wood_button(self, rect, label, hovered=False, disabled=False):
        """Draw wooden-style button."""
        base = (
            (80, 80, 80) if disabled else (140, 105, 65) if hovered else (100, 70, 40)
        )
        border = (110, 110, 110) if disabled else (80, 150, 80)
        text_color = (150, 150, 150) if disabled else (255, 215, 0)

        pygame.draw.rect(self.screen, base, rect, border_radius=10)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=10)

        label_surf = self._f_body.render(label, True, text_color)
        self.screen.blit(label_surf, label_surf.get_rect(center=rect.center))

    # ============================================================
    # PHASE DRAWING METHODS
    # ============================================================

    def _draw_choose_phase(self):
        """Draw the initial choice screen (Auto vs Manual)."""
        ph = self._ph_choose
        py = self._draw_panel(ph)
        bottom = self._draw_title(
            py, "Field is Empty!", "All crops have been harvested."
        )

        mouse_pos = pygame.mouse.get_pos()
        btn_w, btn_h = 200, 56
        gap = 24
        total = btn_w * 2 + gap
        start_x = SCREEN_W // 2 - total // 2
        btn_y = bottom + 28

        self._btn_auto = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self._btn_manual = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        self._wood_button(
            self._btn_auto, "Auto Plant", self._btn_auto.collidepoint(mouse_pos)
        )
        self._wood_button(
            self._btn_manual, "Manual Select", self._btn_manual.collidepoint(mouse_pos)
        )

        # Captions
        auto_caption = self._f_small.render(
            "CSP generates the layout", True, (130, 170, 130)
        )
        manual_caption = self._f_small.render(
            "You choose crop & count", True, (130, 170, 130)
        )

        self.screen.blit(
            auto_caption,
            auto_caption.get_rect(
                centerx=self._btn_auto.centerx, top=self._btn_auto.bottom + 6
            ),
        )
        self.screen.blit(
            manual_caption,
            manual_caption.get_rect(
                centerx=self._btn_manual.centerx, top=self._btn_manual.bottom + 6
            ),
        )

    def _draw_manual_phase(self):
        """Draw the manual crop selection screen."""
        ph = self._ph_manual
        py = self._draw_panel(ph)
        bottom = self._draw_title(py, "Choose Your Crop")

        mouse_pos = pygame.mouse.get_pos()

        # Crop selection cards
        card_w, card_h = 78, 78
        cols = len(CROP_OPTIONS)
        spacing = 14
        row_w = cols * card_w + (cols - 1) * spacing
        start_x = SCREEN_W // 2 - row_w // 2
        card_y = bottom + 18

        self._crop_rects = []
        for i, (_, name, emoji, color) in enumerate(CROP_OPTIONS):
            rect = pygame.Rect(start_x + i * (card_w + spacing), card_y, card_w, card_h)
            self._crop_rects.append(rect)

            selected = i == self._selected_crop_idx
            hovered = rect.collidepoint(mouse_pos)

            bg_color = (40, 55, 40) if not selected else (30, 60, 30)
            border_color = (
                color if selected else ((80, 120, 80) if hovered else (50, 70, 50))
            )
            border_width = 3 if selected else 1

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(
                self.screen, border_color, rect, border_width, border_radius=10
            )

            # Emoji icon
            emoji_surf = self._f_head.render(emoji, True, color)
            self.screen.blit(
                emoji_surf, emoji_surf.get_rect(centerx=rect.centerx, top=rect.top + 10)
            )

            # Crop name
            name_color = color if selected else (170, 190, 170)
            name_surf = self._f_small.render(name, True, name_color)
            self.screen.blit(
                name_surf,
                name_surf.get_rect(centerx=rect.centerx, bottom=rect.bottom - 8),
            )

        # Count selector
        count_y = card_y + card_h + 24
        label = self._f_head.render("How many crops?", True, (200, 210, 200))
        self.screen.blit(label, label.get_rect(centerx=SCREEN_W // 2, top=count_y))

        btn_size = 36
        center_y = count_y + 40

        self._btn_minus = pygame.Rect(
            SCREEN_W // 2 - 80 - btn_size, center_y, btn_size, btn_size
        )
        self._btn_plus = pygame.Rect(SCREEN_W // 2 + 80, center_y, btn_size, btn_size)

        for btn, symbol in ((self._btn_minus, "-"), (self._btn_plus, "+")):
            hovered = btn.collidepoint(mouse_pos)
            color = (60, 90, 60) if hovered else (40, 60, 40)
            pygame.draw.rect(self.screen, color, btn, border_radius=8)
            pygame.draw.rect(self.screen, (100, 160, 100), btn, 2, border_radius=8)
            symbol_surf = self._f_head.render(symbol, True, (255, 215, 0))
            self.screen.blit(symbol_surf, symbol_surf.get_rect(center=btn.center))

        # Count display
        count_surf = self._f_title.render(str(self._crop_count), True, (255, 215, 0))
        self.screen.blit(
            count_surf,
            count_surf.get_rect(
                centerx=SCREEN_W // 2, centery=center_y + btn_size // 2
            ),
        )

        # Hint text
        hint = self._f_small.render("← → or buttons to adjust", True, (120, 150, 120))
        self.screen.blit(
            hint, hint.get_rect(centerx=SCREEN_W // 2, top=center_y + btn_size + 6)
        )

        # Confirm/Back buttons
        action_y = center_y + btn_size + 36
        btn_w, btn_h = 170, 50
        gap = 20
        start_x = SCREEN_W // 2 - btn_w - gap // 2

        self._btn_back = pygame.Rect(start_x, action_y, btn_w, btn_h)
        self._btn_confirm = pygame.Rect(start_x + btn_w + gap, action_y, btn_w, btn_h)

        self._wood_button(
            self._btn_back, "Back", self._btn_back.collidepoint(mouse_pos)
        )
        self._wood_button(
            self._btn_confirm,
            "Start Planting",
            self._btn_confirm.collidepoint(mouse_pos),
        )
