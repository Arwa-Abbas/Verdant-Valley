"""
src/agents/guard.py - Guard Agent

Patrols waypoints, detects animals within alert radius, chases them,
and catches them. Stamina system affects chase speed.
"""

import random
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan, tile_center


class Guard(Agent):
    ALERT_RADIUS = 10
    RETURN_RADIUS = 15
    CHASE_REPLAN_FRAMES = 5
    PATROL_REPLAN_FRAMES = 30
    GIVE_UP_TIME = 30 * 60
    STAMINA_MAX = 100
    STAMINA_DRAIN = 1
    STAMINA_RECOVER = 2

    def draw_failed_move_indicator(self, surface, grid):
        """Draw a cross on the last failed tile if timer is active."""
        self.show_blocked_cross(surface, grid)

    def show_blocked_cross(self, surface, grid):
        """Draw a cross on the last failed tile if timer is active."""
        if (
            getattr(self, "_failed_move_tile", None) is not None
            and getattr(self, "_failed_move_timer", 0) > 0
        ):
            from game_ui.game_ui import draw_blocked_tile_cross

            tile = self._failed_move_tile
            if isinstance(tile, tuple) and len(tile) == 2:
                col, row = tile
                draw_blocked_tile_cross(surface, col, row, grid)

    def _show_failed_move(self, tile_pos=None):
        """Mark a tile as failed and start the failure indicator timer."""
        self._failed_move_tile = (
            tile_pos if tile_pos is not None else (self.col, self.row)
        )
        self._failed_move_timer = 60

    def update_failed_move_timer(self):
        """Decrement the failed move timer and clear the indicator when it reaches zero."""
        if hasattr(self, "_failed_move_timer") and self._failed_move_timer > 0:
            self._failed_move_timer -= 1
        if hasattr(self, "_failed_move_timer") and self._failed_move_timer == 0:
            self._failed_move_tile = None

    def __init__(self, col, row, color=C_GUARD):
        import os
        import pygame

        path = "assets/agents/guard/guard.png"
        frame_w, frame_h = 16, 16

        if os.path.exists(path):
            img = pygame.image.load(path)
            w, h = img.get_size()
            frame_w = w // 4
            frame_h = h // 4

        Agent.__init__(
            self,
            col,
            row,
            color,
            speed=2.2,
            name="Guard",
            sprite_sheet_path=path if os.path.exists(path) else None,
            frame_size=(frame_w, frame_h),
            animation_rows=4,
            animation_cols=4,
            scale=2,
        )
        self.state = "patrol"
        self.waypoints = []
        self.wp_index = 0
        self.chase_target = None
        self.replan_cd = 0
        self._stuck_ticks = 0
        self._last_pos = (col, row)
        self.chase_start_time = 0
        self.stamina = self.STAMINA_MAX
        self.original_color = C_GUARD

        # Visualization data for pathfinding
        self.last_explored_nodes = []
        self.nodes_expanded = 0
        self.path_cost = 0
        self.last_path = []

    def get_color(self):
        """Return the agent's color based on current state and stamina."""
        if self.state == "chase":
            if self.stamina < self.STAMINA_MAX // 2:
                return (255, 100, 100)
            return (255, 165, 0)
        elif self.state == "alert":
            return (255, 255, 0)
        return self.original_color

    def set_waypoints(self, waypoints):
        """Set the patrol waypoints for the guard."""
        self.waypoints = waypoints
        self.wp_index = 0

    def _nearest_animal(self, agents):
        """Find the closest alive animal to the guard."""
        animals = [a for a in agents if a.__class__.__name__ == "Animal" and a.alive]
        if not animals:
            return None
        return min(
            animals, key=lambda a: manhattan((self.col, self.row), (a.col, a.row))
        )

    def _plan_to(self, grid, goal, season_mgr=None):
        """Plan a path to the specified goal using A*."""
        goal = self._resolve_goal(grid, goal)
        if goal is None:
            return False

        rain_active = season_mgr.rain_active if season_mgr else False
        result = astar(
            grid,
            (self.col, self.row),
            goal,
            agent_type="Guard",
            rain_active=rain_active,
        )

        # Store visualization data
        self.last_explored_nodes = list(getattr(result, "explored", []))
        self.nodes_expanded = getattr(result, "nodes_expanded", 0)
        self.path_cost = getattr(result, "cost", 0)
        self.last_path = getattr(result, "path", [])

        if getattr(result, "path", None):
            self.set_path(result.path, result.explored)
            self.moving = True
            return True
        return False

    def _is_valid_step(self, tile):
        """Check if a tile is valid for the guard to step on."""
        if tile is None:
            return False
        return GUARD_COSTS.get(tile.type, float("inf")) != float("inf")

    def _can_step(self, grid, col, row):
        """Check if the guard can step onto a given tile."""
        tile = grid.get(col, row)
        if not self._is_valid_step(tile):
            return False
        if getattr(tile, "flooded", False) or getattr(tile, "muddy", False):
            return False
        return True

    def _move_cost(self, tile):
        """Calculate movement cost for a tile, with penalty for crops."""
        if not self._is_valid_step(tile):
            return float("inf")
        cost = GUARD_COSTS.get(tile.type, 1.0)
        if tile.crop != CROP_NONE:
            cost += 1.5
        return cost

    def _resolve_goal(self, grid, goal):
        """Find the nearest passable tile to the goal if the goal itself is impassable."""
        gc, gr = goal
        t = grid.get(gc, gr)
        if self._is_valid_step(t):
            return goal

        for radius in range(1, 5):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if abs(dc) + abs(dr) != radius:
                        continue
                    nc, nr = gc + dc, gr + dr
                    n = grid.get(nc, nr)
                    if self._is_valid_step(n):
                        return (nc, nr)

        return None

    def _ensure_valid_position(self, grid):
        """If current tile is impassable, move to the nearest passable tile."""
        current_tile = grid.get(self.col, self.row)
        if self._is_valid_step(current_tile):
            return

        fallback = self._resolve_goal(grid, (self.col, self.row))
        if fallback is None:
            return

        self.col, self.row = fallback
        cx, cy = tile_center(self.col, self.row)
        self.x = float(cx)
        self.y = float(cy)
        self.path = []
        self.path_idx = 0
        self.moving = False

    def ensure_valid_position(self, grid):
        """Public wrapper for _ensure_valid_position."""
        self._ensure_valid_position(grid)

    def _move_directly_toward(self, grid, target_col, target_row):
        """
        Move directly toward a target when A* fails.
        Uses simple Manhattan direction prioritization.
        """
        dx = target_col - self.col
        dy = target_row - self.row

        if abs(dx) > abs(dy):
            next_col = self.col + (1 if dx > 0 else -1)
            next_row = self.row
        else:
            next_col = self.col
            next_row = self.row + (1 if dy > 0 else -1)

        tile = grid.get(next_col, next_row)
        if self._is_valid_step(tile):
            self.set_path([(next_col, next_row)], set())
        else:
            # Try the other direction if the first is blocked
            if abs(dx) > abs(dy):
                next_row = self.row + (1 if dy > 0 else -1)
            else:
                next_col = self.col + (1 if dx > 0 else -1)
            tile = grid.get(next_col, next_row)
            if self._is_valid_step(tile):
                self.set_path([(next_col, next_row)], set())

    def update(self, grid, agents, season_mgr=None):
        """Main update loop for the guard agent."""
        self._ensure_valid_position(grid)
        Agent.update(self, grid, agents, season_mgr)
        self.replan_cd = max(0, self.replan_cd - 1)

        # Track stuck state
        if (self.col, self.row) == self._last_pos:
            self._stuck_ticks += 1
        else:
            self._stuck_ticks = 0
            self._last_pos = (self.col, self.row)

        self.color = self.get_color()

        nearest = self._nearest_animal(agents)

        # State transition logic based on animal proximity
        if nearest and nearest.alive:
            dist = manhattan((self.col, self.row), (nearest.col, nearest.row))
            crop_damage = getattr(nearest, "recent_crop_damage_timer", 0) > 0
            crop_alert_radius = self.RETURN_RADIUS + 4
            near_enough = dist <= self.ALERT_RADIUS or (
                crop_damage and dist <= crop_alert_radius
            )

            if near_enough:
                if self.state == "patrol":
                    self.state = "alert"
                    self.replan_cd = 0
                elif self.state == "alert" and dist <= 5:
                    self.state = "chase"
                    self.chase_target = nearest
                    import pygame

                    self.chase_start_time = pygame.time.get_ticks()
                    self.replan_cd = 0
                elif self.state == "chase":
                    self.chase_target = nearest
            elif (
                self.state in ["alert", "chase"]
                and dist > self.RETURN_RADIUS
                and not crop_damage
            ):
                self.state = "patrol"
                self.chase_target = None
                self.replan_cd = 0

        # Alert state: move toward the animal
        if self.state == "alert":
            if nearest and nearest.alive:
                dist = manhattan((self.col, self.row), (nearest.col, nearest.row))
                if dist > 5 and self.replan_cd == 0:
                    self._plan_to(grid, (nearest.col, nearest.row), season_mgr)
                    self.replan_cd = 10
            return

        # Chase state: pursue the target animal
        if self.state == "chase" and self.chase_target and self.chase_target.alive:
            # Stamina management
            self.stamina = max(0, self.stamina - self.STAMINA_DRAIN)
            if self.stamina == 0:
                self.speed = 1.0
            else:
                self.speed = 2.2

            # Check if guard caught the animal
            if self.col == self.chase_target.col and self.row == self.chase_target.row:
                if (
                    hasattr(self.chase_target, "animal_type")
                    and self.chase_target.animal_type == "bear"
                ):
                    self.chase_target.alive = False
                    self.score = getattr(self, "score", 0) + 1
                    self.state = "patrol"
                    self.chase_target = None
                    return

            # Give up chase after timeout
            import pygame

            if pygame.time.get_ticks() - self.chase_start_time > self.GIVE_UP_TIME:
                self.state = "patrol"
                self.chase_target = None
                self.replan_cd = 0
                return

            # Catch on adjacent tile
            if (
                manhattan(
                    (self.col, self.row), (self.chase_target.col, self.chase_target.row)
                )
                <= 1
            ):
                self.chase_target.caught()
                self.score += 50
                self.state = "patrol"
                self.chase_target = None
                self._stuck_ticks = 0
                self.replan_cd = 0
                return
            else:
                # Force replan if stuck
                force_replan = self._stuck_ticks >= 60
                if force_replan:
                    self._stuck_ticks = 0
                    self.path = []
                    self.path_idx = 0
                    self.moving = False
                    self.replan_cd = 0

                should_replan = self.replan_cd == 0 and (
                    not self.moving
                    or not self.path
                    or self.path_idx >= max(0, len(self.path) - 2)
                    or force_replan
                )
                if should_replan:
                    ok = self._plan_to(
                        grid, (self.chase_target.col, self.chase_target.row), season_mgr
                    )
                    if not ok:
                        self._move_directly_toward(
                            grid, self.chase_target.col, self.chase_target.row
                        )
                    self.replan_cd = self.CHASE_REPLAN_FRAMES
                return

        # Patrol state: follow waypoints
        self.state = "patrol"
        self.stamina = min(self.STAMINA_MAX, self.stamina + self.STAMINA_RECOVER)
        self.speed = 2.2

        if not self.waypoints:
            return

        current_goal = self.waypoints[self.wp_index % len(self.waypoints)]

        # Move to next waypoint when current is reached
        if (self.col, self.row) == current_goal and not self.moving:
            self.wp_index = (self.wp_index + 1) % len(self.waypoints)
            current_goal = self.waypoints[self.wp_index % len(self.waypoints)]
            ok = self._plan_to(grid, current_goal, season_mgr)
            self.replan_cd = self.PATROL_REPLAN_FRAMES if ok else 10
        elif self.replan_cd == 0 and (
            not self.moving
            or not self.path
            or self.path_idx >= max(0, len(self.path) - 1)
        ):
            ok = self._plan_to(grid, current_goal, season_mgr)
            if ok:
                self.replan_cd = self.PATROL_REPLAN_FRAMES
            else:
                self.wp_index = (self.wp_index + 1) % len(self.waypoints)
                self.replan_cd = 10
