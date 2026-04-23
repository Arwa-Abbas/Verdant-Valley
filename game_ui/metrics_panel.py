"""
Metrics Panel - Display simulation statistics (crops, agents, performance, status)
Shown at bottom of screen during gameplay
"""

import pygame
from utils.constants import *
from utils.helpers import draw_rounded_rect, draw_text
from game_ui.fonts import FontCache


class MetricsPanel:
    """Bottom panel showing real-time game metrics"""

    def __init__(self, screen):
        self.screen = screen
        self.panel_height = 120
        self.panel_y = SCREEN_H - self.panel_height

    def draw(self, grid, agents):
        """Draw comprehensive farming simulation metrics panel"""
        panel_rect = pygame.Rect(0, self.panel_y, SCREEN_W, self.panel_height)
        panel_surface = pygame.Surface((SCREEN_W, self.panel_height), pygame.SRCALPHA)
        panel_surface.fill((25, 32, 28, 220))

        draw_rounded_rect(
            panel_surface,
            (25, 32, 28, 240),
            pygame.Rect(8, 8, SCREEN_W - 16, self.panel_height - 16),
            radius=18,
            border=2,
            border_color=(100, 140, 90),
        )
        self.screen.blit(panel_surface, (0, self.panel_y))

        # Fonts
        title_font = FontCache.get(FONT_MEDIUM, bold=True)
        normal_font = FontCache.get(FONT_SMALL)
        tiny_font = FontCache.get(FONT_TINY)

        # Calculate current metrics
        metrics = self._calculate_metrics(grid, agents)

        # Draw sections
        x = 24
        sections = [
            ("Crops", self._draw_crop_metrics, metrics["crops"]),
            ("Agents", self._draw_agent_metrics, metrics["agents"]),
            ("Performance", self._draw_performance_metrics, metrics["performance"]),
            ("Status", self._draw_status_metrics, metrics["status"]),
        ]

        for title, draw_func, data in sections:
            section_width = 280
            if x + section_width > SCREEN_W - 20:
                break

            # Section header
            header_rect = pygame.Rect(x - 8, self.panel_y + 10, section_width, 28)
            draw_rounded_rect(self.screen, (20, 28, 24, 200), header_rect, radius=10)

            # Section title
            title_text = title_font.render(title, True, C_TEXT_GOLD)
            self.screen.blit(title_text, (x, self.panel_y + 14))

            # Section content
            draw_func(
                x, self.panel_y + 42, section_width - 24, data, normal_font, tiny_font
            )

            x += section_width + 20

    # ============================================================
    # METRICS CALCULATION
    # ============================================================

    def _calculate_metrics(self, grid, agents):
        """Calculate all metrics from current game state"""
        # Crop metrics
        crops = {
            "planted": 0,
            "ready": 0,
            "harvested_value": 0,
            "by_type": {
                CROP_WHEAT: 0,
                CROP_SUNFLOWER: 0,
                CROP_CORN: 0,
                CROP_TOMATO: 0,
                CROP_CARROT: 0,
            },
        }

        # Agent metrics
        agents_data = {
            "farmers": {"count": 0, "total_score": 0, "active": 0},
            "guards": {"count": 0, "total_score": 0, "active": 0},
            "animals": {"count": 0, "total_score": 0, "alive": 0, "crops_eaten": 0},
        }

        # Analyze crops
        for col, row in grid.crop_tiles():
            tile = grid.get(col, row)
            crops["planted"] += 1

            if tile.crop in crops["by_type"]:
                crops["by_type"][tile.crop] += 1

            if tile.crop_stage >= 2:  # Ready to harvest
                crops["ready"] += 1
                crops["harvested_value"] += CROP_VALUE[tile.crop] * tile.crop_stage

        # Analyze agents
        for agent in agents:
            if hasattr(agent, "alive") and not agent.alive:
                continue

            if "Farmer" in agent.name:
                agents_data["farmers"]["count"] += 1
                agents_data["farmers"]["total_score"] += agent.score
                if agent.moving or agent.state != "idle":
                    agents_data["farmers"]["active"] += 1

            elif "Guard" in agent.name:
                agents_data["guards"]["count"] += 1
                agents_data["guards"]["total_score"] += agent.score
                if agent.moving or agent.state != "idle":
                    agents_data["guards"]["active"] += 1

            elif "Animal" in agent.name:
                agents_data["animals"]["count"] += 1
                agents_data["animals"]["total_score"] += agent.score
                if agent.alive:
                    agents_data["animals"]["alive"] += 1
                if hasattr(agent, "crops_eaten"):
                    agents_data["animals"]["crops_eaten"] += agent.crops_eaten

        # Performance metrics
        performance = {
            "efficiency": (crops["harvested_value"] / max(1, crops["planted"])),
            "protection": (
                agents_data["animals"]["crops_eaten"] / max(1, crops["planted"])
            )
            * 100,
            "productivity": agents_data["farmers"]["total_score"]
            + agents_data["guards"]["total_score"],
        }

        # Status metrics
        wet_count = 0
        for col in range(grid.cols):
            for row in range(grid.rows):
                if grid.tiles[col][row].wet:
                    wet_count += 1

        status = {
            "wet_tiles": wet_count,
            "field_utilization": len(grid.field_tiles())
            / (grid.cols * grid.rows)
            * 100,
        }

        return {
            "crops": crops,
            "agents": agents_data,
            "performance": performance,
            "status": status,
        }

    # ============================================================
    # SECTION DRAWING METHODS
    # ============================================================

    def _draw_crop_metrics(self, x, y, width, data, normal_font, tiny_font):
        """Draw crop-related metrics"""
        lines = [
            f"Planted: {data['planted']}",
            f"Ready: {data['ready']}",
            f"Value: ${data['harvested_value']}",
        ]

        # Crop icons
        crop_icons = {
            CROP_WHEAT: "🌾",
            CROP_SUNFLOWER: "🌻",
            CROP_CORN: "🌽",
            CROP_TOMATO: "🍅",
            CROP_CARROT: "🥕",
        }

        # Add crop type counts with positive values
        for crop_id, count in data["by_type"].items():
            if count > 0:
                icon = crop_icons.get(crop_id, "❓")
                lines.append(f"{icon} {CROP_NAMES[crop_id]}: {count}")

        # Render lines
        for i, line in enumerate(lines):
            if "Ready" in line and data["ready"] > 0:
                color = C_TEXT_SUCCESS
            else:
                color = C_TEXT_MAIN

            text = tiny_font.render(line, True, color)
            self.screen.blit(text, (x, y + i * 18))

    def _draw_agent_metrics(self, x, y, width, data, normal_font, tiny_font):
        """Draw agent-related metrics"""
        lines = []

        for agent_type, info in data.items():
            if agent_type == "farmers":
                icon = "🌾"
                color = C_FARMER
            elif agent_type == "guards":
                icon = "🛡️"
                color = C_GUARD
            else:  # animals
                icon = "🐮"
                color = C_ANIMAL

            count = info["count"]
            score = info["total_score"]
            lines.append(f"{icon} {agent_type.title()}: {count} (Score: {score})")

            if agent_type == "animals":
                eaten = info["crops_eaten"]
                lines.append(f"   Crops eaten: {eaten}")
            else:
                active = info.get("active", 0)
                lines.append(f"   Active: {active}/{count}")

        for i, line in enumerate(lines):
            text = tiny_font.render(line, True, C_TEXT_MAIN)
            self.screen.blit(text, (x, y + i * 18))

    def _draw_performance_metrics(self, x, y, width, data, normal_font, tiny_font):
        """Draw performance metrics with color coding"""
        lines = [
            f"Efficiency: {data['efficiency']:.1f}%",
            f"Protection: {data['protection']:.1f}%",
            f"Productivity: {data['productivity']:.0f}",
        ]

        for i, line in enumerate(lines):
            if "Efficiency" in line:
                color = C_TEXT_SUCCESS if data["efficiency"] > 50 else C_TEXT_WARN
            elif "Protection" in line:
                color = C_TEXT_WARN if data["protection"] > 20 else C_TEXT_SUCCESS
            else:
                color = C_TEXT_MAIN

            text = tiny_font.render(line, True, color)
            self.screen.blit(text, (x, y + i * 18))

    def _draw_status_metrics(self, x, y, width, data, normal_font, tiny_font):
        """Draw status metrics"""
        lines = [
            f"Wet tiles: {data['wet_tiles']}",
            f"Field utilization: {data['field_utilization']:.1f}%",
        ]

        for i, line in enumerate(lines):
            text = tiny_font.render(line, True, C_TEXT_DIM)
            self.screen.blit(text, (x, y + i * 18))
