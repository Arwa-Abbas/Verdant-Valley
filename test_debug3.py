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

print(f"Analyzing candidate positions:")
solver.refresh_grid_context()
solver._init_domains()
solver.assign = {var: None for var in solver.vars}
solver._refresh_domains_for_search(test_counts)

print(f"\nCorn candidates:")
corn_candidates = solver._candidate_positions_for_crop(CROP_CORN)
print(f"  Total candidates: {len(corn_candidates)}")
print(f"  First 10: {corn_candidates[:10]}")
print(f"  Can place 5? {len(corn_candidates) >= 5}")

print(f"\nCarrot candidates:")
carrot_candidates = solver._candidate_positions_for_crop(CROP_CARROT)
print(f"  Total candidates: {len(carrot_candidates)}")
print(f"  First 10: {carrot_candidates[:10]}")
print(f"  Can place 5? {len(carrot_candidates) >= 5}")

print(f"\nCombined available after placing both:")
remaining_after_corn = len([p for p in carrot_candidates if p not in corn_candidates[:5]])
print(f"  Unique carrot positions: {remaining_after_corn}")
