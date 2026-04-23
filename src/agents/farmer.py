"""
src/agents/farmer.py - Farmer Agent

Functionality:
- Terrain: walks on mud/dirt/grass/field, blocked by water and stone
- Plant mode: triggered externally via farmer.trigger_planting()
- Manual planting: farmer.plant_selected_crops(crop_id, count)
    -> Farmer physically walks to each tile and plants, then auto-harvests
- Crop growth: ticks over time per planted tile
- Harvest: auto-harvests stage-2 crops using A* pathfinding
"""

import random
from .base_agent import Agent
from src.algorithms.astar import astar
from src.algorithms.csp import CROP_HEURISTIC_VALUE
from utils.constants import *
from utils.helpers import manhattan, tile_center


def _animal_aware_cost(tile, base_cost, agents, animal_avoidance_radius=2):
    """
    Add cost penalty for tiles near animals to make farmer avoid them.
    Returns infinity if tile is adjacent to an animal.
    """
    if base_cost == float("inf"):
        return float("inf")
    if not agents:
        return base_cost

    animals = [
        a for a in agents if hasattr(a, "name") and "Animal" in a.name and a.alive
    ]
    if not animals:
        return base_cost

    tile_pos = (tile.col, tile.row)
    min_dist = min(manhattan(tile_pos, (a.col, a.row)) for a in animals)

    if min_dist <= 1:
        return float("inf")
    elif min_dist <= animal_avoidance_radius:
        return base_cost + 20
    return base_cost


# Desirability score for planting on different tile types
PLANT_TILE_SCORE = {
    TILE_FIELD: 3.0,
    TILE_MUD: 2.0,
    TILE_DIRT: 1.0,
}

# Growth requirements: (ticks to sprout, ticks to ripe)
CROP_GROWTH_TICKS_OLD = {
    CROP_WHEAT: (180, 300),
    CROP_SUNFLOWER: (240, 360),
    CROP_CORN: (200, 320),
    CROP_TOMATO: (220, 340),
    CROP_CARROT: (160, 280),
}

CROP_GROWTH_TICKS_NEW = {
    CROP_WHEAT: (900, 1800),
    CROP_SUNFLOWER: (900, 1800),
    CROP_CORN: (900, 1800),
    CROP_TOMATO: (900, 1800),
    CROP_CARROT: (900, 1800),
}

CROP_GROWTH_PROFILE = "old"

if CROP_GROWTH_PROFILE == "new":
    CROP_GROWTH_TICKS = CROP_GROWTH_TICKS_NEW
    DEFAULT_CROP_GROWTH_TICKS = (900, 1800)
else:
    CROP_GROWTH_TICKS = CROP_GROWTH_TICKS_OLD
    DEFAULT_CROP_GROWTH_TICKS = (180, 300)


class Farmer(Agent):

    def show_blocked_cross(self, surface, grid):
        """Draw a red cross on the last failed plant tile if the failure timer is active."""
        if (
            getattr(self, "_failed_plant_tile", None) is not None
            and getattr(self, "_failed_plant_timer", 0) > 0
        ):
            from game_ui.game_ui import draw_blocked_tile_cross

            tile = self._failed_plant_tile
            if isinstance(tile, tuple) and len(tile) == 2:
                col, row = tile
                draw_blocked_tile_cross(surface, col, row, grid)

    def __init__(self, col, row):
        import os
        import pygame

        path = "assets/agents/farmer/Farmer.png"
        frame_w, frame_h = 32, 32
        rows, cols = 10, 6

        if os.path.exists(path):
            try:
                sheet = pygame.image.load(path)
                sw, sh = sheet.get_size()
                cols = max(1, sw // frame_w)
                rows = max(1, sh // frame_h)
            except Exception:
                pass

        Agent.__init__(
            self,
            col,
            row,
            C_FARMER,
            speed=2.0,
            name="Farmer",
            sprite_sheet_path=path if os.path.exists(path) else None,
            frame_size=(frame_w, frame_h),
            animation_rows=rows,
            animation_cols=cols,
            scale=2,
        )

        self._anim_direction_rows = {
            "down": 0,
            "up": 2 if rows > 2 else 0,
            "left": 4 if rows > 4 else 0,
            "right": 3 if rows > 3 else 0,
        }

        if self.animation:
            self.animation.animation_speed = 0.15

        self.target = None
        self.replan_cd = 0
        self.idle_ticks = 0
        self.debug_timer = 0
        self.harvest_count = 0
        self.plant_count = 0
        self.harvested_count = 0

        # Single-tile planting (G key or UI button)
        self._plant_requested = False

        # Autonomous multi-tile planting (manual selection mode)
        self._planting_mode = False
        self._plant_queue = []
        self._plant_crop_id = CROP_WHEAT
        self._auto_plant_disabled = True

        # Growth timers for planted crops
        self._growth_timers = {}

        # Failed plant visual indicator
        self._failed_plant_tile = None
        self._failed_plant_timer = 0

        # Visualization data for pathfinding
        self.last_explored_nodes = []
        self.nodes_expanded = 0
        self.path_cost = 0
        self.last_path = []

    # Public API

    def trigger_planting(self):
        """Plant one crop on the farmer's current tile (triggered by G key or UI button)."""
        if self._planting_mode:
            return
        self._plant_requested = True

    def plant_selected_crops(self, crop_id: int, count: int):
        """Begin autonomous planting mode for a specified number of crops."""
        self._plant_crop_id = crop_id
        self._plant_queue = []
        self._planting_mode = True
        self._pending_count = count
        self._tiles_planted = 0
        self.state = "planting"

    # Internal helpers

    def _tile_passable(self, tile) -> bool:
        """Check if a tile is passable for the farmer based on terrain cost."""
        return tile is not None and FARMER_COSTS.get(tile.type, float("inf")) != float(
            "inf"
        )

    def _can_step(self, grid, col, row):
        """Check if the farmer can step onto a given tile."""
        tile = grid.get(col, row)
        if not self._tile_passable(tile):
            return False
        if getattr(tile, "flooded", False) or getattr(tile, "muddy", False):
            return False
        return True

    def _ensure_valid_position(self, grid):
        """If current tile is impassable, find nearest passable tile and move there."""
        tile = grid.get(self.col, self.row)
        if self._tile_passable(tile):
            return

        for radius in range(1, 6):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if abs(dc) + abs(dr) != radius:
                        continue
                    nc, nr = self.col + dc, self.row + dr
                    t = grid.get(nc, nr)
                    if self._tile_passable(t):
                        self.col, self.row = nc, nr
                        cx, cy = tile_center(self.col, self.row)
                        self.x = float(cx)
                        self.y = float(cy)
                        self.path = []
                        self.path_idx = 0
                        self.moving = False
                        return

    def _move_along_path(self, grid=None):
        """Override to check tile passability before moving along path."""
        if grid is not None and self.path and self.path_idx < len(self.path):
            tc, tr = self.path[self.path_idx]
            if not self._can_step(grid, tc, tr):
                self._show_failed_plant((tc, tr))
        super()._move_along_path(grid)

    def _pick_harvest_target(self, grid, agents, season_mgr=None):
        """
        Select the best ripe crop tile to harvest.
        Scoring factors: crop value, distance, and proximity to animals.
        """
        best_score, best_tile = -1, None
        animals = [
            a for a in agents if hasattr(a, "name") and "Animal" in a.name and a.alive
        ]

        for c, r in grid.crop_tiles():
            tile = grid.get(c, r)
            if tile is None or tile.crop == CROP_NONE or tile.crop_stage < 2:
                continue

            rain_active = season_mgr.rain_active if season_mgr else False
            result = astar(
                grid,
                (self.col, self.row),
                (c, r),
                agent_type="Farmer",
                rain_active=rain_active,
            )
            if not getattr(result, "path", None) or len(result.path) > 20:
                continue

            value = CROP_VALUE[tile.crop]
            dist = manhattan((self.col, self.row), (c, r)) + 1

            animal_penalty = 0
            min_animal_dist = float("inf")
            for a in animals:
                d = manhattan((c, r), (a.col, a.row))
                min_animal_dist = min(min_animal_dist, d)
                if hasattr(a, "name") and "Bear" in a.name:
                    animal_penalty += 50 if d <= 3 else (20 if d <= 5 else 0)

            if min_animal_dist <= 2:
                animal_penalty += 30
            elif min_animal_dist <= 4:
                animal_penalty += 10

            score = (value * tile.crop_stage) / dist - animal_penalty
            if score > best_score:
                best_score, best_tile = score, (c, r)

        return best_tile

    def _pick_plant_tiles(self, grid, agents, count, season_mgr=None):
        """
        Select the best tiles for planting based on crop value, distance,
        and animal proximity.
        """
        candidates = []
        animals = [
            a for a in agents if hasattr(a, "name") and "Animal" in a.name and a.alive
        ]

        target_crop = (
            self._plant_crop_id
            if getattr(self, "_plant_crop_id", None) is not None
            else CROP_SUNFLOWER
        )

        for c in range(grid.cols):
            for r in range(grid.rows):
                tile = grid.get(c, r)
                if tile is None or tile.type not in PLANT_TILE_SCORE:
                    continue
                if tile.crop != CROP_NONE:
                    continue
                if (c, r) in self._growth_timers:
                    continue

                domain = getattr(tile, "domain", [CROP_NONE])
                if CROP_NONE in domain and len(domain) == 1:
                    continue
                if target_crop not in domain and target_crop != CROP_NONE:
                    continue

                value = CROP_HEURISTIC_VALUE.get(target_crop, 1.0) * getattr(
                    tile, "utility", 1.0
                )

                animal_penalty = 0.0
                for a in animals:
                    d = manhattan((c, r), (a.col, a.row))
                    if d <= 3:
                        animal_penalty = 2.0
                        break
                    elif d <= 5:
                        animal_penalty = 1.0

                dist = manhattan((self.col, self.row), (c, r)) + 1
                score = value - (0.1 * dist) - animal_penalty
                candidates.append((score, c, r))

        candidates.sort(reverse=True)
        return [(c, r) for _, c, r in candidates[:count]]

    def _choose_crop_for_tile(self, grid, c, r) -> int:
        """
        Choose the best crop to plant on a given tile based on:
        - Tile type (field, mud, dirt)
        - Proximity to water
        - Random variation to avoid deterministic behavior
        """
        import random

        tile = grid.get(c, r)

        near_water = False
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = grid.get(c + dc, r + dr)
            if neighbor and neighbor.type == TILE_WATER:
                near_water = True
                break

        domain = getattr(
            tile,
            "domain",
            [
                CROP_WHEAT,
                CROP_SUNFLOWER,
                CROP_CORN,
                CROP_TOMATO,
                CROP_CARROT,
                CROP_NONE,
            ],
        )
        allowed_crops = [
            crop
            for crop in [
                CROP_WHEAT,
                CROP_SUNFLOWER,
                CROP_CORN,
                CROP_TOMATO,
                CROP_CARROT,
            ]
            if crop in domain
        ]

        if not allowed_crops:
            return CROP_WHEAT

        crop_scores = {}

        for crop in allowed_crops:
            score = 0

            # Base desirability
            if crop == CROP_SUNFLOWER:
                score = 100
            elif crop == CROP_TOMATO:
                score = 90
            elif crop == CROP_CORN:
                score = 80
            elif crop == CROP_CARROT:
                score = 70
            elif crop == CROP_WHEAT:
                score = 60

            # Tile type bonuses
            if tile.type == TILE_FIELD:
                if crop == CROP_SUNFLOWER:
                    score += 50
                elif crop == CROP_WHEAT:
                    score += 30
            elif tile.type == TILE_MUD:
                if crop == CROP_CORN:
                    score += 40
            elif tile.type == TILE_DIRT:
                if crop == CROP_CARROT or crop == CROP_WHEAT:
                    score += 30

            # Water proximity bonus
            if near_water:
                if crop == CROP_TOMATO:
                    score += 60
                elif crop == CROP_CORN:
                    score += 30

            score += random.randint(0, 20)
            crop_scores[crop] = score

        best_crop = max(crop_scores, key=crop_scores.get)
        return best_crop

    def _plant_at(self, grid, c, r, crop=None):
        """Plant a crop at the specified tile coordinates."""
        tile = grid.get(c, r)
        if tile is None or tile.type not in PLANT_TILE_SCORE:
            return

        if crop is None:
            if self._planting_mode and self._plant_crop_id is not None:
                crop = self._plant_crop_id
            else:
                crop = self._choose_crop_for_tile(grid, c, r)

        tile.crop = crop
        tile.crop_stage = 0
        tile.managed_growth = True
        self._growth_timers[(c, r)] = 0
        self.plant_count += 1

    def _harvest(self, grid):
        """Harvest a ripe crop on the farmer's current tile."""
        tile = grid.get(self.col, self.row)
        if tile and tile.crop != CROP_NONE and tile.crop_stage >= 2:
            value = CROP_VALUE[tile.crop] * tile.crop_stage
            self.score += value
            self.harvest_count += 1
            self.harvested_count += 1

            tile.crop = CROP_NONE
            tile.crop_stage = 0
            tile.managed_growth = False
            self._growth_timers.pop((self.col, self.row), None)
            self.target = None
            self.state = "harvesting"

    def _tick_growth(self, grid):
        """Update growth timers for all planted crops."""
        done = []
        for (c, r), ticks in self._growth_timers.items():
            tile = grid.get(c, r)
            if tile is None or tile.crop == CROP_NONE:
                if tile is not None:
                    tile.managed_growth = False
                done.append((c, r))
                continue

            ticks += 1
            self._growth_timers[(c, r)] = ticks
            grow = CROP_GROWTH_TICKS.get(tile.crop, DEFAULT_CROP_GROWTH_TICKS)

            if tile.crop_stage == 0 and ticks >= grow[0]:
                tile.crop_stage = 1
            elif tile.crop_stage == 1 and ticks >= grow[1]:
                tile.crop_stage = 2
                tile.managed_growth = False
                done.append((c, r))

        for key in done:
            self._growth_timers.pop(key, None)

    def _try_plant_current_tile(self, grid):
        """Attempt to plant a crop on the farmer's current tile."""
        self._plant_requested = False
        tile = grid.get(self.col, self.row)

        if tile is None:
            self._show_failed_plant()
            return
        if tile.type not in PLANT_TILE_SCORE:
            self._show_failed_plant()
            return
        if tile.crop != CROP_NONE:
            self._show_failed_plant()
            return
        if (self.col, self.row) in self._growth_timers:
            self._show_failed_plant()
            return

        domain = getattr(tile, "domain", [CROP_NONE])
        if CROP_NONE in domain and len(domain) == 1:
            self._show_failed_plant()
            return

        best_crop = self._choose_crop_for_tile(grid, self.col, self.row)
        self._plant_at(grid, self.col, self.row, best_crop)

    def _show_failed_plant(self, tile_pos=None):
        """Mark a tile as failed for planting and start the failure indicator timer."""
        self._failed_plant_tile = (
            tile_pos if tile_pos is not None else (self.col, self.row)
        )
        self._failed_plant_timer = 60

    def update_failed_plant_timer(self):
        """Decrement the failed plant timer and clear the indicator when it reaches zero."""
        if self._failed_plant_timer > 0:
            self._failed_plant_timer -= 1
        if self._failed_plant_timer == 0:
            self._failed_plant_tile = None

    def _update_planting(self, grid, agents, season_mgr=None):
        """
        Manage autonomous planting mode: select target tiles, navigate to them,
        and plant crops.
        """
        if (
            not self._plant_queue
            and hasattr(self, "_pending_count")
            and self._pending_count > 0
        ):
            new_tiles = self._pick_plant_tiles(
                grid, agents, self._pending_count, season_mgr
            )
            if not new_tiles:
                new_tiles = []
            new_tiles = [
                (c, r)
                for c, r in new_tiles
                if grid.get(c, r)
                and grid.get(c, r).crop == CROP_NONE
                and (c, r) not in self._growth_timers
            ]
            self._plant_queue = new_tiles
            self._pending_count = 0

        # Filter out tiles that are no longer plantable
        self._plant_queue = [
            (c, r)
            for c, r in self._plant_queue
            if grid.get(c, r)
            and grid.get(c, r).crop == CROP_NONE
            and (c, r) not in self._growth_timers
        ]

        if not self._plant_queue:
            self._planting_mode = False
            self._pending_count = 0
            self.state = "idle"
            self.target = None
            return

        next_tile = self._plant_queue[0]
        next_tile_obj = grid.get(*next_tile)
        if next_tile_obj is None or next_tile_obj.type not in PLANT_TILE_SCORE:
            self._show_failed_plant(next_tile)
            self._plant_queue.pop(0)
            return

        # If we've reached the target tile, plant
        if (self.col, self.row) == next_tile:
            self._plant_at(grid, *next_tile, self._plant_crop_id)
            self._tiles_planted += 1
            self._plant_queue.pop(0)
            self.moving = False
            return

        # Find path to the next plant tile
        if not self.moving or self.replan_cd == 0:
            rain_active = season_mgr.rain_active if season_mgr else False
            path, explored = self._find_path_with_animal_avoidance(
                grid, agents, next_tile, rain_active=rain_active
            )
            if path:
                self.set_path(path, explored)
                self.replan_cd = 60
            else:
                self._show_failed_plant(next_tile)
                self._plant_queue.pop(0)
            return

    def _find_path_with_animal_avoidance(self, grid, agents, target, rain_active=False):
        """Find a path to target while avoiding animals using A*."""

        def cost_with_animal_avoidance(tile):
            base = FARMER_COSTS.get(tile.type, 1.0)
            return _animal_aware_cost(tile, base, agents, animal_avoidance_radius=2)

        result = astar(
            grid,
            (self.col, self.row),
            target,
            cost_dict=cost_with_animal_avoidance,
            agent_type="Farmer",
            rain_active=rain_active,
        )

        # Store visualization data
        self.last_explored_nodes = list(getattr(result, "explored", []))
        self.nodes_expanded = getattr(result, "nodes_expanded", 0)
        self.path_cost = getattr(result, "cost", 0)
        self.last_path = getattr(result, "path", [])

        return result.path, (result.explored if result.path else None)

    def update(self, grid, agents, season_mgr=None):
        """Main update loop for the farmer agent."""
        self._ensure_valid_position(grid)
        Agent.update(self, grid, agents, season_mgr)
        self.replan_cd = max(0, self.replan_cd - 1)

        if self.state == "idle" and not self._auto_plant_disabled:
            self.idle_ticks = getattr(self, "idle_ticks", 0) + 1
        else:
            self.idle_ticks = 0

        if self._failed_plant_timer > 0:
            self._failed_plant_timer -= 1

        self._tick_growth(grid)
        self._harvest(grid)

        # Handle single-tile planting request
        if self._plant_requested and not self._planting_mode:
            self._plant_requested = False
            self._try_plant_current_tile(grid)
            return

        # Handle autonomous planting mode
        if self._planting_mode:
            self._update_planting(grid, agents, season_mgr)
            return

        # Default behavior: harvest ripe crops
        if not self.moving or self.replan_cd == 0:
            new_target = self._pick_harvest_target(grid, agents, season_mgr)
            if new_target and new_target != self.target:
                self.target = new_target
                rain_active = season_mgr.rain_active if season_mgr else False
                path, explored = self._find_path_with_animal_avoidance(
                    grid, agents, self.target, rain_active=rain_active
                )
                if path and len(path) <= 20:
                    self.set_path(path, explored)
                    self.replan_cd = 45
                    self.state = "moving"
                else:
                    self._show_failed_plant(self.target)
                    self.target = None
                    self.state = "no_path"
            elif not new_target:
                self.moving = False
                self.state = "idle"
            else:
                self.state = "moving"

    def update_animation_direction(self):
        if not self.animation:
            return

        dx = self.col - self.last_pos[0]
        dy = self.row - self.last_pos[1]

        if dx > 0:
            self.animation.set_direction(self._anim_direction_rows["right"])
        elif dx < 0:
            self.animation.set_direction(self._anim_direction_rows["left"])
        elif dy > 0:
            self.animation.set_direction(self._anim_direction_rows["down"])
        elif dy < 0:
            self.animation.set_direction(self._anim_direction_rows["up"])

        self.last_pos = (self.col, self.row)

        if self.moving:
            self.animation.update()
        else:
            self.animation.current_frame = 0
            self.animation.animation_timer = 0

    def draw(self, surface, font=None):
        Agent.draw(self, surface, font)

    def draw_failed_plant_indicator(self, surface, grid=None):
        import pygame

        if self._failed_plant_timer <= 0 or self._failed_plant_tile is None:
            return

        from utils.helpers import tile_center

        col, row = self._failed_plant_tile
        px, py = tile_center(col, row)
        box_size = TILE_SIZE - 16
        box_rect = pygame.Rect(
            px - box_size // 2, py - box_size // 2, box_size, box_size
        )

        bg = pygame.Surface((box_rect.width + 8, box_rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(
            bg,
            (0, 0, 0, 180),
            pygame.Rect(0, 0, bg.get_width(), bg.get_height()),
            border_radius=8,
        )
        surface.blit(bg, (box_rect.x - 4, box_rect.y - 4))

        bc = (220, 40, 40)
        pygame.draw.rect(surface, bc, box_rect, width=3, border_radius=8)
        pygame.draw.line(
            surface,
            bc,
            (box_rect.left + 6, box_rect.top + 6),
            (box_rect.right - 6, box_rect.bottom - 6),
            4,
        )
        pygame.draw.line(
            surface,
            bc,
            (box_rect.right - 6, box_rect.top + 6),
            (box_rect.left + 6, box_rect.bottom - 6),
            4,
        )

        hc = (255, 220, 220)
        pygame.draw.line(
            surface,
            hc,
            (box_rect.left + 8, box_rect.top + 6),
            (box_rect.right - 6, box_rect.bottom - 8),
            2,
        )
        pygame.draw.line(
            surface,
            hc,
            (box_rect.right - 6, box_rect.top + 6),
            (box_rect.left + 8, box_rect.bottom - 8),
            2,
        )
