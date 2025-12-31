import random
from shared.domain.actions import Action
from shared.domain.prey_state import PreyState

class PreyPolicy:
    def decide_state(self, distance: float) -> PreyState:
        if distance <= 2:
            return PreyState.PANIC
        elif distance <= 5:
            return PreyState.ALERT
        return PreyState.IDLE

    def decide_action(
        self,
        state: PreyState,
        prey_pos,
        hunter_pos
    ) -> Action:

        # malo haosa – da nije deterministički
        if random.random() < 0.1:
            return random.choice(list(Action))

        px, py = prey_pos
        hx, hy = hunter_pos

        if state == PreyState.IDLE:
            return random.choice(list(Action))

        # bježi od huntera
        dx = px - hx
        dy = py - hy

        if abs(dx) > abs(dy):
            return Action.DOWN if dx > 0 else Action.UP
        else:
            return Action.RIGHT if dy > 0 else Action.LEFT
