from shared.environment.grid_world import GridWorld
from shared.domain.agent_state import AgentState
from shared.application.world_step_service import WorldStepService
from shared.application.reward_service import RewardService
from shared.application.metrics_service import MetricsService
from shared.application.episode_service import EpisodeService
from shared.ml.dqn_trainer import DQNTrainer
from shared.runners.hunter_agent_runner import HunterAgentRunner
from shared.runners.prey_agent_runner import PreyAgentRunner
from shared.infrastructure.game_logger import GameLogger

class GameService:
    def __init__(self, grid_size, max_steps, hunter_checkpoint, prey_checkpoint):
        self.grid_size = grid_size
        self.max_steps = max_steps
        
        # Initialize Core Components
        self.grid = GridWorld(grid_size, grid_size, seed=42)
        self.world = WorldStepService(self.grid)
        self.metrics = MetricsService()
        self.logger = GameLogger(max_lines=10)
        self.reward_service = RewardService()

        # Initialize Agents
        self.hunter = AgentState("hunter", (0, 0))
        self.prey = AgentState("prey", (grid_size - 1, grid_size - 1))

        # Initialize ML
        self.h_trainer = DQNTrainer(11, 4, checkpoint_path=hunter_checkpoint)
        self.p_trainer = DQNTrainer(10, 4, checkpoint_path=prey_checkpoint)

        # Initialize Runners
        self.h_runner = HunterAgentRunner(self.hunter, self.prey, None, self.world, self.reward_service, self.metrics, self.h_trainer)
        self.p_runner = PreyAgentRunner(self.prey, self.hunter, None, self.world, self.reward_service, self.metrics, self.p_trainer)

        # Initialize Orchestrator
        self.episode_service = EpisodeService(
            self.world, self.hunter, self.prey, self.metrics, 
            self.h_trainer, self.p_trainer, 
            self.h_runner, self.p_runner, max_steps
        )
        
        # Link episodes
        self.h_runner.episode = self.episode_service.episode
        self.p_runner.episode = self.episode_service.episode

    def start_new_episode(self, walls_count, pallets_count):
        self.episode_service.reset_episode(walls_count, pallets_count)

    def update(self, simulation_speed, paused, walls_count, pallets_count):
        return self.episode_service.update_simulation(simulation_speed, paused, walls_count, pallets_count, self.logger)

    def reset_learning(self, walls_count, pallets_count):
        import os
        
        # 1. Delete Checkpoints
        if self.h_trainer.checkpoint_path and os.path.exists(self.h_trainer.checkpoint_path):
            try: os.remove(self.h_trainer.checkpoint_path)
            except: pass
        if self.p_trainer.checkpoint_path and os.path.exists(self.p_trainer.checkpoint_path):
            try: os.remove(self.p_trainer.checkpoint_path)
            except: pass
            
        # 2. Delete Stats
        if self.metrics.save_path and os.path.exists(self.metrics.save_path):
            try: os.remove(self.metrics.save_path)
            except: pass
            
        # 3. Reset In-Memory State
        self.metrics.reset()
        self.h_trainer.reset_training()
        self.p_trainer.reset_training()
        
        # 4. Start Fresh Episode
        self.episode_service.episode.reset()
        self.start_new_episode(walls_count, pallets_count)
        self.logger.log("SYSTEM: Learning Reset Complete!")
