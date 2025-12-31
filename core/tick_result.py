# core/tick_result.py

from dataclasses import dataclass
from typing import Any


@dataclass
class TickResult:
    agent_type: str        # "hunter" | "prey"
    action: Any            # Action enum
    reward: float
    caught: bool
    distance: float
