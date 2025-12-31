from collections import deque
from shared.domain.actions import Action
from core.tick_result import TickResult
from core.software_agent import SoftwareAgent


class PreyAgentRunner(SoftwareAgent):
    def __init__(self, prey, hunter, episode, world, reward_service, metrics, trainer):
        self.prey = prey
        self.hunter = hunter
        self.episode = episode
        self.world = world
        self.reward_service = reward_service
        self.metrics = metrics
        self.trainer = trainer
        self.hunter_pos_history = deque(maxlen=4)
        self.jump_cooldown = 0
        self.last_action = None

    def _get_raycast_dist(self, dr, dc):
        grid = self.world.grid
        r, c = self.prey.position
        for dist in range(1, 6):
            p = (r + dr * dist, c + dc * dist)
            if not grid.in_bounds(p) or p in grid.walls:
                return dist / 5.0
        return 1.0

    def _is_hidden(self):
        hr, hc = self.hunter.position
        pr, pc = self.prey.position
        dr = 1 if hr > pr else -1 if hr < pr else 0
        dc = 1 if hc > pc else -1 if hc < pc else 0
        return (pr + dr, pc + dc) in self.world.grid.walls

    def _get_state(self):
        pr, pc = self.prey.position
        hr, hc = self.hunter.position
        grid = self.world.grid
        dx, dy = (hr - pr) / grid.height, (hc - pc) / grid.width

        # Intuicija
        if len(self.hunter_pos_history) == 4:
            old_h = self.hunter_pos_history[0]
            odx, ody = (old_h[0] - pr) / grid.height, (old_h[1] - pc) / grid.width
        else:
            odx, ody = dx, dy

        rays = [self._get_raycast_dist(-1, 0), self._get_raycast_dist(1, 0),
                self._get_raycast_dist(0, -1), self._get_raycast_dist(0, 1)]

        hidden = 1.0 if self._is_hidden() else 0.0

        # PANIC BIT: 1.0 ako je lovac jako blizu
        panic = 1.0 if self.world.distance(self.hunter, self.prey) < 3 else 0.0

        return [dx, dy, odx, ody] + rays + [hidden, panic]

    def tick(self):
        if self.episode.done: return None
        state = self._get_state()
        self.hunter_pos_history.append(self.hunter.position)
        is_hidden = self._is_hidden()
        action_idx = self.trainer.select_action(state)
        action = list(Action)[action_idx]

        is_reversing = False
        if self.last_action and action == self.last_action.opposite():
            is_reversing = True

        prev_dist = self.world.distance(self.hunter, self.prey)
        valid, bumped = self.world.move_agent(self.prey, action)

        if self.jump_cooldown == 0 and valid:
            self.world.move_agent(self.prey, action)
            self.jump_cooldown = 2
        elif self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        new_dist = self.world.distance(self.hunter, self.prey)
        caught = self.world.check_collision(self.hunter, self.prey)
        self.last_action = action

        reward = self.reward_service.prey_reward(
            prev_dist, new_dist, caught, valid,
            self.prey.position, self.world.grid.height,
            is_reversing, is_hidden
        )
        self.trainer.store_experience(state, action_idx, reward, self._get_state(), self.episode.done)
        self.trainer.train_step()
        return TickResult("prey", action, reward, caught, new_dist)

    def reset_episode_state(self):
        self.hunter_pos_history.clear()
        self.jump_cooldown = 0
        self.last_action = None