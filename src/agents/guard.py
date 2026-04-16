import random
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan


class Guard(Agent):
    """
    Guard agent.
    States: 'patrol' — cycles through waypoints using A*
            'chase'  — chases the nearest animal using A*
    """

    ALERT_RADIUS = 5
    RETURN_RADIUS = 8

    def __init__(self, col, row):
        super().__init__(col, row, C_GUARD, speed=1.8, name="Guard")
        self.state = "patrol"
        self.waypoints = []
        self.wp_index = 0
        self.chase_target = None
        self.replan_cd = 0

    def set_waypoints(self, waypoints):
        self.waypoints = waypoints
        self.wp_index = 0

    def _nearest_animal(self, agents):
        animals = [a for a in agents if a.__class__.__name__ == "Animal" and a.alive]
        if not animals:
            return None
        return min(
            animals, key=lambda a: manhattan((self.col, self.row), (a.col, a.row))
        )

    def _plan_to(self, grid, goal):
        result = astar(grid, (self.col, self.row), goal)
        if result.path:
            self.set_path(result.path, result.explored)

    def update(self, grid, agents):
        super().update(grid, agents)
        self.replan_cd = max(0, self.replan_cd - 1)

        nearest = self._nearest_animal(agents)

        # Chase logic
        if nearest:
            dist = manhattan((self.col, self.row), (nearest.col, nearest.row))
            if dist <= self.ALERT_RADIUS:
                self.state = "chase"
                self.chase_target = nearest
            elif self.state == "chase" and dist > self.RETURN_RADIUS:
                self.state = "patrol"
                self.chase_target = None

        if self.state == "chase" and self.chase_target and self.chase_target.alive:
            if self.replan_cd == 0:
                self._plan_to(grid, (self.chase_target.col, self.chase_target.row))
                self.replan_cd = 20
            # Catch animal
            if (self.col, self.row) == (self.chase_target.col, self.chase_target.row):
                self.chase_target.caught()
                self.state = "patrol"
                self.chase_target = None
                print("Guard caught the animal!")
            return

        # Patrol logic
        self.state = "patrol"
        if not self.waypoints:
            return

        if not self.moving or self.path_idx >= len(self.path):
            goal = self.waypoints[self.wp_index % len(self.waypoints)]
            self._plan_to(grid, goal)
            self.wp_index += 1
