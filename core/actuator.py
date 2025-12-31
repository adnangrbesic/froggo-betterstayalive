from collections import deque
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
                self.grid.break_pallet(new_pos)
                return False, True

        if new_pos in self.grid.walls:
            return False, True

        agent.move(new_pos)
        return True, False

    def check_collision(self, hunter: AgentState, prey: AgentState) -> bool:
        return hunter.position == prey.position

    def distance(self, a: AgentState, b: AgentState) -> float:
        """Vazdušna linija (Manhattan)"""
        ar, ac = a.position
        br, bc = b.position
        return abs(ar - br) + abs(ac - bc)

    def real_path_distance(self, start_pos, end_pos) -> int:
        """Računa broj koraka zaobilazeći zidove koristeći BFS"""
        if start_pos == end_pos: return 0
        
        q = deque([(start_pos, 0)])
        visited = {start_pos}
        
        while q:
            (r, c), dist = q.popleft()
            if (r, c) == end_pos:
                return dist
                
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                np = (nr, nc)
                if self.grid.in_bounds(np) and np not in self.grid.walls and np not in visited:
                    visited.add(np)
                    q.append((np, dist + 1))
        return 100 # Ako nema puta (ne bi trebalo da se desi zbog flood-fill-a)