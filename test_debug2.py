import sys
import time
from src.world.environment.grid import Grid
from src.algorithms.csp import CSPSolver
from utils.constants import *

# Suppress pygame warnings
import warnings
warnings.filterwarnings("ignore")

grid = Grid()
solver = CSPSolver(grid)
solver.set_mode("manual")

test_counts = {
    CROP_WHEAT: 0,
    CROP_SUNFLOWER: 0,
    CROP_CORN: 5,
    CROP_TOMATO: 0,
    CROP_CARROT: 5,
}

print(f"Testing _build_constrained_crop_slots:")
solver.refresh_grid_context()
solver._init_domains()
solver.assign = {var: None for var in solver.vars}

constrained_slots = solver._build_constrained_crop_slots(test_counts)
print(f"  Constrained slots: {constrained_slots}")
print(f"  Number of constrained slots: {len(constrained_slots)}")

# Check the constrained_counts
constrained_counts = {
    crop: test_counts.get(crop, 0)
    for crop in (CROP_SUNFLOWER, CROP_TOMATO, CROP_WHEAT)
}
print(f"  Constrained counts (SUNFLOWER, TOMATO, WHEAT): {constrained_counts}")
print(f"  Will run backtracking search: {bool(constrained_slots)}")

# Check _fill_remaining_easy_crops
print(f"\nTesting remaining easy crops logic:")
remaining_counts = dict(test_counts)
for crop in (CROP_SUNFLOWER, CROP_TOMATO, CROP_WHEAT):
    remaining_counts[crop] = 0
print(f"  Remaining easy crop counts: {remaining_counts}")
print(f"  Crops to fill: CORN={remaining_counts[CROP_CORN]}, CARROT={remaining_counts[CROP_CARROT]}")
