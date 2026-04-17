"""
src/agents/farmer.py - Farmer Agent — full functionality
  - Terrain: walks mud/dirt/grass/field, blocked by water & stone
  - Plant mode: triggered externally via farmer.trigger_planting()
  - Crop growth: ticks over time per planted tile
  - Harvest: auto-harvests stage-2 crops using A*
"""

import random
from .base_agent import Agent
from src.algorithms.astar import astar
from utils.constants import *
from utils.helpers import manhattan


# ── Terrain passability ────────────────────────────────────────────────────
# Stone and water are impassable for the farmer.
# This dict is read by your A* cost function — make sure astar() calls
# grid.get(c,r).move_cost and returns float('inf') for impassable tiles.
FARMER_COSTS = {
    TILE_GRASS: 1.0,
    TILE_DIRT: 1.0,
    TILE_FIELD: 1.0,
    TILE_MUD: 3.0,  # slow but passable
    TILE_WATER: None,  # impassable
    TILE_STONE: None,  # impassable
}

# Planting score: how desirable is each tile type for planting?
PLANT_TILE_SCORE = {
    TILE_FIELD: 3.0,  # best — purpose-built farmland
    TILE_MUD: 2.0,  # decent
    TILE_DIRT: 1.0,  # okay
}

# Crops cycle through stages 0 (seed) → 1 (sprout) → 2 (ripe)
# Ticks needed to advance each stage (at 60 fps, 300 ticks ≈ 5 s)
CROP_GROWTH_TICKS = {
    CROP_WHEAT: (180, 300),  # stage0→1, stage1→2
    CROP_SUNFLOWER: (240, 360),
    CROP_CORN: (200, 320),
}


class Farmer(Agent):
    """
    AI Farmer — harvests ripe crops and plants new ones on command.

    External API:
        farmer.trigger_planting()   — call this from your UI button handler
    """

    def __init__(self, col, row):
        import os

        path = "assets/agents/farmer/farmer.png"
        super().__init__(
            col,
            row,
            C_FARMER,
            speed=2.0,
            name="Farmer",
            sprite_sheet_path=path if os.path.exists(path) else None,
            frame_size=(30, 30),
            animation_rows=6,
            animation_cols=6,
            scale=2,
        )

        self.target = None
        self.replan_cd = 0
        self.harvest_count = 0
        self.plant_count = 0

        # Planting mode — set True by trigger_planting(), cleared after done
        self._plant_requested = False
        self._planting_mode = False
        self._plant_queue = []  # list of (col, row) tiles to plant

        # Growth timers: {(col, row): ticks_at_current_stage}
        self._growth_timers: dict[tuple, int] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def trigger_planting(self):
        """Call from your UI 'Plant Crops' button handler."""
        self._plant_requested = True
        print("🌱 Farmer: planting requested")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _tile_passable(self, tile) -> bool:
        """True if the farmer can walk on this tile type."""
        return tile is not None and FARMER_COSTS.get(tile.type) is not None

    def _pick_harvest_target(self, grid):
        """Highest-utility ripe (stage=2) crop, weighted by value/distance."""
        best_score = -1
        best_tile = None
        for c, r in grid.crop_tiles():
            tile = grid.get(c, r)
            if tile is None or tile.crop == CROP_NONE or tile.crop_stage < 2:
                continue
            if not self._tile_passable(tile):
                continue
            value = CROP_VALUE[tile.crop]
            dist = manhattan((self.col, self.row), (c, r)) + 1
            score = (value * tile.crop_stage) / dist
            if score > best_score:
                best_score = score
                best_tile = (c, r)
        return best_tile

    def _pick_plant_tiles(self, grid) -> list[tuple[int, int]]:
        """
        Find plantable tiles sorted by desirability score:
          - tile must be TILE_FIELD / MUD / DIRT
          - no existing crop
          - must be reachable (A* sanity check skipped here — done at path time)
          - bonus for being adjacent to a water tile
        Returns up to 8 best candidates.
        """
        candidates = []
        for c in range(grid.cols):
            for r in range(grid.rows):
                tile = grid.get(c, r)
                if tile is None:
                    continue
                if tile.type not in PLANT_TILE_SCORE:
                    continue
                if tile.crop != CROP_NONE:
                    continue  # already has a crop
                if (c, r) in self._growth_timers:
                    continue  # seed planted, waiting to emerge

                base = PLANT_TILE_SCORE[tile.type]
                # Water adjacency bonus
                water_bonus = 0.0
                for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nb = grid.get(c + dc, r + dr)
                    if nb and nb.type == TILE_WATER:
                        water_bonus = 1.5
                        break
                dist = manhattan((self.col, self.row), (c, r)) + 1
                score = (base + water_bonus) / dist
                candidates.append((score, c, r))

        candidates.sort(reverse=True)
        return [(c, r) for _, c, r in candidates[:8]]

    def _choose_crop_for_tile(self, grid, c, r) -> int:
        """Pick the best crop for this tile (field → sunflower, mud → corn, dirt → wheat)."""
        tile = grid.get(c, r)
        if tile.type == TILE_FIELD:
            return CROP_SUNFLOWER  # highest value on good soil
        if tile.type == TILE_MUD:
            return CROP_CORN
        return CROP_WHEAT

    def _plant_at(self, grid, c, r):
        """Actually plant a seed on tile (c, r)."""
        tile = grid.get(c, r)
        if tile is None or tile.type not in PLANT_TILE_SCORE:
            return
        crop = self._choose_crop_for_tile(grid, c, r)
        tile.crop = crop
        tile.crop_stage = 0  # stage 0 = seed / just planted
        self._growth_timers[(c, r)] = 0
        self.plant_count += 1
        print(f"🌱 Farmer planted {CROP_NAMES[crop]} at ({c},{r})")

    def _harvest(self, grid):
        """Harvest ripe crop at current tile, if any."""
        tile = grid.get(self.col, self.row)
        if tile and tile.crop != CROP_NONE and tile.crop_stage >= 2:
            crop_name = CROP_NAMES[tile.crop]
            value = CROP_VALUE[tile.crop] * tile.crop_stage
            self.score += value
            self.harvest_count += 1
            print(f"🌾 Farmer harvested {crop_name}! +{value}  total={self.score}")
            tile.crop = CROP_NONE
            tile.crop_stage = 0
            self._growth_timers.pop((self.col, self.row), None)
            self.target = None
            self.state = "harvesting"

    def _tick_growth(self, grid):
        """Advance crop growth timers for all planted tiles."""
        done = []
        for (c, r), ticks in self._growth_timers.items():
            tile = grid.get(c, r)
            if tile is None or tile.crop == CROP_NONE:
                done.append((c, r))
                continue
            ticks += 1
            self._growth_timers[(c, r)] = ticks

            grow = CROP_GROWTH_TICKS.get(tile.crop, (240, 480))
            if tile.crop_stage == 0 and ticks >= grow[0]:
                tile.crop_stage = 1
                print(f"🌿 Crop sprouted at ({c},{r})")
            elif tile.crop_stage == 1 and ticks >= grow[1]:
                tile.crop_stage = 2
                print(f"🌻 Crop ripe at ({c},{r})!")
                done.append((c, r))  # stop tracking once ripe

        for key in done:
            self._growth_timers.pop(key, None)

    # ── Planting flow ─────────────────────────────────────────────────────────

    def _enter_planting_mode(self, grid):
        self._planting_mode = True
        self._plant_requested = False
        self._plant_queue = self._pick_plant_tiles(grid)
        self.state = "planting"
        print(
            f"🌱 Farmer entering planting mode — {len(self._plant_queue)} tiles queued"
        )

    def _update_planting(self, grid):
        """Navigate to the next tile in the plant queue and plant it."""
        # Remove tiles that now have crops (planted by CSP or another pass)
        self._plant_queue = [
            (c, r)
            for c, r in self._plant_queue
            if grid.get(c, r)
            and grid.get(c, r).crop == CROP_NONE
            and (c, r) not in self._growth_timers
        ]

        if not self._plant_queue:
            self._planting_mode = False
            self.state = "idle"
            print("✅ Farmer finished planting")
            return

        next_tile = self._plant_queue[0]

        # Already there → plant immediately
        if (self.col, self.row) == next_tile:
            self._plant_at(grid, *next_tile)
            self._plant_queue.pop(0)
            self.moving = False
            return

        # Need to walk there
        if not self.moving or self.replan_cd == 0:
            result = astar(grid, (self.col, self.row), next_tile)
            if result.path:
                self.set_path(result.path, result.explored)
                self.replan_cd = 60
            else:
                # Can't reach this tile — skip it
                print(f"⚠️ Farmer can't reach plant tile {next_tile}, skipping")
                self._plant_queue.pop(0)

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, grid, agents):
        super().update(grid, agents)
        self.replan_cd = max(0, self.replan_cd - 1)

        # Always tick growth, harvest if standing on ripe crop
        self._tick_growth(grid)
        self._harvest(grid)

        # Start planting if button was pressed
        if self._plant_requested and not self._planting_mode:
            self._enter_planting_mode(grid)
            return

        # Planting mode takes priority over harvesting
        if self._planting_mode:
            self._update_planting(grid)
            return

        # ── Harvest mode ──────────────────────────────────────────────────
        if not self.moving or self.replan_cd == 0:
            new_target = self._pick_harvest_target(grid)

            if new_target and new_target != self.target:
                self.target = new_target
                result = astar(grid, (self.col, self.row), self.target)
                if result.path:
                    self.set_path(result.path, result.explored)
                    self.replan_cd = 90
                    self.state = "moving"
                else:
                    self.state = "no_path"

            elif not new_target:
                self.moving = False
                self.state = "idle"
            else:
                self.state = "moving"
