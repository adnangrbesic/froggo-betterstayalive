import matplotlib.pyplot as plt
import json
import os

class MetricsService:
    def __init__(self, save_path=None):
        if save_path is None:
            # Build absolute path to data/stats.json
            # This file is in shared/application/metrics_service.py
            # We need to go up two levels to root, then into data
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
            self.save_path = os.path.join(project_root, "data", "stats.json")
        else:
            self.save_path = save_path
            
        self.reset()
        self.load_stats()

    def reset(self):
        self.hunter_wins = 0
        self.prey_wins = 0
        self.episode_steps = []
        self.total_episodes = 0

    def end_episode(self, steps: int, hunter_won: bool):
        self.total_episodes += 1
        self.episode_steps.append(steps)
        if hunter_won:
            self.hunter_wins += 1
        else:
            self.prey_wins += 1
        self.save_stats()

    def save_stats(self):
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        data = {
            "hunter_wins": self.hunter_wins,
            "prey_wins": self.prey_wins,
            "total_episodes": self.total_episodes,
            "episode_steps": self.episode_steps[-100:] # Čuvamo samo zadnjih 100 radi brzine
        }
        with open(self.save_path, "w") as f:
            json.dump(data, f)

    def load_stats(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r") as f:
                    data = json.load(f)
                    self.hunter_wins = data.get("hunter_wins", 0)
                    self.prey_wins = data.get("prey_wins", 0)
                    self.total_episodes = data.get("total_episodes", 0)
                    self.episode_steps = data.get("episode_steps", [])
            except: pass