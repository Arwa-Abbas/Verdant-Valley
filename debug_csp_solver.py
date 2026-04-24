#!/usr/bin/env python
"""
Debug CSP solver to understand failure points
"""

import sys
from src.world.environment.grid import Grid
from src.algorithms.csp import CSPSolver
from utils.constants import *

def debug_csp():
    """Debug CSP solver with minimal crops"""
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
    
    print(f"Grid: {grid.cols}x{grid.rows}")
    print(f"Field tiles available: {len(solver.vars)}")
    print(f"Request: {test_counts}")
    
    # Manually step through what solve() does
    solver.solve_start_time = None
    solver.timed_out = False
    solver.refresh_grid_context()
    solver.backtrack_log = []
    solver._init_domains()
    solver.last_failure_reason = ""
    
    solver.set_requested_counts(test_counts)
    
    # Initialize assignments
    solver.assign = {}
    for var in solver.vars:
        solver.assign[var] = None
    
    solver.log = []
    
    # This is the key part
    requested = dict(solver.get_requested_counts())
    print(f"\nRequested (after processing): {requested}")
    
    # Step into _solve_manual_with_backtracking
    print("\n=== _solve_manual_with_backtracking ===")
    
    constrained_slots = solver._build_constrained_crop_slots(requested)
    print(f"Constrained slots: {constrained_slots}")
    
    constrained_counts = {
        crop: requested.get(crop, 0)
        for crop in (CROP_SUNFLOWER, CROP_TOMATO, CROP_WHEAT)
    }
    print(f"Constrained counts: {constrained_counts}")
    
    # First forward check
    solver._refresh_domains_for_search(requested)
    print(f"\nForward check on requested counts...")
    fc_result = solver._forward_check(requested)
    print(f"Forward check result: {fc_result}")
    if solver.last_failure_reason:
        print(f"Failure reason: {solver.last_failure_reason}")
    
    if constrained_slots:
        print(f"\nWould backtrack search here, but constrained_slots is empty")
    
    # Remaining counts
    remaining_counts = dict(requested)
    for crop in (CROP_SUNFLOWER, CROP_TOMATO, CROP_WHEAT):
        remaining_counts[crop] = 0
    print(f"\nRemaining counts after removing constrained: {remaining_counts}")
    
    # Try to fill remaining
    print(f"\n=== _fill_remaining_easy_crops ===")
    solver._refresh_domains_for_search(remaining_counts)
    
    fill_result = solver._fill_remaining_easy_crops(remaining_counts)
    print(f"Fill result: {fill_result}")
    if solver.last_failure_reason:
        print(f"Failure reason: {solver.last_failure_reason}")
    
    # Check final constraints
    print(f"\n=== _final_constraints_satisfied ===")
    solver._refresh_domains_for_search({crop: 0 for crop in requested})
    final_result = solver._final_constraints_satisfied()
    print(f"Final constraints satisfied: {final_result}")
    
    # Count what was assigned
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
    
    print(f"\nAssigned counts: {counts}")
    print(f"Expected counts: {requested}")

if __name__ == "__main__":
    debug_csp()
