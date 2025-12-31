# shared/domain/episode_state.py

from dataclasses import dataclass


@dataclass
class EpisodeState:
    steps: int = 0
    done: bool = False

    def reset(self):
        self.steps = 0
        self.done = False
