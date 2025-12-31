import pygame
import random
from shared.domain.agent_state import AgentState
from shared.domain.episode_state import EpisodeState


class EpisodeService:
    def __init__(self, world, hunter, prey, metrics, hunter_trainer, prey_trainer,
                 hunter_runner, prey_runner, max_steps=400):
        self.world = world
        self.hunter = hunter
        self.prey = prey
        self.metrics = metrics
        self.hunter_trainer = hunter_trainer
        self.prey_trainer = prey_trainer
        self.hunter_runner = hunter_runner
        self.prey_runner = prey_runner

        self.episode = EpisodeState()
        self.max_steps = max_steps
        self.min_spawn_dist = 6
        self.last_logic_tick = 0

    def reset_episode(self, wall_count, pallet_count):
        self.world.grid.generate_random_layout(
            wall_count=wall_count,
            pallet_count=pallet_count,
            reserved=set(),
        )
        h_pos = self._safe_spawn()
        p_pos = self._safe_spawn(exclude={h_pos})
        for _ in range(50):
            if abs(h_pos[0] - p_pos[0]) + abs(h_pos[1] - p_pos[1]) >= self.min_spawn_dist:
                break
            p_pos = self._safe_spawn(exclude={h_pos})
        self.hunter.position = h_pos
        self.prey.position = p_pos
        self.episode.reset()
        if hasattr(self.hunter_runner, "reset_episode_state"):
            self.hunter_runner.reset_episode_state()
        if hasattr(self.prey_runner, "reset_episode_state"):
            self.prey_runner.reset_episode_state()

    def update_simulation(self, speed, paused, walls, pallets, logger):
        """Centralna logika petlje simulacije"""
        if paused:
            return None, None

        now = pygame.time.get_ticks()
        logic_interval = 200 / speed
        h_res, p_res = None, None

        if now - self.last_logic_tick > logic_interval:
            steps_to_run = 1 if speed <= 10 else (speed // 10)
            for _ in range(steps_to_run):
                p_res = self.prey_runner.tick()
                h_res = self.hunter_runner.tick()
                self.episode.steps += 1

                was_caught = h_res.caught if h_res else False

                if self._check_and_handle_end(walls, pallets, was_caught, logger):
                    break
            self.last_logic_tick = now
        return h_res, p_res

    def _check_and_handle_end(self, wall_count, pallet_count, was_caught, logger):
        if self.episode.steps >= self.max_steps:
            self.episode.done = True

        if self.episode.done:
            self.metrics.end_episode(self.episode.steps, was_caught)

            winner = "GHOST won!" if was_caught else "FROGGO won!"
            logger.log(winner)

            if self.metrics.total_episodes % 50 == 0:
                self.hunter_trainer.save()
                self.prey_trainer.save()

            self.hunter_trainer.decay_epsilon()
            self.prey_trainer.decay_epsilon()
            self.reset_episode(wall_count, pallet_count)
            return True
        return False

    def _safe_spawn(self, exclude=set()):
        grid = self.world.grid
        for _ in range(200):
            p = grid.random_free_pos(exclude=exclude, allow_border=False)
            if p is None: continue
            r, c = p
            walls_around = sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] if (r + dr, c + dc) in grid.walls)
            if walls_around <= 1: return p
        return grid.random_free_pos(exclude=exclude, allow_border=False)