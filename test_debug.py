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

print(f"Grid info:")
print(f"  Field tiles: {len(solver.vars)}")
print(f"  Grid size: {grid.cols}x{grid.rows}")
print(f"\nRequested counts: {test_counts}")
print(f"  Sunflower: {test_counts[CROP_SUNFLOWER]}")
print(f"  Tomato: {test_counts[CROP_TOMATO]}")
print(f"  Wheat: {test_counts[CROP_WHEAT]}")
print(f"  Corn: {test_counts[CROP_CORN]}")
print(f"  Carrot: {test_counts[CROP_CARROT]}")
print(f"  Total: {sum(test_counts.values())} crops")

# Manually trace through _forward_check
solver.refresh_grid_context()
solver._init_domains()
solver.assign = {var: None for var in solver.vars}

print(f"\nInitial _forward_check result:")
result = solver._forward_check(test_counts)
print(f"  Forward check passed: {result}")
print(f"  Failure reason: '{solver.last_failure_reason}'")

start_time = time.time()
result = solver.solve(test_counts)
elapsed = time.time() - start_time

print(f"\nFinal result:")
print(f"  Solve result: {result}")
print(f"  Time elapsed: {elapsed:.4f}s")
print(f"  Backtracks: {len(solver.backtrack_log)}")
print(f"  Timed out: {solver.timed_out}")
print(f"  Failure reason: '{solver.last_failure_reason}'")
