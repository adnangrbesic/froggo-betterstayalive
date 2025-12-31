from __future__ import annotations
import random
from typing import Iterable, Set, Tuple
from collections import deque

Pos = Tuple[int, int]


class GridWorld:
    def __init__(self, width: int, height: int, seed: int | None = None, walls: Iterable[Pos] | None = None):
        self.width = int(width)
        self.height = int(height)
        self._rng = random.Random(seed)
        self.walls: Set[Pos] = set(walls or [])
        self._pallets_active: Set[Pos] = set()

    def in_bounds(self, pos: Pos) -> bool:
        r, c = pos
        return 0 <= r < self.height and 0 <= c < self.width

    def is_pallet_active(self, pos: Pos) -> bool:
        return pos in self._pallets_active

    def break_pallet(self, pos: Pos) -> None:
        self._pallets_active.discard(pos)

    def is_free(self, pos: Pos) -> bool:
        return self.in_bounds(pos) and (pos not in self.walls)

    def flood_fill(self, start: Pos) -> Set[Pos]:
        if not self.is_free(start):
            return set()
        visited = {start}
        q = deque([start])
        while q:
            r, c = q.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                p = (r + dr, c + dc)
                if self.is_free(p) and p not in visited:
                    visited.add(p)
                    q.append(p)
        return visited

    def random_free_pos(self, exclude: Set[Pos] | None = None, allow_border: bool = True) -> Pos:
        exclude = exclude or set()
        for _ in range(1000):
            r = self._rng.randint(0, self.height - 1)
            c = self._rng.randint(0, self.width - 1)

            # Ako je allow_border=False, ne dozvoli red/kolonu 0 i zadnji red/kolonu
            if not allow_border:
                if r == 0 or r == self.height - 1 or c == 0 or c == self.width - 1:
                    continue

            p = (r, c)
            if p not in self.walls and p not in exclude:
                return p
        return (1, 1)  # Siguran fallback unutar mape

    def _has_adjacent_pallet(self, pos: Pos) -> bool:
        r, c = pos
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            if (r + dr, c + dc) in self._pallets_active:
                return True
        return False

    def has_line_of_sight(self, start: Pos, end: Pos) -> bool:
        """Proverava da li postoji cista linija vida izmedju dve tacke (Bresenham)"""
        x0, y0 = start
        x1, y1 = end
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                if (x, y) in self.walls: return False
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                if (x, y) in self.walls: return False
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        # Provera krajnje tacke (iako je tu plen, mozda je u zidu greskom?)
        if (x, y) in self.walls: return False
        return True

    def generate_random_layout(self, wall_count: int, pallet_count: int, reserved: Set[Pos] | None = None):
        reserved = reserved or set()
        self.walls.clear()
        self._pallets_active.clear()

        # 1. GENERISANJE ZIDOVA (Zabranjeno na ivicama)
        attempts = 0
        while len(self.walls) < wall_count and attempts < 3000:
            attempts += 1
            # Zidovi se generišu samo od indeksa 1 do size-2
            r = self._rng.randint(1, self.height - 2)
            c = self._rng.randint(1, self.width - 2)
            p = (r, c)

            if p in reserved or p in self.walls: continue

            self.walls.add(p)
            start_p = self.random_free_pos(exclude=self.walls, allow_border=True)
            reachable = self.flood_fill(start_p)

            # Sva polja (uključujući ivice) moraju biti povezana
            if len(reachable) < (self.width * self.height) - len(self.walls):
                self.walls.remove(p)

        # 2. GENERISANJE PALETA (Strogo unutrašnjost, bez dodirivanja)
        all_possible_chokes = []
        for r in range(1, self.height - 1):
            for c in range(1, self.width - 1):
                p = (r, c)
                if p in self.walls or p in reserved: continue

                h_choke = (r, c - 1) in self.walls and (r, c + 1) in self.walls
                v_choke = (r - 1, c) in self.walls and (r + 1, c) in self.walls
                if h_choke or v_choke:
                    all_possible_chokes.append(p)

        self._rng.shuffle(all_possible_chokes)
        for p in all_possible_chokes:
            if len(self._pallets_active) >= pallet_count: break
            if not self._has_adjacent_pallet(p):
                self._pallets_active.add(p)

        # Fallback za preostale palete (isključivo unutrašnjost)
        attempts = 0
        while len(self._pallets_active) < pallet_count and attempts < 1000:
            attempts += 1
            p = self.random_free_pos(exclude=self.walls | self._pallets_active | reserved, allow_border=False)
            if not self._has_adjacent_pallet(p):
                self._pallets_active.add(p)