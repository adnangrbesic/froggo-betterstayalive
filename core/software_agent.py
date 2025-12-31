# core/software_agent.py

from abc import ABC, abstractmethod
from typing import Optional
from core.tick_result import TickResult


class SoftwareAgent(ABC):
    """
    Base class for all agents.
    Each tick represents exactly ONE Sense–Think–Act–Learn cycle.
    """

    @abstractmethod
    def tick(self) -> Optional[TickResult]:
        """
        Executes a single agent step.
        Returns:
            TickResult if work was done
            None if no work (no-op)
        """
        pass
