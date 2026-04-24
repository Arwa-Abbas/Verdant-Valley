"""
Animal Agent - Fox and Rabbit with A* pathfinding, visualization tracking, and Genetic Algorithm evolution
"""

import random
import os
import pygame
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan, tile_center


class Animal(Agent):
    """Base animal class for Fox and Rabbit with GA evolution capabilities"""

    FLEE_DISTANCE = 5
    STAMINA_MAX = 100
    STAMINA_DRAIN = 0.5

    def __init__(self, col, row, animal_type="fox"):
        self.animal_type = animal_type

        # Load animal-specific assets
        if animal_type == "rabbit":
            path = "assets/agents/animal/hare.png"
            name = "Rabbit"
            color = (180, 140, 220)
            default_speed = 1.8
            animation_cols = 6
            animation_rows = 4
            w_guard_avoid = 1.0
        else:
            path = "assets/agents/animal/fox.png"
            name = "Fox"
            color = (255, 100, 50)
            default_speed = 1.6
            animation_cols = 6
            animation_rows = 4
            w_guard_avoid = 1.5

        # Load sprite sheet
        frame_w, frame_h = 16, 16
        sprite_path = None
        if os.path.exists(path):
            img = pygame.image.load(path)
            w, h = img.get_size()
            frame_w = w // animation_cols
            frame_h = h // animation_rows
            sprite_path = path

        super().__init__(
            col,
            row,
            color,
            speed=default_speed,
            name=name,
            sprite_sheet_path=sprite_path,
            frame_size=(frame_w, frame_h),
            animation_rows=animation_rows,
            animation_cols=animation_cols,
            scale=2,
        )

        # Animal state
        self.alive = True
        self.crops_eaten = 0
        self.recent_crop_damage_timer = 0
        self.replan_cd = 0
        self.w_crop_value = 1.0
        self.w_guard_avoid = w_guard_avoid
        self._ate_this_tile = False
        self.season_mgr = None
        self.state = "hungry"
        self.stamina = self.STAMINA_MAX
        self.original_color = color
        self.scared_animation_timer = 0

        # A* visualization tracking
        self.last_explored_nodes = []
        self.nodes_expanded = 0
        self.path_cost = 0
        self.last_path = []

        # Genetic Algorithm - Chromosome (4 traits)
        self.chromosome = {
            "crop_attraction": random.uniform(0.5, 2.0),
            "guard_avoidance": random.uniform(0.5, 2.0),
            "speed": random.uniform(1.0, 2.5),
            "boldness": random.uniform(0.5, 2.0),
        }
        self._sync_chromosome()

        # Fitness tracking (lifetime across full year for GA)
        self.crops_eaten_this_season = 0
        self.lifetime_crops = 0
        self.survival_time = 0
        self.lifetime_survival = 0
        self.fitness = 0.0
        self.generation = 1

    # ============================================================
    # GENETIC ALGORITHM METHODS
    # ============================================================

    def _sync_chromosome(self):
        """Apply chromosome values to live agent attributes"""
        self.speed = self.chromosome.get("speed", self.speed)
        self.w_guard_avoid = self.chromosome.get("guard_avoidance", self.w_guard_avoid)
        self.w_crop_value = self.chromosome.get("crop_attraction", self.w_crop_value)

    def update_fitness(self):
        """Calculate fitness based on lifetime performance (entire year)"""
        self.fitness = self.lifetime_crops * 10 + self.lifetime_survival / 60.0
        return self.fitness

    def reset_for_new_year(self):
        """Reset counters at start of new year (after GA runs)"""
        self.crops_eaten_this_season = 0
        self.lifetime_crops = 0
        self.survival_time = 0
        self.lifetime_survival = 0
        self.fitness = 0.0

    def reset_for_new_season(self):
        """Reset seasonal display counters (keeps lifetime fitness)"""
        self.crops_eaten_this_season = 0
        self.survival_time = 0

    def apply_chromosome(self, new_chromosome):
        """Apply evolved chromosome after crossover/mutation"""
        self.chromosome = new_chromosome.copy()
        self._sync_chromosome()

    # ============================================================
    # VISUAL STATE
    # ============================================================

    def get_color(self):
        """Return color based on current state"""
        if self.state == "scared":
            return (
                (255, 0, 0)
                if (self.scared_animation_timer // 5) % 2 == 0
                else (200, 0, 0)
            )
        if self.state == "wandering":
            return (128, 128, 128)
        return self.original_color

    def draw(self, surface, font=None):
        """Draw animal with scared effects and stamina bar"""
        if self.state == "scared":
            self.scared_animation_timer += 1

        # Shake effect when scared
        offset_x = offset_y = 0
        if self.state == "scared":
            offset_x = random.randint(-4, 4)
            offset_y = random.randint(-4, 4)

        original_x, original_y = self.x, self.y
        self.x += offset_x
        self.y += offset_y

        # Red glow when scared
        if self.state == "scared":
            glow_radius = TILE_SIZE // 2 + 8
            for i in range(3):
                pygame.draw.circle(
                    surface,
                    (255, 0, 0),
                    (int(self.x), int(self.y)),
                    glow_radius - i * 2,
                )

            if font:
                exclaim = font.render("!!!", True, (255, 0, 0))
                exclaim_shadow = font.render("!!!", True, (100, 0, 0))
                ey = int(self.y) - TILE_SIZE // 2 - 45
                surface.blit(
                    exclaim_shadow, (int(self.x) - exclaim.get_width() // 2 + 2, ey + 2)
                )
                surface.blit(exclaim, (int(self.x) - exclaim.get_width() // 2, ey))

        super().draw(surface, font)

        # Red border when scared
        if self.state == "scared":
            rect = pygame.Rect(
                int(self.x) - TILE_SIZE // 2 - 2,
                int(self.y) - TILE_SIZE // 2 - 2,
                TILE_SIZE + 4,
                TILE_SIZE + 4,
            )
            pygame.draw.rect(surface, (255, 0, 0), rect, 3)

            corner_offset = 8
            for cx, cy in [
                (int(self.x) - corner_offset, int(self.y) - corner_offset),
                (int(self.x) + corner_offset, int(self.y) - corner_offset),
                (int(self.x) - corner_offset, int(self.y) + corner_offset),
                (int(self.x) + corner_offset, int(self.y) + corner_offset),
            ]:
                pygame.draw.line(
                    surface, (255, 0, 0), (cx - 5, cy - 5), (cx + 5, cy + 5), 2
                )
                pygame.draw.line(
                    surface, (255, 0, 0), (cx + 5, cy - 5), (cx - 5, cy + 5), 2
                )

        self.x, self.y = original_x, original_y

        # Scared text
        if self.state == "scared" and font:
            scared_text = font.render("SCARED!", True, (255, 255, 255))
            scared_bg = font.render("SCARED!", True, (255, 0, 0))
            sx = int(self.x) - scared_text.get_width() // 2
            sy = int(self.y) - TILE_SIZE // 2 - 35
            for ox, oy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
                surface.blit(scared_bg, (sx + ox, sy + oy))
            surface.blit(scared_text, (sx, sy))

        # Stamina bar (only when scared)
        if self.state == "scared":
            bar_w = TILE_SIZE
            bar_h = 6
            pct = max(0, self.stamina / self.STAMINA_MAX)
            bx = int(self.x) - bar_w // 2
            by = int(self.y) - TILE_SIZE // 2 - 25
            pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, bar_h))
            bar_color = (255, 100, 0) if pct > 0.3 else (255, 0, 0)
            pygame.draw.rect(surface, bar_color, (bx, by, int(bar_w * pct), bar_h))
            if font:
                st = font.render(f"{int(pct * 100)}%", True, (255, 255, 255))
                surface.blit(st, (bx + bar_w // 2 - st.get_width() // 2, by - 12))

        # Wandering indicator
        if self.state == "wandering" and font:
            wt = font.render("?", True, (150, 150, 150))
            surface.blit(
                wt,
                (int(self.x) - wt.get_width() // 2, int(self.y) - TILE_SIZE // 2 - 25),
            )

    # ============================================================
    # MOVEMENT & NAVIGATION
    # ============================================================

    def caught(self):
        """Animal caught by guard"""
        self.alive = False
        self.state = "caught"
        self.moving = False
        self.path = []
        print(f"Guard caught {self.name} at ({self.col}, {self.row})")

    def _is_valid_step(self, tile, rain_active=False):
        """Check if tile is walkable"""
        if tile is None:
            return False
        return tile.type not in (TILE_WATER, TILE_STONE, TILE_SNOW_STONE)

    def _can_step(self, grid, col, row):
        """Check if animal can step on tile"""
        if not grid or col < 0 or col >= grid.cols or row < 0 or row >= grid.rows:
            return False
        tile = grid.get(col, row)
        rain_active = self.season_mgr is not None and self.season_mgr.rain_active
        return self._is_valid_step(tile, rain_active)

    def _nearest_valid_tile(self, grid, col, row):
        """Find nearest walkable tile"""
        if grid:
            col = max(0, min(grid.cols - 1, col))
            row = max(0, min(grid.rows - 1, row))

        start = grid.get(col, row)
        rain_active = self.season_mgr is not None and self.season_mgr.rain_active
        if start and self._is_valid_step(start, rain_active):
            return col, row

        for radius in range(1, 6):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if abs(dc) + abs(dr) != radius:
                        continue
                    nc, nr = col + dc, row + dr
                    if grid and (
                        nc < 0 or nc >= grid.cols or nr < 0 or nr >= grid.rows
                    ):
                        continue
                    if self._is_valid_step(grid.get(nc, nr)):
                        return nc, nr
        return col, row

    def respawn(self, col, row, grid=None):
        """Respawn animal at new position"""
        if grid is not None:
            col, row = self._nearest_valid_tile(grid, col, row)
        self.alive = True
        self.col = col
        self.row = row
        self.crops_eaten = 0
        self.crops_eaten_this_season = 0
        self.lifetime_crops = 0
        self.recent_crop_damage_timer = 0
        cx, cy = tile_center(col, row)
        self.x = float(cx)
        self.y = float(cy)
        self.state = "hungry"
        self.path = []
        self.path_idx = 0
        self.moving = False
        self._ate_this_tile = False
        self.replan_cd = 0
        self.stamina = self.STAMINA_MAX
        print(f"{self.name} respawned at ({col}, {row})")

    def ensure_valid_position(self, grid):
        """Ensure animal is on a walkable tile"""
        if not grid:
            return
        self.col = max(0, min(grid.cols - 1, self.col))
        self.row = max(0, min(grid.rows - 1, self.row))
        tile = grid.get(self.col, self.row)
        if tile and self._is_valid_step(tile):
            return
        nc, nr = self._nearest_valid_tile(grid, self.col, self.row)
        self.col, self.row = nc, nr
        cx, cy = tile_center(self.col, self.row)
        self.x = float(cx)
        self.y = float(cy)
        self.path = []
        self.path_idx = 0
        self.moving = False

    # ============================================================
    # A* PATHFINDING
    # ============================================================

    def _astar(self, grid, target):
        """Run A* and store visualization data"""
        rain_active = self.season_mgr is not None and self.season_mgr.rain_active
        result = astar(
            grid,
            (self.col, self.row),
            target,
            cost_dict=ANIMAL_COSTS,
            agent_type="Animal",
            rain_active=rain_active,
        )
        if result.path:
            self.set_path(result.path, result.explored)
            self.last_explored_nodes = list(getattr(result, "explored", []))
            self.nodes_expanded = getattr(result, "nodes_expanded", 0)
            self.path_cost = getattr(result, "cost", 0)
            self.last_path = list(getattr(result, "path", []))
        return result

    def _plan_wander(self, grid):
        """Plan random wander path"""
        if not grid:
            return False
        rain_active = self.season_mgr is not None and self.season_mgr.rain_active
        for _ in range(5):
            nc = max(0, min(grid.cols - 1, self.col + random.randint(-3, 3)))
            nr = max(0, min(grid.rows - 1, self.row + random.randint(-3, 3)))
            if not self._is_valid_step(grid.get(nc, nr), rain_active):
                continue
            result = self._astar(grid, (nc, nr))
            if result.path:
                return True
        return False

    def _wander(self, grid):
        """Extended wander with more attempts"""
        if not grid:
            return False
        rain_active = self.season_mgr is not None and self.season_mgr.rain_active
        for _ in range(15):
            nc = max(0, min(grid.cols - 1, self.col + random.randint(-4, 4)))
            nr = max(0, min(grid.rows - 1, self.row + random.randint(-4, 4)))
            if not self._is_valid_step(grid.get(nc, nr), rain_active):
                continue
            if (nc, nr) != (self.col, self.row):
                result = self._astar(grid, (nc, nr))
                if result.path:
                    return True
        return False

    def _flee_from_guard(self, grid, guard):
        """Move away from guard"""
        if not guard or not grid:
            return
        dx = self.col - guard.col
        dy = self.row - guard.row
        dist = max(1, abs(dx) + abs(dy))
        tc = max(0, min(grid.cols - 1, self.col + int(dx / dist * 5)))
        tr = max(0, min(grid.rows - 1, self.row + int(dy / dist * 5)))
        result = self._astar(grid, (tc, tr))
        if not result.path:
            self._wander(grid)

    def _pick_target(self, grid, agents):
        """Select best crop target based on chromosome traits"""
        if not grid:
            return None
        guard = next((a for a in agents if a.__class__.__name__ == "Guard"), None)

        best_score = -1
        best_tile = None

        for c, r in grid.crop_tiles():
            tile = grid.get(c, r)
            if tile is None or tile.crop == CROP_NONE:
                continue

            value = CROP_VALUE[tile.crop] * self.chromosome.get("crop_attraction", 1.0)
            dist = manhattan((self.col, self.row), (c, r)) + 1

            guard_penalty = 0
            if guard:
                gd = manhattan((c, r), (guard.col, guard.row)) + 1
                guard_penalty = self.chromosome.get("guard_avoidance", 1.0) * (10 / gd)

            score = (value / dist) - guard_penalty
            if score > best_score:
                best_score = score
                best_tile = (c, r)

        return best_tile

    # ============================================================
    # EATING & BEHAVIOR
    # ============================================================

    def _eat(self, grid):
        """Eat crop at current tile"""
        if self.moving or not grid:
            return False

        tile = grid.get(self.col, self.row)
        if tile and tile.crop != CROP_NONE:
            crop_name = CROP_NAMES[tile.crop]

            if not self._ate_this_tile:
                if self.animal_type == "rabbit":
                    # Rabbit nibbles - reduces stage by 1
                    if tile.crop_stage > 0:
                        original_crop = tile.crop
                        crop_name = CROP_NAMES.get(original_crop, original_crop)
                        tile.crop_stage -= 1
                        self.crops_eaten += 1
                        self.crops_eaten_this_season += 1
                        self.lifetime_crops += 1
                        self.recent_crop_damage_timer = 8 * FPS
                        self.score += CROP_VALUE[original_crop]
                        self._ate_this_tile = True
                        print(
                            f"Rabbit ate {crop_name} at ({self.col}, {self.row}); stage is now {tile.crop_stage}"
                        )
                        if tile.crop_stage <= 0:
                            tile.crop = CROP_NONE
                            tile.crop_stage = 0
                        return True
                else:
                    # Fox destroys crop
                    original_crop = tile.crop
                    original_stage = tile.crop_stage
                    crop_name = CROP_NAMES.get(original_crop, original_crop)
                    self.crops_eaten += 1
                    self.crops_eaten_this_season += 1
                    self.lifetime_crops += 1
                    self.recent_crop_damage_timer = 8 * FPS
                    self.score += CROP_VALUE[original_crop] * max(1, original_stage)
                    tile.crop = CROP_NONE
                    tile.crop_stage = 0
                    self._ate_this_tile = True
                    print(
                        f"Fox destroyed {crop_name} at ({self.col}, {self.row}) from stage {original_stage}"
                    )
                    return True
        else:
            self._ate_this_tile = False
        return False

    # ============================================================
    # UPDATE LOOP
    # ============================================================

    def update(self, grid, agents, season_mgr=None):
        """Main update loop for animal"""
        if season_mgr:
            self.season_mgr = season_mgr
        if not self.alive or not grid:
            return

        # Track survival time for fitness
        self.survival_time += 1
        self.lifetime_survival += 1

        self.ensure_valid_position(grid)
        super().update(grid, agents, season_mgr)
        self.replan_cd = max(0, self.replan_cd - 1)
        self.recent_crop_damage_timer = max(0, self.recent_crop_damage_timer - 1)
        self.color = self.get_color()
        self._eat(grid)

        # Guard proximity detection
        guard = next((a for a in agents if a.__class__.__name__ == "Guard"), None)
        if guard:
            dist = manhattan((self.col, self.row), (guard.col, guard.row))
            flee_dist = self.FLEE_DISTANCE * self.chromosome.get("boldness", 1.0)
            if dist <= flee_dist:
                self.state = "scared"
                self.stamina = max(0, self.stamina - self.STAMINA_DRAIN)
                self.speed = 1.0 if self.stamina == 0 else 2.2
            else:
                self.state = "hungry"
                self.stamina = min(self.STAMINA_MAX, self.stamina + 1)
                self.speed = self.chromosome.get(
                    "speed", 1.7 if self.animal_type == "rabbit" else 1.6
                )

        if self.moving or self.replan_cd > 0:
            return

        self._ate_this_tile = False

        if self.state == "scared":
            self._flee_from_guard(grid, guard)
            self.replan_cd = 5
        elif self.state == "hungry":
            target = self._pick_target(grid, agents)
            if target:
                result = self._astar(grid, target)
                self.replan_cd = 60 if result.path else 45
                if not result.path:
                    self.state = "wandering"
                    self._plan_wander(grid)
            else:
                self.state = "wandering"
                self._plan_wander(grid)
                self.replan_cd = 90
        else:
            self._plan_wander(grid)
            self.replan_cd = 45
