import random
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan


class Farmer(Agent):
    """
    AI Farmer agent.
    Uses A* to navigate to the highest-priority ripe crop and harvest it.
    """

    def __init__(self, col, row):
        super().__init__(col, row, C_FARMER, speed=2.0, name="Farmer")
        self.target = None
        self.replan_cd = 0

    def _pick_target(self, grid):
        """Choose the highest-utility ripe crop."""
        best_score = -1
        best_tile = None

        for c, r in grid.crop_tiles():
            tile = grid.get(c, r)
            if tile.crop_stage < 2:
                continue
            value = CROP_VALUE[tile.crop]
            dist = manhattan((self.col, self.row), (c, r)) + 1
            score = (value * tile.crop_stage) / dist
            if score > best_score:
                best_score = score
                best_tile = (c, r)

        return best_tile

    def _harvest(self, grid):
        tile = grid.get(self.col, self.row)
        if tile and tile.crop != CROP_NONE and tile.crop_stage >= 2:
            crop_name = CROP_NAMES[tile.crop]
            value = CROP_VALUE[tile.crop] * tile.crop_stage
            self.score += value
            print(
                f"Farmer harvested {crop_name}! +{value} points. Total score: {self.score}"
            )
            tile.crop = CROP_NONE
            tile.crop_stage = 0
            self.target = None

    def update(self, grid, agents):
        super().update(grid, agents)

        self.replan_cd = max(0, self.replan_cd - 1)

        # Harvest if standing on a ready crop
        self._harvest(grid)

        # Replan if idle or target disappeared
        if not self.moving or self.replan_cd == 0:
            new_target = self._pick_target(grid)
            if new_target and new_target != self.target:
                self.target = new_target
                result = astar(grid, (self.col, self.row), self.target)
                if result.path:
                    self.set_path(result.path, result.explored)
                    self.replan_cd = 90
                    self.state = "moving"
            elif not new_target:
                self.moving = False
                self.state = "idle"
            else:
                self.state = "harvesting"
