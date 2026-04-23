"""
Algorithm Visualizer - Shows A* node expansion, CSP backtracking, and real-time metrics
Toggles with TAB key, node overlay with N key
"""

import pygame
from utils.constants import *
from utils.helpers import grid_to_px


class AlgorithmVisualizer:
    """Visualization panel for A* pathfinding and CSP backtracking algorithms"""

    def __init__(self, screen, grid):
        self.screen = screen
        self.grid = grid
        self.visible = True
        self.show_node_overlay = True
        self.flash_timer = 0

        # Fonts
        self.font = pygame.font.Font(None, 16)
        self.font_title = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 12)

        # Panel dimensions
        self.panel_width = 350
        self.panel_height = 700
        self.panel_x = SCREEN_W - self.panel_width - 10
        self.panel_y = 10

        # A* tracking data for all agents
        self.farmer_nodes = []
        self.guard_nodes = []
        self.animal_nodes = []
        self.farmer_expanded = 0
        self.guard_expanded = 0
        self.animal_expanded = 0
        self.farmer_cost = 0
        self.guard_cost = 0
        self.animal_cost = 0

        # CSP tracking data
        self.csp_assignments = {}
        self.csp_backtracks = 0
        self.csp_domains = {}

        # Agent display colors (yellow, orange, red)
        self.agent_colors = {
            "farmer": (255, 255, 0),
            "guard": (255, 165, 0),
            "animal": (255, 100, 100),
        }

        print(
            "AlgorithmVisualizer initialized - TAB to toggle panel, N for node overlay"
        )

    # ============================================================
    # DATA UPDATE METHODS
    # ============================================================

    def update_astar_data(self, farmer, guard, animal_fox, animal_rabbit):
        """Collect A* exploration data from all agents"""
        if farmer:
            self.farmer_nodes = getattr(farmer, "last_explored_nodes", [])
            self.farmer_expanded = getattr(farmer, "nodes_expanded", 0)
            self.farmer_cost = getattr(farmer, "path_cost", 0)

        if guard:
            self.guard_nodes = getattr(guard, "last_explored_nodes", [])
            self.guard_expanded = getattr(guard, "nodes_expanded", 0)
            self.guard_cost = getattr(guard, "path_cost", 0)

        # Merge animal data (Fox + Rabbit)
        self.animal_nodes = []
        self.animal_expanded = 0
        self.animal_cost = 0

        if animal_fox:
            self.animal_nodes.extend(getattr(animal_fox, "last_explored_nodes", []))
            self.animal_expanded += getattr(animal_fox, "nodes_expanded", 0)
            self.animal_cost += getattr(animal_fox, "path_cost", 0)

        if animal_rabbit:
            self.animal_nodes.extend(getattr(animal_rabbit, "last_explored_nodes", []))
            self.animal_expanded += getattr(animal_rabbit, "nodes_expanded", 0)
            self.animal_cost += getattr(animal_rabbit, "path_cost", 0)

        self.animal_nodes = self.animal_nodes[-100:]

    def update_csp_data(self, csp_solver):
        """Collect CSP backtracking and domain data"""
        if csp_solver:
            self.csp_assignments = getattr(csp_solver, "assign", {})
            self.csp_backtracks = len(getattr(csp_solver, "backtrack_log", []))
            self.csp_domains = getattr(csp_solver, "domains", {})

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _draw_section(self, x, y, title, height, color=(80, 150, 80)):
        """Draw a bordered section with title bar"""
        panel_rect = pygame.Rect(x, y, self.panel_width - 20, height)
        pygame.draw.rect(self.screen, (30, 40, 50), panel_rect)
        pygame.draw.rect(self.screen, color, panel_rect, 2)

        title_bar = pygame.Rect(x, y, self.panel_width - 20, 22)
        pygame.draw.rect(self.screen, (50, 70, 50), title_bar)
        title_text = self.font_title.render(title, True, (255, 215, 0))
        self.screen.blit(title_text, (x + 8, y + 4))

    def _draw_agent_row(self, x, y, name, color, node_count, path_cost):
        """Draw single agent stats row"""
        name_text = self.font.render(name, True, color)
        self.screen.blit(name_text, (x + 10, y))

        nodes_text = self.font.render(f"Nodes: {node_count}", True, (200, 200, 200))
        self.screen.blit(nodes_text, (x + 130, y))

        cost_text = self.font.render(f"Cost: {path_cost:.1f}", True, (200, 200, 200))
        self.screen.blit(cost_text, (x + 230, y))

    def _draw_bar(self, x, y, width, height, value, max_val, color):
        """Draw a progress bar"""
        if max_val <= 0:
            max_val = 1
        fill = int(width * min(1.0, value / max_val))

        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, width, height))
        if fill > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill, height))

    # ============================================================
    # PANEL SECTIONS
    # ============================================================

    def _draw_astar_section(self, x, y):
        """Display A* node expansion statistics for all agents"""
        self._draw_section(x, y, "A* PATHFINDING", 185)
        y_start = y + 26
        line_h = 22

        self._draw_agent_row(
            x,
            y_start,
            "FARMER",
            self.agent_colors["farmer"],
            self.farmer_expanded,
            self.farmer_cost,
        )
        y_start += line_h

        self._draw_agent_row(
            x,
            y_start,
            "GUARD",
            self.agent_colors["guard"],
            self.guard_expanded,
            self.guard_cost,
        )
        y_start += line_h

        self._draw_agent_row(
            x,
            y_start,
            "ANIMAL",
            self.agent_colors["animal"],
            self.animal_expanded,
            self.animal_cost,
        )

        # Color legend
        legend = self.font_small.render(
            "Colors: Yellow=Farmer Orange=Guard Red=Animal", True, (180, 180, 180)
        )
        self.screen.blit(legend, (x + 10, y_start + line_h + 5))

        return y + 185 + 5

    def _draw_csp_section(self, x, y):
        """Display CSP backtracking statistics and domain progress"""
        self._draw_section(x, y, "CSP BACKTRACKING", 160)
        y_start = y + 26

        # Stats
        assign_count = len([c for c in self.csp_assignments.values() if c != CROP_NONE])
        self.screen.blit(
            self.font.render(f"Assignments: {assign_count}", True, (200, 200, 200)),
            (x + 10, y_start),
        )
        self.screen.blit(
            self.font.render(
                f"Backtracks: {self.csp_backtracks}", True, (200, 200, 200)
            ),
            (x + 150, y_start),
        )

        # Domain display (first 4 variables only)
        y_start += 22
        self.screen.blit(
            self.font.render("Remaining Domains:", True, (150, 200, 150)),
            (x + 10, y_start),
        )

        y_start += 20
        for i, (var, domain) in enumerate(list(self.csp_domains.items())[:4]):
            if isinstance(var, tuple):
                col, row = var
                crops = [
                    CROP_NAMES.get(c, str(c))[:2] for c in domain if c != CROP_NONE
                ]
                if crops:
                    text = self.font_small.render(
                        f"({col},{row}): {', '.join(crops[:3])}", True, (200, 200, 150)
                    )
                    self.screen.blit(text, (x + 15, y_start + (i * 16)))

        # Backtrack flash indicator
        if self.flash_timer > 0:
            flash = self.font.render("BACKTRACK!", True, (255, 100, 100))
            self.screen.blit(flash, (x + 10, y + 160 - 20))

        return y + 160 + 5

    def _draw_metrics_section(self, x, y, farmer_score, guard_score, animal_score, fps):
        """Display live game metrics"""
        self._draw_section(x, y, "LIVE METRICS", 105)
        y_start = y + 26
        line_h = 20

        metrics = [
            (f"Farmer: {farmer_score}", self.agent_colors["farmer"]),
            (f"Guard: {guard_score}", self.agent_colors["guard"]),
            (f"Animal: {animal_score}", self.agent_colors["animal"]),
            (f"FPS: {fps}", (150, 150, 255)),
        ]

        for i, (text, color) in enumerate(metrics):
            rendered = self.font.render(text, True, color)
            self.screen.blit(rendered, (x + 10, y_start + (i * line_h)))

        return y + 105 + 5

    def _draw_legend_section(self, x, y):
        """Display color legend for visualizations"""
        self._draw_section(x, y, "LEGEND", 70, (100, 150, 100))
        y_start = y + 26

        legends = [
            ("Yellow", "Farmer Nodes"),
            ("Orange", "Guard Nodes"),
            ("Red", "Animal Nodes"),
            ("Red Flash", "CSP Backtrack"),
        ]

        for i, (color, desc) in enumerate(legends):
            text = self.font_small.render(
                (
                    f"🟡{color}: {desc}"
                    if i == 0
                    else f"🟠{color}: {desc}" if i == 1 else f"🔴{color}: {desc}"
                ),
                True,
                (200, 200, 200),
            )
            self.screen.blit(text, (x + 10, y_start + (i * 14)))

        return y + 70 + 5

    def _draw_controls_section(self, x, y):
        """Display keyboard controls"""
        self._draw_section(x, y, "CONTROLS", 55, (80, 120, 80))
        y_start = y + 26

        controls = ["TAB: Toggle Panel", "N: Toggle Node Colors", "P: Pause Game"]
        for i, ctrl in enumerate(controls):
            text = self.font_small.render(ctrl, True, (200, 200, 200))
            self.screen.blit(text, (x + 10, y_start + (i * 16)))

        return y + 55 + 5

    # ============================================================
    # NODE OVERLAY (On-Grid Visualization)
    # ============================================================

    def draw_node_overlay_on_grid(self):
        """Draw colored highlights on grid showing A* explored nodes"""
        if not self.show_node_overlay:
            return

        # Farmer nodes (Yellow - fade older nodes)
        for idx, (col, row) in enumerate(self.farmer_nodes[-50:]):
            alpha = max(40, 180 - idx * 3)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 255, 0, alpha))
            self.screen.blit(surf, (x, y))

        # Guard nodes (Orange)
        for idx, (col, row) in enumerate(self.guard_nodes[-50:]):
            alpha = max(40, 150 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 165, 0, alpha))
            self.screen.blit(surf, (x, y))

        # Animal nodes (Red)
        for idx, (col, row) in enumerate(self.animal_nodes[-50:]):
            alpha = max(40, 130 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 100, 100, alpha))
            self.screen.blit(surf, (x, y))

    # ============================================================
    # MAIN DRAW METHOD
    # ============================================================

    def draw(self, farmer_score=0, guard_score=0, animal_score=0, fps=60):
        """Render the complete visualization panel"""
        if not self.visible:
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Panel background
        panel = pygame.Rect(
            self.panel_x, self.panel_y, self.panel_width, self.panel_height
        )
        overlay = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        overlay.fill((20, 25, 30, 240))
        self.screen.blit(overlay, (self.panel_x, self.panel_y))
        pygame.draw.rect(self.screen, (100, 150, 100), panel, 2)

        # Title bar
        title_bar = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, 24)
        pygame.draw.rect(self.screen, (60, 80, 60), title_bar)
        title = self.font_title.render(
            "ALGORITHM VISUALIZER [TAB]", True, (255, 215, 0)
        )
        self.screen.blit(title, (self.panel_x + 8, self.panel_y + 4))

        y = self.panel_y + 28
        x = self.panel_x + 10

        # Draw all sections
        y = self._draw_astar_section(x, y)
        y = self._draw_csp_section(x, y)
        y = self._draw_metrics_section(
            x, y, farmer_score, guard_score, animal_score, fps
        )
        y = self._draw_legend_section(x, y)
        self._draw_controls_section(x, y)

    # ============================================================
    # TOGGLE FUNCTIONS
    # ============================================================

    def toggle(self):
        """Show/hide the visualization panel"""
        self.visible = not self.visible
        print(f"Visualizer Panel: {'ON' if self.visible else 'OFF'}")

    def toggle_node_overlay(self):
        """Show/hide colored node overlay on grid"""
        self.show_node_overlay = not self.show_node_overlay
        print(f"Node Overlay: {'ON' if self.show_node_overlay else 'OFF'}")

    def notify_backtrack(self):
        """Trigger backtrack visual flash"""
        self.flash_timer = 30
