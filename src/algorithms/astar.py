import heapq
from utils.helpers import manhattan, neighbors_4
from utils.constants import TILE_COST


class AStarResult:
    def __init__(self, path, explored, cost):
        self.path = path  # list of (col, row) from start→goal
        self.explored = explored  # set of (col, row) nodes expanded
        self.cost = cost


def astar(grid, start, goal):
    """
    A* on the weighted grid.
    Returns AStarResult(path, explored, total_cost).
    path is [] if unreachable.
    """
    if start == goal:
        return AStarResult([start], set(), 0)

    open_heap = []  # (f, g, node)
    heapq.heappush(open_heap, (0, 0, start))

    came_from = {start: None}
    g_cost = {start: 0}
    explored = set()

    while open_heap:
        f, g, current = heapq.heappop(open_heap)

        if current in explored:
            continue
        explored.add(current)

        if current == goal:
            path = _reconstruct(came_from, goal)
            return AStarResult(path, explored, g)

        col, row = current
        for nc, nr in neighbors_4(col, row, grid.cols, grid.rows):
            tile = grid.get(nc, nr)
            if not tile or not tile.walkable:
                continue

            new_g = g + tile.cost
            if new_g < g_cost.get((nc, nr), float("inf")):
                g_cost[(nc, nr)] = new_g
                h = manhattan((nc, nr), goal)
                heapq.heappush(open_heap, (new_g + h, new_g, (nc, nr)))
                came_from[(nc, nr)] = current

    # Unreachable
    return AStarResult([], explored, float("inf"))


def _reconstruct(came_from, node):
    path = []
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path
