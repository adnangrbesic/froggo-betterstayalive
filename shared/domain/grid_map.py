# shared/domain/grid_map.py

class GridMap:
    def __init__(self, width: int, height: int, walls=None):
        self.width = width
        self.height = height
        self.walls = set(walls) if walls else set()

    @property
    def size(self):
        return self.width, self.height

    def in_bounds(self, pos):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, pos):
        return pos not in self.walls
