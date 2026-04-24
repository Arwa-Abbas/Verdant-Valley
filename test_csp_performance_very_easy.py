#!/usr/bin/env python
"""
Quick test of CSP solver performance with very easy settings
"""

import sys
import time
from src.world.environment.grid import Grid
from src.algorithms.csp import CSPSolver
from utils.constants import *

def test_csp_performance_very_easy():
    """Test CSP solver with very easy crop counts - one of each"""
    print("Creating test grid...")
    grid = Grid()
    
    print("Initializing CSP solver...")
    solver = CSPSolver(grid)
    solver.set_mode("manual")
    
    # Test with VERY easy crop counts - just 1 of each
    test_counts = {
        CROP_WHEAT: 1,
        CROP_SUNFLOWER: 1,
        CROP_CORN: 1,
        CROP_TOMATO: 1,
        CROP_CARROT: 1,
    }
    
    print(f"Testing with crop counts: {test_counts}")
    print(f"Total crops to place: {sum(test_counts.values())}")
    print(f"Available field tiles: {len(solver.vars)}")
    print(f"Grid size: {grid.cols}x{grid.rows}")
    
    start_time = time.time()
    result = solver.solve(test_counts)
    elapsed = time.time() - start_time
    
    print(f"\n{'='*50}")
    print(f"Solve result: {result}")
    print(f"Time elapsed: {elapsed:.4f}s")
    print(f"Backtracks: {len(solver.backtrack_log)}")
    print(f"{'='*50}")
    
    if solver.timed_out:
        print("WARNING: Solver timed out!")
    
    if solver.last_failure_reason:
        print(f"Failure reason: {solver.last_failure_reason}")
    
    # Verify solution
    if result:
        counts = {
            CROP_WHEAT: 0,
            CROP_SUNFLOWER: 0,
            CROP_CORN: 0,
            CROP_TOMATO: 0,
            CROP_CARROT: 0,
        }
        for crop in solver.assign.values():
            if crop in counts:
                counts[crop] += 1
        
        print(f"\nSolution crop counts:")
        for crop, count in counts.items():
            if crop != CROP_NONE:
                print(f"  {CROP_NAMES.get(crop, crop)}: {count} (requested: {test_counts.get(crop, 0)})")
        
        success = all(counts[crop] == test_counts[crop] for crop in test_counts)
        print(f"\nSolution valid: {success}")
        return success
    else:
        print("Solver failed to find solution")
        return False

if __name__ == "__main__":
    success = test_csp_performance_very_easy()
    sys.exit(0 if success else 1)
