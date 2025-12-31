from shared.environment.grid_world import GridWorld
from shared.domain.agent_state import AgentState
from shared.application.world_step_service import WorldStepService
from shared.application.reward_service import RewardService
from shared.application.metrics_service import MetricsService
from shared.application.episode_service import EpisodeService
from shared.ml.dqn_trainer import DQNTrainer
from shared.runners.hunter_agent_runner import HunterAgentRunner
from shared.runners.prey_agent_runner import PreyAgentRunner
from data.logs import GameLogger

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
