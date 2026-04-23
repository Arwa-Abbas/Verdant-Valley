"""
Visualization Manager - Handles A* node expansion, CSP backtracking, path overlays, and historical view
Controls: TAB=Panel | N=Nodes | M=Paths
"""

import pygame
from utils.constants import *
from utils.helpers import grid_to_px, manhattan
from collections import deque
import time


class VisualizationManager:
    """Real-time algorithm visualization panel for A* and CSP"""

    def __init__(self, screen, grid):
        self.screen = screen
        self.grid = grid
        self.visible = True

        # Fonts
        self.font = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 14)

        # Panel dimensions
        self.panel_width = 420
        self.panel_height = 680
        self.panel_x = SCREEN_W - self.panel_width - 10
        self.panel_y = 10

        # A* Node expansion tracking (separate for each agent)
        self.farmer_nodes = []
        self.guard_nodes = []
        self.fox_nodes = []
        self.rabbit_nodes = []

        self.farmer_path = []
        self.guard_path = []
        self.fox_path = []
        self.rabbit_path = []

        # Node expansion counters
        self.farmer_expanded = 0
        self.guard_expanded = 0
        self.fox_expanded = 0
        self.rabbit_expanded = 0

        # Path costs
        self.farmer_cost = 0
        self.guard_cost = 0
        self.fox_cost = 0
        self.rabbit_cost = 0

        # CSP tracking
        self.csp_domains = {}
        self.csp_step = 0
        self.csp_flash_timer = 0
        self.csp_flash_pos = None
        self.last_backtrack_count = 0

        # Historical view
        self.backtrack_history = deque(maxlen=10)
        self.assignment_history = deque(maxlen=15)

        # Toggle states
        self.show_node_overlay = True
        self.show_paths = True
        self.show_panel = True
        self.frame_counter = 0

        # Agent colors (yellow, orange, bright red, purple)
        self.agent_colors = {
            "farmer": (255, 255, 0),
            "guard": (255, 165, 0),
            "fox": (255, 80, 80),
            "rabbit": (200, 100, 255),
            "farmer_path": (0, 255, 0),
            "guard_path": (255, 0, 0),
            "fox_path": (255, 140, 0),
            "rabbit_path": (180, 100, 255),
        }

        print("Visualization Manager initialized - TAB=Panel N=Nodes M=Paths")

    # ============================================================
    # DATA UPDATE METHODS
    # ============================================================

    def update_astar_data(self, farmer, guard, animal_fox, animal_rabbit):
        """Collect A* exploration data from all four agents"""
        if farmer:
            self.farmer_nodes = getattr(farmer, "last_explored_nodes", [])[-100:]
            self.farmer_expanded = getattr(farmer, "nodes_expanded", 0)
            self.farmer_cost = getattr(farmer, "path_cost", 0)
            self.farmer_path = getattr(farmer, "last_path", [])

        if guard:
            self.guard_nodes = getattr(guard, "last_explored_nodes", [])[-100:]
            self.guard_expanded = getattr(guard, "nodes_expanded", 0)
            self.guard_cost = getattr(guard, "path_cost", 0)
            self.guard_path = getattr(guard, "last_path", [])

        if animal_fox:
            self.fox_nodes = getattr(animal_fox, "last_explored_nodes", [])[-50:]
            self.fox_expanded = getattr(animal_fox, "nodes_expanded", 0)
            self.fox_cost = getattr(animal_fox, "path_cost", 0)
            self.fox_path = getattr(animal_fox, "last_path", [])

        if animal_rabbit:
            self.rabbit_nodes = getattr(animal_rabbit, "last_explored_nodes", [])[-50:]
            self.rabbit_expanded = getattr(animal_rabbit, "nodes_expanded", 0)
            self.rabbit_cost = getattr(animal_rabbit, "path_cost", 0)
            self.rabbit_path = getattr(animal_rabbit, "last_path", [])

    def update_csp_data(self, csp_solver):
        """Collect CSP backtracking and domain data"""
        if csp_solver:
            # Track domain changes
            new_domains = getattr(csp_solver, "domains", {})
            if new_domains != self.csp_domains:
                self.csp_domains = new_domains.copy()
                self.csp_step += 1

            # Track assignments
            current_assign = getattr(csp_solver, "assign", {})
            for (col, row), crop in current_assign.items():
                if crop != CROP_NONE:
                    is_new = True
                    for hist in self.assignment_history:
                        if hist[0] == col and hist[1] == row and hist[2] == crop:
                            is_new = False
                            break
                    if is_new:
                        self.assignment_history.append(
                            (col, row, crop, self.csp_step, time.time())
                        )

            # Track backtracks
            backtrack_log = getattr(csp_solver, "backtrack_log", [])
            if len(backtrack_log) > self.last_backtrack_count:
                for entry in backtrack_log[self.last_backtrack_count :]:
                    if isinstance(entry, tuple) and len(entry) >= 2:
                        col, row = entry[0], entry[1]
                        self.backtrack_history.append(
                            (col, row, self.csp_step, time.time())
                        )
                        self.csp_flash_timer = 30
                        self.csp_flash_pos = (col, row)

                self.last_backtrack_count = len(backtrack_log)

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _draw_bar(self, x, y, w, h, value, max_val, color):
        """Draw a progress bar"""
        if max_val <= 0:
            max_val = 1
        fill = int(w * min(1.0, max(0.0, value / max_val)))
        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, w, h))
        if fill > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill, h))

    def _draw_domain_bar(self, x, y, domain):
        """Draw domain shrinking progress bar"""
        total = 5
        remaining = len([c for c in domain if c != CROP_NONE])
        bar_w = 120
        fill_w = int(bar_w * (remaining / total))

        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, bar_w, 12))

        if remaining > 3:
            color = (0, 200, 0)
        elif remaining > 1:
            color = (200, 200, 0)
        else:
            color = (200, 0, 0)

        pygame.draw.rect(self.screen, color, (x, y, fill_w, 12))

        pct = self.font_small.render(
            f"{int(remaining/total*100)}%", True, (200, 200, 200)
        )
        self.screen.blit(pct, (x + bar_w + 5, y))

    def _draw_agent_row(self, x, y, name, color, node_count, path_cost):
        """Draw single agent stats row"""
        name_text = self.font.render(name, True, color)
        self.screen.blit(name_text, (x + 8, y))

        nodes_text = self.font.render(f"Nodes: {node_count}", True, (220, 220, 220))
        self.screen.blit(nodes_text, (x + 130, y))

        cost_text = self.font.render(f"Cost: {path_cost:.1f}", True, (220, 220, 220))
        self.screen.blit(cost_text, (x + 260, y))

    # ============================================================
    # ON-GRID VISUALIZATIONS
    # ============================================================

    def draw_node_expansion_on_grid(self):
        """Draw colored node highlights on grid for all agents"""
        if not self.show_node_overlay:
            return

        # Farmer nodes (Yellow)
        for idx, (col, row) in enumerate(self.farmer_nodes[-80:]):
            alpha = max(30, 180 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 255, 0, alpha))
            self.screen.blit(surf, (x, y))

        # Guard nodes (Orange)
        for idx, (col, row) in enumerate(self.guard_nodes[-80:]):
            alpha = max(30, 150 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 165, 0, alpha))
            self.screen.blit(surf, (x, y))

        # Fox nodes (Red)
        for idx, (col, row) in enumerate(self.fox_nodes[-50:]):
            alpha = max(40, 160 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 80, 80, alpha))
            self.screen.blit(surf, (x, y))

        # Rabbit nodes (Purple)
        for idx, (col, row) in enumerate(self.rabbit_nodes[-50:]):
            alpha = max(40, 140 - idx * 2)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((200, 100, 255, alpha))
            self.screen.blit(surf, (x, y))

    def draw_paths_on_grid(self):
        """Draw final chosen paths for all agents"""
        if not self.show_paths or not self.show_node_overlay:
            return

        # Farmer path (Green)
        for i in range(len(self.farmer_path) - 1):
            col, row = self.farmer_path[i]
            nc, nr = self.farmer_path[i + 1]
            x1 = GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
            y1 = GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
            x2 = GRID_OFFSET_X + nc * TILE_SIZE + TILE_SIZE // 2
            y2 = GRID_OFFSET_Y + nr * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.line(self.screen, (0, 255, 0), (x1, y1), (x2, y2), 3)

        # Guard path (Red)
        for i in range(len(self.guard_path) - 1):
            col, row = self.guard_path[i]
            nc, nr = self.guard_path[i + 1]
            x1 = GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
            y1 = GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
            x2 = GRID_OFFSET_X + nc * TILE_SIZE + TILE_SIZE // 2
            y2 = GRID_OFFSET_Y + nr * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.line(self.screen, (255, 0, 0), (x1, y1), (x2, y2), 3)

        # Fox path (Orange)
        for i in range(len(self.fox_path) - 1):
            col, row = self.fox_path[i]
            nc, nr = self.fox_path[i + 1]
            x1 = GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
            y1 = GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
            x2 = GRID_OFFSET_X + nc * TILE_SIZE + TILE_SIZE // 2
            y2 = GRID_OFFSET_Y + nr * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.line(self.screen, (255, 140, 0), (x1, y1), (x2, y2), 3)

        # Rabbit path (Purple)
        for i in range(len(self.rabbit_path) - 1):
            col, row = self.rabbit_path[i]
            nc, nr = self.rabbit_path[i + 1]
            x1 = GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
            y1 = GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
            x2 = GRID_OFFSET_X + nc * TILE_SIZE + TILE_SIZE // 2
            y2 = GRID_OFFSET_Y + nr * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.line(self.screen, (180, 100, 255), (x1, y1), (x2, y2), 3)

        # Path dots
        for col, row in self.farmer_path:
            x = GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
            y = GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(self.screen, (0, 255, 0), (x, y), 4)

    def draw_csp_backtrack_flash(self):
        """Flash red on grid when CSP backtrack occurs"""
        if self.csp_flash_timer > 0 and self.csp_flash_pos:
            col, row = self.csp_flash_pos
            alpha = min(200, self.csp_flash_timer * 6)
            x = GRID_OFFSET_X + col * TILE_SIZE
            y = GRID_OFFSET_Y + row * TILE_SIZE
            flash = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            flash.fill((255, 0, 0, alpha))
            self.screen.blit(flash, (x, y))
            self.csp_flash_timer -= 1
        else:
            self.csp_flash_timer = 0
            self.csp_flash_pos = None

    # ============================================================
    # PANEL DRAWING
    # ============================================================

    def _draw_astar_section(self, x, y, col_w):
        """Draw A* node expansion statistics section"""
        section_h = 145
        pygame.draw.rect(self.screen, (35, 45, 55), (x, y, col_w, section_h))
        pygame.draw.rect(self.screen, (80, 150, 80), (x, y, col_w, section_h), 1)

        header = self.font.render("A* SEARCH NODE EXPANSION", True, (255, 215, 0))
        self.screen.blit(header, (x + 8, y + 5))

        self._draw_agent_row(
            x,
            y + 28,
            "FARMER:",
            self.agent_colors["farmer"],
            self.farmer_expanded,
            self.farmer_cost,
        )
        self._draw_agent_row(
            x,
            y + 48,
            "GUARD:",
            self.agent_colors["guard"],
            self.guard_expanded,
            self.guard_cost,
        )
        self._draw_agent_row(
            x,
            y + 68,
            "FOX:",
            self.agent_colors["fox"],
            self.fox_expanded,
            self.fox_cost,
        )
        self._draw_agent_row(
            x,
            y + 88,
            "RABBIT:",
            self.agent_colors["rabbit"],
            self.rabbit_expanded,
            self.rabbit_cost,
        )

        return y + section_h + 8

    def _draw_csp_section(self, x, y, col_w):
        """Draw CSP backtracking and domain shrinking section"""
        section_h = 140
        pygame.draw.rect(self.screen, (35, 45, 55), (x, y, col_w, section_h))
        pygame.draw.rect(self.screen, (80, 150, 80), (x, y, col_w, section_h), 1)

        header = self.font.render("CSP BACKTRACKING", True, (255, 215, 0))
        self.screen.blit(header, (x + 8, y + 5))

        self.screen.blit(
            self.font.render(
                f"Backtracks: {len(self.backtrack_history)}", True, (255, 180, 180)
            ),
            (x + 8, y + 28),
        )
        self.screen.blit(
            self.font.render(
                f"Assignments: {len(self.assignment_history)}", True, (180, 255, 180)
            ),
            (x + 200, y + 28),
        )

        self.screen.blit(
            self.font_small.render("Domain Progress:", True, (150, 200, 150)),
            (x + 8, y + 52),
        )

        domain_y = y + 72
        for i, (var, domain) in enumerate(list(self.csp_domains.items())[:3]):
            if isinstance(var, tuple):
                col, row = var
                self.screen.blit(
                    self.font_small.render(f"({col},{row}):", True, (200, 200, 150)),
                    (x + 8, domain_y + i * 20),
                )
                self._draw_domain_bar(x + 70, domain_y + i * 20, domain)

        return y + section_h + 8

    def _draw_history_section(self, x, y, col_w):
        """Draw backtrack and assignment history section"""
        section_h = 150
        pygame.draw.rect(self.screen, (35, 45, 55), (x, y, col_w, section_h))
        pygame.draw.rect(self.screen, (80, 150, 80), (x, y, col_w, section_h), 1)

        header = self.font.render("HISTORICAL VIEW", True, (255, 215, 0))
        self.screen.blit(header, (x + 8, y + 5))

        # Backtrack history
        title = self.font.render("Recent Backtracks:", True, (255, 215, 0))
        self.screen.blit(title, (x + 8, y + 28))

        hist_y = y + 50
        for i, (col, row, step, timestamp) in enumerate(self.backtrack_history):
            if i > 4:
                break
            time_ago = time.time() - timestamp
            if time_ago < 1:
                time_str = "just now"
            elif time_ago < 60:
                time_str = f"{int(time_ago)}s ago"
            else:
                time_str = f"{int(time_ago/60)}m ago"

            text = self.font_small.render(
                f"({col},{row}) step {step} ({time_str})", True, (255, 150, 150)
            )
            self.screen.blit(text, (x + 15, hist_y))
            hist_y += 16

        # Assignment history
        hist_y += 8
        title = self.font.render("Recent Assignments:", True, (100, 200, 100))
        self.screen.blit(title, (x + 8, hist_y))
        hist_y += 20

        for i, (col, row, crop, step, timestamp) in enumerate(self.assignment_history):
            if i > 4:
                break
            crop_name = CROP_NAMES.get(crop, "Unknown")[:8]
            text = self.font_small.render(
                f"({col},{row}): {crop_name} step {step}", True, (150, 200, 150)
            )
            self.screen.blit(text, (x + 15, hist_y))
            hist_y += 16

        return y + section_h + 8

    def _draw_metrics_section(
        self, x, y, col_w, farmer_score, guard_score, fox_score, rabbit_score, fps
    ):
        """Draw live metrics section"""
        section_h = 80
        pygame.draw.rect(self.screen, (35, 45, 55), (x, y, col_w, section_h))
        pygame.draw.rect(self.screen, (80, 150, 80), (x, y, col_w, section_h), 1)

        header = self.font.render("LIVE METRICS", True, (255, 215, 0))
        self.screen.blit(header, (x + 8, y + 5))

        self.screen.blit(
            self.font.render(f"Farmer: {farmer_score}", True, (100, 200, 100)),
            (x + 8, y + 30),
        )
        self.screen.blit(
            self.font.render(f"Guard: {guard_score}", True, (255, 100, 100)),
            (x + 150, y + 30),
        )
        self.screen.blit(
            self.font.render(f"Fox: {fox_score}", True, (255, 80, 80)),
            (x + 300, y + 30),
        )
        self.screen.blit(
            self.font.render(f"Rabbit: {rabbit_score}", True, (200, 100, 255)),
            (x + 8, y + 55),
        )
        self.screen.blit(
            self.font.render(f"FPS: {fps}", True, (150, 150, 255)), (x + 300, y + 55)
        )

        return y + section_h + 8

    def _draw_legend_section(self, x, y, col_w):
        """Draw legend and controls section"""
        section_h = 85
        pygame.draw.rect(self.screen, (35, 45, 55), (x, y, col_w, section_h))
        pygame.draw.rect(self.screen, (80, 150, 80), (x, y, col_w, section_h), 1)

        header = self.font.render("LEGEND & CONTROLS", True, (255, 215, 0))
        self.screen.blit(header, (x + 8, y + 5))

        legends = [
            ("Yellow", "Farmer Nodes"),
            ("Orange", "Guard Nodes"),
            ("Red", "Fox Nodes"),
            ("Purple", "Rabbit Nodes"),
            ("Green", "Farmer Path"),
            ("Red Line", "Guard Path"),
            ("Orange Line", "Fox Path"),
            ("Purple Line", "Rabbit Path"),
            ("Red Flash", "CSP Backtrack"),
        ]

        for i, (color, desc) in enumerate(legends):
            text = self.font_small.render(f"{color}: {desc}", True, (200, 200, 200))
            if i < 4:
                self.screen.blit(text, (x + 10, y + 28 + i * 14))
            elif i < 8:
                self.screen.blit(text, (x + 200, y + 28 + (i - 4) * 14))

        controls = "TAB:Panel | N:Nodes | M:Paths"
        self.screen.blit(
            self.font_small.render(controls, True, (180, 180, 180)), (x + 10, y + 68)
        )

    # ============================================================
    # MAIN DRAW METHOD
    # ============================================================

    def draw_panel(self, farmer_score, guard_score, fox_score, rabbit_score, fps):
        """Draw complete visualization panel"""
        if not self.show_panel:
            return

        self.frame_counter += 1

        # Panel background
        panel_rect = pygame.Rect(
            self.panel_x, self.panel_y, self.panel_width, self.panel_height
        )
        overlay = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        overlay.fill((20, 25, 30, 245))
        self.screen.blit(overlay, (self.panel_x, self.panel_y))
        pygame.draw.rect(self.screen, (100, 150, 100), panel_rect, 2)

        # Title bar
        title_bar = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, 32)
        pygame.draw.rect(self.screen, (60, 80, 60), title_bar)
        title = self.font_title.render(
            "ALGORITHM VISUALIZER [TAB]", True, (255, 215, 0)
        )
        self.screen.blit(title, (self.panel_x + 10, self.panel_y + 6))

        y = self.panel_y + 40
        x = self.panel_x + 12
        col_w = self.panel_width - 24

        y = self._draw_astar_section(x, y, col_w)
        y = self._draw_csp_section(x, y, col_w)
        y = self._draw_history_section(x, y, col_w)
        y = self._draw_metrics_section(
            x, y, col_w, farmer_score, guard_score, fox_score, rabbit_score, fps
        )
        self._draw_legend_section(x, y, col_w)

    def draw_all(
        self,
        farmer_score=0,
        guard_score=0,
        fox_score=0,
        rabbit_score=0,
        fps=60,
        guard=None,
    ):
        """Draw all visualizations"""
        if self.csp_flash_timer > 0:
            self.csp_flash_timer -= 1

        self.draw_node_expansion_on_grid()
        self.draw_paths_on_grid()
        self.draw_csp_backtrack_flash()
        self.draw_panel(farmer_score, guard_score, fox_score, rabbit_score, fps)

    # ============================================================
    # TOGGLE FUNCTIONS
    # ============================================================

    def toggle_panel(self):
        self.show_panel = not self.show_panel
        print(f"Visualizer Panel: {'ON' if self.show_panel else 'OFF'}")

    def toggle_nodes(self):
        self.show_node_overlay = not self.show_node_overlay
        print(f"Node Overlay: {'ON' if self.show_node_overlay else 'OFF'}")

    def toggle_paths(self):
        self.show_paths = not self.show_paths
        print(f"Path Overlay: {'ON' if self.show_paths else 'OFF'}")

    def record_backtrack(self, col, row, constraint=""):
        self.backtrack_history.append((col, row, self.csp_step, time.time()))
        self.csp_flash_timer = 30
        self.csp_flash_pos = (col, row)
