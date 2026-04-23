"""
CSP Farm Layout Planner

Uses per-tile domains, flooded/muddy state, and utility-based heuristics
so the solver respects hard constraints (flooded tiles => CROP_NONE)
and prefers higher-utility tiles.
"""

import random
from utils.constants import *
from utils.helpers import manhattan


# Expected-value weights for heuristic ordering
CROP_HEURISTIC_VALUE = {
    CROP_WHEAT: 1.0,
    CROP_SUNFLOWER: 0.9,
    CROP_CORN: 1.3,
    CROP_TOMATO: 1.2,
    CROP_CARROT: 0.9,
    CROP_NONE: 0.0,
}


class CSPSolver:

    def set_requested_counts(self, requested_counts):
        """Set the requested crop counts for the solver."""
        self.requested_counts = (
            requested_counts if requested_counts is not None else self._default_counts()
        )

    def get_requested_counts(self):
        """Return the current requested crop counts dict."""
        return getattr(self, "requested_counts", self._default_counts())

    def __init__(self, grid):
        self.grid = grid
        self.refresh_grid_context()
        self.assign = {}
        self.log = []
        self.requested_counts = self._default_counts()
        self.mode = "manual"

        # Backtrack tracking for visualization
        self.backtrack_log = []  # Stores (col, row) of each backtrack
        self.domains = {}  # Stores current domains for each variable
        self._init_domains()  # Initialize domains

    def _init_domains(self):
        """Initialize domains for all variables."""
        for col, row in self.vars:
            tile = self.grid.get(col, row)
            if tile and tile.type == TILE_FIELD:
                self.domains[(col, row)] = [
                    CROP_WHEAT,
                    CROP_SUNFLOWER,
                    CROP_CORN,
                    CROP_TOMATO,
                    CROP_CARROT,
                    CROP_NONE,
                ]
            else:
                self.domains[(col, row)] = [CROP_NONE]

    def _default_counts(self):
        """Generate default crop counts based on total field tiles."""
        total_fields = len(self.vars)
        target_planted = max(1, int(total_fields * 0.4))
        sunflower = target_planted // 4
        corn = target_planted // 3
        tomato = target_planted // 5
        carrot = target_planted // 5
        wheat = max(0, target_planted - sunflower - corn - tomato - carrot)
        return {
            CROP_WHEAT: wheat,
            CROP_SUNFLOWER: sunflower,
            CROP_CORN: corn,
            CROP_TOMATO: tomato,
            CROP_CARROT: carrot,
        }

    def refresh_grid_context(self):
        """Pull fresh tile lists from the grid. Keep field tile coords even if temporarily pruned."""
        self.vars = self.grid.field_tiles()
        self.water = self.grid.water_sources()

        if self.vars:
            cols = [c for c, r in self.vars]
            rows = [r for c, r in self.vars]
            self.min_c, self.max_c = min(cols), max(cols)
            self.min_r, self.max_r = min(rows), max(rows)
        else:
            self.min_c = self.max_c = self.min_r = self.max_r = 0

    # Tile and domain helpers

    def _tile(self, pos):
        """Get tile at position."""
        col, row = pos
        return self.grid.get(col, row)

    def _get_season(self):
        """Get current season index (0=Spring, 1=Summer, 2=Autumn, 3=Winter)."""
        if hasattr(self.grid, "season") and self.grid.season:
            return getattr(self.grid.season, "index", 0)
        return 0  # Default to Spring

    def _get_allowed_crops_for_season(self):
        """Return list of crops allowed in current season."""
        season = self._get_season()

        # Spring, Summer, Autumn - all crops allowed
        if season != 3:  # Not winter
            return [CROP_WHEAT, CROP_SUNFLOWER, CROP_CORN, CROP_TOMATO, CROP_CARROT]
        else:  # Winter - only corn and carrot
            return [CROP_CORN, CROP_CARROT]

    def _tile_allows(self, pos, crop):
        """Return True when the tile can plant this crop."""
        tile = self._tile(pos)
        if tile is None:
            return False

        # Get allowed crops for current season
        allowed_crops = self._get_allowed_crops_for_season()

        # If crop is not allowed in this season, return False
        if crop not in allowed_crops:
            return False

        # For winter, Corn and Carrot are always allowed on field tiles
        season = self._get_season()
        if season == 3 and crop in (CROP_CORN, CROP_CARROT) and tile.type == TILE_FIELD:
            return True

        # For non-winter, check if tile is field or dirt
        if tile.type in (TILE_FIELD, TILE_DIRT):
            return True

        return False

    def _is_available(self, pos):
        """Available means not yet assigned and tile is plantable."""
        assigned = self.assign.get(pos, CROP_NONE)
        if assigned != CROP_NONE:
            return False

        tile = self._tile(pos)
        if not tile:
            return False

        # For winter, field tiles are always available for Corn/Carrot
        season = self._get_season()
        if season == 3 and tile.type == TILE_FIELD:
            return True

        # For non-winter, field and dirt tiles are available
        if tile.type in (TILE_FIELD, TILE_DIRT):
            return True

        return False

    def _is_edge(self, col, row):
        """Check if a tile is on the edge of the field area."""
        return (
            col == self.min_c
            or col == self.max_c
            or row == self.min_r
            or row == self.max_r
        )

    def _near_water(self, col, row, radius=4):
        """Check if tile is within radius of a water source."""
        for wc, wr in self.water:
            if manhattan((col, row), (wc, wr)) <= radius:
                return True
        return False

    def _has_adjacent_sunflower(self, col, row):
        """Check if there is an adjacent sunflower tile."""
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if self.assign.get((col + dc, row + dr)) == CROP_SUNFLOWER:
                return True
        return False

    # Candidate ordering utilities

    def _score_tile_for_crop(self, pos, crop):
        """Calculate a score for planting a specific crop on a tile."""
        tile = self._tile(pos)
        if not tile:
            return -9999

        base = CROP_HEURISTIC_VALUE.get(crop, 0.0)
        utility = getattr(tile, "utility", 0.5)
        score = base * utility

        if crop in (CROP_CORN, CROP_TOMATO) and self._near_water(
            pos[0], pos[1], radius=3
        ):
            score *= 1.08

        if getattr(tile, "muddy", False):
            score *= 0.85

        return score

    def _ordered_candidates(self, positions, crop, limit=None):
        """Return positions sorted by desirability for a given crop."""
        filtered = [
            p for p in positions if self._is_available(p) and self._tile_allows(p, crop)
        ]
        filtered.sort(key=lambda p: self._score_tile_for_crop(p, crop), reverse=True)
        if limit:
            return filtered[:limit]
        return filtered

    # Assignment routines

    def _assign_crop(self, positions, crop, limit):
        """Assign a crop to available positions with sunflower adjacency check."""
        placed = 0
        if limit <= 0:
            return 0

        candidates = self._ordered_candidates(positions, crop, limit * 3)
        for col, row in candidates:
            if placed >= limit:
                break
            if not self._is_available((col, row)):
                continue
            if crop == CROP_SUNFLOWER and self._has_adjacent_sunflower(col, row):
                continue
            if not self._tile_allows((col, row), crop):
                continue
            self.assign[(col, row)] = crop
            self.log.append((col, row, crop, "assign"))
            placed += 1
        return placed

    def _assign_crop_relaxed(self, positions, crop, limit):
        """Assign a crop to available positions without adjacency check."""
        placed = 0
        if limit <= 0:
            return 0

        candidates = self._ordered_candidates(positions, crop, limit * 3)
        for col, row in candidates:
            if placed >= limit:
                break
            if not self._is_available((col, row)):
                continue
            if not self._tile_allows((col, row), crop):
                continue
            self.assign[(col, row)] = crop
            self.log.append((col, row, crop, "assign"))
            placed += 1
        return placed

    # Auto solver (heuristic-driven)

    def _solve_auto(self):
        """Auto-solve mode - heuristic-driven crop placement."""
        if len(self.grid.crop_tiles()) > 0:
            return False

        season = self._get_season()
        is_winter = season == 3

        if is_winter:
            # Plant Corn and Carrot on ALL field tiles in winter
            field_tiles = list(self.vars)
            random.shuffle(field_tiles)

            planted = 0
            for idx, (col, row) in enumerate(field_tiles):
                crop = CROP_CORN if idx % 2 == 0 else CROP_CARROT
                self.assign[(col, row)] = crop
                self.log.append((col, row, crop, "assign"))
                planted += 1

            return True

        # Normal seasons (Spring, Summer, Autumn) - Plant all crop types
        target_planted = max(1, int(len(self.vars) * 0.5))
        planted = 0

        edge_tiles = [v for v in self.vars if self._is_edge(v[0], v[1])]
        inner_tiles = [v for v in self.vars if not self._is_edge(v[0], v[1])]

        # Plant Sunflowers on edge tiles
        sf_candidates = [v for v in edge_tiles if self._is_available(v)]
        sf_candidates.sort(
            key=lambda p: self._score_tile_for_crop(p, CROP_SUNFLOWER), reverse=True
        )

        for col, row in sf_candidates:
            if planted >= target_planted:
                break
            if self._has_adjacent_sunflower(col, row):
                continue
            if random.random() > 0.35:
                self.assign[(col, row)] = CROP_SUNFLOWER
                self.log.append((col, row, CROP_SUNFLOWER, "assign"))
                planted += 1

        # Fill remaining with random crops
        all_tiles = [v for v in edge_tiles + inner_tiles if self._is_available(v)]
        random.shuffle(all_tiles)

        crop_types = [CROP_WHEAT, CROP_CORN, CROP_TOMATO, CROP_CARROT]

        for col, row in all_tiles:
            if planted >= target_planted:
                break
            if self.assign.get((col, row), CROP_NONE) != CROP_NONE:
                continue
            crop = random.choice(crop_types)
            self.assign[(col, row)] = crop
            self.log.append((col, row, crop, "assign"))
            planted += 1

        return True

    # Public solve path (manual / requested)

    def solve(self, requested_counts=None):
        """Generate a grid layout using either auto mode or user-selected crop counts."""
        self.refresh_grid_context()

        # Reset backtrack tracking for new solve
        self.backtrack_log = []
        self._init_domains()

        if requested_counts is not None:
            self.set_requested_counts(requested_counts)

        # Initialize assignments
        self.assign = {}
        for var in self.vars:
            self.assign[var] = CROP_NONE

        self.log = []

        if self.mode == "auto":
            return self._solve_auto()

        # Manual mode with requested counts
        season = self._get_season()
        is_winter = season == 3
        requested = self.get_requested_counts()

        if is_winter:
            # Winter: Only plant Corn and Carrot
            corn_target = requested.get(CROP_CORN, 1)
            carrot_target = requested.get(CROP_CARROT, 1)

            if corn_target == 0 and carrot_target == 0:
                corn_target = 1
                carrot_target = 1

            field_tiles = list(self.vars)
            random.shuffle(field_tiles)

            corn_planted = 0
            carrot_planted = 0

            # Plant Corn first
            for col, row in field_tiles:
                if corn_planted < corn_target:
                    self.assign[(col, row)] = CROP_CORN
                    self.log.append((col, row, CROP_CORN, "assign"))
                    corn_planted += 1
                elif carrot_planted < carrot_target:
                    self.assign[(col, row)] = CROP_CARROT
                    self.log.append((col, row, CROP_CARROT, "assign"))
                    carrot_planted += 1

            total_planted = corn_planted + carrot_planted
            self.apply_to_grid()
            return total_planted > 0

        else:
            # Normal seasons - Plant all crop types
            target_planted = sum(requested.values())
            if target_planted == 0:
                target_planted = max(1, int(len(self.vars) * 0.5))

            planted = 0

            # Plant Sunflowers first
            sunflower_target = requested.get(CROP_SUNFLOWER, 0)
            if sunflower_target > 0:
                field_tiles = [
                    (c, r) for c, r in self.vars if self._is_available((c, r))
                ]
                random.shuffle(field_tiles)
                for col, row in field_tiles[:sunflower_target]:
                    if self._is_available((col, row)) and self._is_edge(col, row):
                        self.assign[(col, row)] = CROP_SUNFLOWER
                        self.log.append((col, row, CROP_SUNFLOWER, "assign"))
                        planted += 1

            # Plant Corn
            corn_target = requested.get(CROP_CORN, 0)
            if corn_target > 0:
                field_tiles = [
                    (c, r) for c, r in self.vars if self._is_available((c, r))
                ]
                random.shuffle(field_tiles)
                for col, row in field_tiles[:corn_target]:
                    if self._is_available((col, row)):
                        self.assign[(col, row)] = CROP_CORN
                        self.log.append((col, row, CROP_CORN, "assign"))
                        planted += 1

            # Plant Tomato
            tomato_target = requested.get(CROP_TOMATO, 0)
            if tomato_target > 0:
                field_tiles = [
                    (c, r) for c, r in self.vars if self._is_available((c, r))
                ]
                random.shuffle(field_tiles)
                for col, row in field_tiles[:tomato_target]:
                    if self._is_available((col, row)):
                        self.assign[(col, row)] = CROP_TOMATO
                        self.log.append((col, row, CROP_TOMATO, "assign"))
                        planted += 1

            # Plant Carrot
            carrot_target = requested.get(CROP_CARROT, 0)
            if carrot_target > 0:
                field_tiles = [
                    (c, r) for c, r in self.vars if self._is_available((c, r))
                ]
                random.shuffle(field_tiles)
                for col, row in field_tiles[:carrot_target]:
                    if self._is_available((col, row)):
                        self.assign[(col, row)] = CROP_CARROT
                        self.log.append((col, row, CROP_CARROT, "assign"))
                        planted += 1

            # Plant Wheat last
            wheat_target = requested.get(CROP_WHEAT, 0)
            if wheat_target > 0:
                field_tiles = [
                    (c, r) for c, r in self.vars if self._is_available((c, r))
                ]
                random.shuffle(field_tiles)
                for col, row in field_tiles[:wheat_target]:
                    if self._is_available((col, row)):
                        self.assign[(col, row)] = CROP_WHEAT
                        self.log.append((col, row, CROP_WHEAT, "assign"))
                        planted += 1

            # Fill remaining with NONE
            for col, row in self.vars:
                if self.assign.get((col, row), CROP_NONE) == CROP_NONE:
                    self.assign[(col, row)] = CROP_NONE

            self.apply_to_grid()
            return planted > 0

    # Apply assignment to the grid

    def apply_to_grid(self):
        """Write the solved assignment back to the grid tiles."""
        # Clear all crops first
        for col in range(self.grid.cols):
            for row in range(self.grid.rows):
                self.grid.tiles[col][row].crop = CROP_NONE
                self.grid.tiles[col][row].crop_stage = 0

        placed_count = 0
        for (col, row), crop in self.assign.items():
            if 0 <= col < self.grid.cols and 0 <= row < self.grid.rows:
                if crop != CROP_NONE:
                    self.grid.tiles[col][row].crop = crop
                    self.grid.tiles[col][row].crop_stage = 2
                    placed_count += 1

    def set_mode(self, mode):
        """Set solver mode to 'auto' or 'manual'."""
        if mode not in ("auto", "manual"):
            raise ValueError(f"Unsupported CSP mode: {mode}")
        self.mode = mode

    def get_mode(self):
        """Get current solver mode."""
        return self.mode

    def available_field_count(self):
        """Return the number of available field tiles."""
        return len(self.vars) if hasattr(self, "vars") else 0

    def get_backtrack_log(self):
        """Return backtrack log for visualization."""
        return self.backtrack_log

    def get_domains(self):
        """Return current domains for visualization."""
        return self.domains
