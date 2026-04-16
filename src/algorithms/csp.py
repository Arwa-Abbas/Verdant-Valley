"""
CSP Farm Layout Planner - Fixed for better crop placement
"""

import random
from utils.constants import *
from utils.helpers import manhattan


class CSPSolver:
    def __init__(self, grid):
        self.grid = grid
        self.vars = grid.field_tiles()
        self.water = grid.water_sources()
        self.assign = {}
        self.log = []

        print(f"Water sources found: {len(self.water)}")
        print(f"Field tiles found: {len(self.vars)}")

        # Find field boundaries
        if self.vars:
            cols = [c for c, r in self.vars]
            rows = [r for c, r in self.vars]
            self.min_c, self.max_c = min(cols), max(cols)
            self.min_r, self.max_r = min(rows), max(rows)
        else:
            self.min_c = self.max_c = self.min_r = self.max_r = 0

    def _is_edge(self, col, row):
        return (
            col == self.min_c
            or col == self.max_c
            or row == self.min_r
            or row == self.max_r
        )

    def _near_water(self, col, row, radius=4):
        # Expanded radius to 4 for better coverage
        for wc, wr in self.water:
            if manhattan((col, row), (wc, wr)) <= radius:
                return True
        return False

    def solve(self):
        """Fast greedy CSP solver"""
        print(f"Solving CSP for {len(self.vars)} field tiles...")

        # First, mark all tiles as unassigned
        for var in self.vars:
            self.assign[var] = CROP_NONE

        # Calculate target (40% planting for better gameplay)
        target_planted = max(1, int(len(self.vars) * 0.4))
        planted = 0

        print(f"Target planted crops: {target_planted}")

        # Sort variables by priority (edge tiles first for sunflowers)
        edge_tiles = [v for v in self.vars if self._is_edge(v[0], v[1])]
        inner_tiles = [v for v in self.vars if not self._is_edge(v[0], v[1])]

        print(f"Edge tiles: {len(edge_tiles)}, Inner tiles: {len(inner_tiles)}")

        # Plant sunflowers on edges first
        for col, row in edge_tiles:
            if planted >= target_planted:
                break
            # Check near water (with relaxed condition)
            near_water = self._near_water(col, row)
            if near_water or random.random() > 0.3:  # Allow some crops not near water
                # Check no adjacent sunflower
                adjacent_free = True
                for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if self.assign.get((col + dc, row + dr)) == CROP_SUNFLOWER:
                        adjacent_free = False
                        break
                if adjacent_free and random.random() > 0.5:  # 50% chance for sunflower
                    self.assign[(col, row)] = CROP_SUNFLOWER
                    self.log.append((col, row, CROP_SUNFLOWER, "assign"))
                    planted += 1
                    print(
                        f"Planted Sunflower at ({col},{row}) - {planted}/{target_planted}"
                    )

        # Plant corn and wheat in remaining spots
        all_tiles = edge_tiles + inner_tiles
        random.shuffle(all_tiles)  # Shuffle for variety

        for col, row in all_tiles:
            if planted >= target_planted:
                break
            if self.assign[(col, row)] == CROP_NONE:
                # 70% chance to plant a crop
                if random.random() > 0.3:
                    # Choose crop based on position
                    if self._is_edge(col, row):
                        crop = random.choice([CROP_CORN, CROP_SUNFLOWER])
                    else:
                        crop = random.choice([CROP_WHEAT, CROP_CORN, CROP_WHEAT])

                    self.assign[(col, row)] = crop
                    self.log.append((col, row, crop, "assign"))
                    planted += 1
                    print(
                        f"Planted {CROP_NAMES[crop]} at ({col},{row}) - {planted}/{target_planted}"
                    )

        # Final pass - fill remaining spots to meet target if needed
        if planted < target_planted:
            print(f"Need {target_planted - planted} more crops, final pass...")
            for col, row in all_tiles:
                if planted >= target_planted:
                    break
                if self.assign[(col, row)] == CROP_NONE:
                    crop = random.choice([CROP_WHEAT, CROP_CORN])
                    self.assign[(col, row)] = crop
                    self.log.append((col, row, crop, "assign"))
                    planted += 1

        # Log final assignments
        for (col, row), crop in self.assign.items():
            if crop != CROP_NONE:
                self.log.append((col, row, crop, "final"))

        print(f"CSP Complete: Planted {planted} crops (target: {target_planted})")
        return True

    def apply_to_grid(self):
        """Write the solved assignment back to the grid tiles."""
        for (col, row), crop in self.assign.items():
            if 0 <= col < self.grid.cols and 0 <= row < self.grid.rows:
                self.grid.tiles[col][row].crop = crop
                if crop != CROP_NONE:
                    self.grid.tiles[col][row].crop_stage = random.randint(1, 2)
