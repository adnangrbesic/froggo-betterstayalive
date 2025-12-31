from collections import deque
import heapq
from shared.domain.actions import Action
from shared.domain.agent_state import AgentState
from shared.environment.grid_world import GridWorld


class WorldStepService:
    def __init__(self, grid: GridWorld):
        self.grid = grid

    def _agent_type(self, agent: AgentState) -> str:
        for attr in ("agent_type", "name", "type"):
            if hasattr(agent, attr):
                v = getattr(agent, attr)
                if isinstance(v, str):
                    return v.lower()
        return "unknown"

    def move_agent(self, agent: AgentState, action: Action) -> tuple[bool, bool]:
        r, c = agent.position

        if action == Action.UP:
            new_pos = (r - 1, c)
        elif action == Action.DOWN:
            new_pos = (r + 1, c)
        elif action == Action.LEFT:
            new_pos = (r, c - 1)
        elif action == Action.RIGHT:
            new_pos = (r, c + 1)
        else:
            return False, False

        if not self.grid.in_bounds(new_pos):
            return False, True

        agent_type = self._agent_type(agent)

        if self.grid.is_pallet_active(new_pos):
            if agent_type == "prey":
                agent.move(new_pos)
                return True, True
            else:
                # HUNTER NERF: Razbija paletu ali OSTAJE na mestu (troši potez)
                self.grid.break_pallet(new_pos)
                return False, True # valid=False jer se nije pomerio, bumped=True

        if new_pos in self.grid.walls:
            return False, True

        agent.move(new_pos)
        return True, False

    def check_collision(self, hunter: AgentState, prey: AgentState) -> bool:
        return hunter.position == prey.position

    def distance(self, a: AgentState, b: AgentState) -> float:
        ar, ac = a.position
        br, bc = b.position
        return abs(ar - br) + abs(ac - bc)

    def real_path_distance(self, start_pos, end_pos) -> int:
        if start_pos == end_pos: return 0
        q = [(0, start_pos)]
        distances = {start_pos: 0}

        while q:
            current_dist, (r, c) = heapq.heappop(q)
            if (r, c) == end_pos: return current_dist
            if current_dist > distances.get((r, c), float('inf')): continue

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                np = (nr, nc)
                if self.grid.in_bounds(np) and np not in self.grid.walls:
                    # Paleta košta 2 (1 za lomljenje, 1 za ulazak), prazno polje 1
                    weight = 2 if self.grid.is_pallet_active(np) else 1
                    new_dist = current_dist + weight
                    if new_dist < distances.get(np, float('inf')):
                        distances[np] = new_dist
                        heapq.heappush(q, (new_dist, np))
        return 100