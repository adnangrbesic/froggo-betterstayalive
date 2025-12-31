# shared/domain/agent_state.py

from dataclasses import dataclass
from typing import Tuple


@dataclass
class AgentState:
    name: str
    position: Tuple[int, int]

    def move(self, new_position: Tuple[int, int]):
        self.position = new_position
