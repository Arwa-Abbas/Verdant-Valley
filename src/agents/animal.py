import random
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan


class Animal(Agent):
    """
    Animal / intruder agent.
    Navigates toward juicy crops while avoiding the Guard.
    """

    def __init__(self, col, row):
        super().__init__(col, row, C_ANIMAL, speed=1.5, name="Animal")
        self.alive = True
        self.crops_eaten = 0
        self.replan_cd = 0

        # Behavior weights
        self.w_crop_value = 1.0
        self.w_guard_avoid = 1.5

    def caught(self):
        self.alive = False
        self.state = "caught"
        self.moving = False
        print("Animal was caught!")

    def respawn(self, col, row):
        self.alive = True
        self.col = col
        self.row = row
        from utils.helpers import tile_center

        cx, cy = tile_center(col, row)
        self.px = float(cx)
        self.py = float(cy)
        self.state = "idle"
        self.path = []
        self.moving = False
        print(f"Animal respawned at ({col},{row})")

    def _pick_target(self, grid, agents):
        guard = next((a for a in agents if a.__class__.__name__ == "Guard"), None)

        best_score = -1
        best_tile = None

        for c, r in grid.crop_tiles():
            tile = grid.get(c, r)
            if tile.crop_stage < 1:
                continue
            value = CROP_VALUE[tile.crop] * self.w_crop_value
            dist = manhattan((self.col, self.row), (c, r)) + 1

            # Guard avoidance penalty
            guard_penalty = 0
            if guard:
                gd = manhattan((c, r), (guard.col, guard.row)) + 1
                guard_penalty = self.w_guard_avoid * (10 / gd)

            score = (value / dist) - guard_penalty
            if score > best_score:
                best_score = score
                best_tile = (c, r)

        return best_tile

    def _eat(self, grid):
        tile = grid.get(self.col, self.row)
        if tile and tile.crop != CROP_NONE:
            self.crops_eaten += 1
            self.score += CROP_VALUE[tile.crop] * tile.crop_stage
            print(f"Animal ate {CROP_NAMES[tile.crop]}! Score: {self.score}")
            tile.crop = CROP_NONE
            tile.crop_stage = 0

    def update(self, grid, agents):
        if not self.alive:
            return
        super().update(grid, agents)
        self.replan_cd = max(0, self.replan_cd - 1)

        self._eat(grid)

        if not self.moving or self.replan_cd == 0:
            target = self._pick_target(grid, agents)
            if target:
                result = astar(grid, (self.col, self.row), target)
                if result.path:
                    self.set_path(result.path, result.explored)
                    self.replan_cd = 60
            else:
                # Wander randomly
                for _ in range(5):
                    nc = self.col + random.randint(-3, 3)
                    nr = self.row + random.randint(-3, 3)
                    nc = max(0, min(grid.cols - 1, nc))
                    nr = max(0, min(grid.rows - 1, nr))
                    t = grid.get(nc, nr)
                    if t and t.walkable:
                        result = astar(grid, (self.col, self.row), (nc, nr))
                        if result.path:
                            self.set_path(result.path)
                            break
                self.replan_cd = 90
