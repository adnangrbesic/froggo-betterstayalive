import os
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque

from shared.ml.dqn_model import DQN


class DQNTrainer:
    def __init__(
            self,
            state_dim,
            action_dim,
            lr=1e-3,
            gamma=0.99,
            epsilon=1.0,
            epsilon_min=0.05,
            epsilon_decay=0.998,
            batch_size=64,
            memory_size=50_000,
            checkpoint_path=None,
            device=None,
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.checkpoint_path = checkpoint_path

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.model = DQN(state_dim, action_dim).to(self.device)
        # Target Network - stabilna kopija za računanje cilja (Pravilo #3)
        self.target_model = DQN(state_dim, action_dim).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())

        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

        self.memory = deque(maxlen=memory_size)
        self.train_steps_counter = 0

        if checkpoint_path and os.path.exists(checkpoint_path):
            self._load_checkpoint()

    def select_action(self, state):
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        with torch.no_grad():
            s = torch.tensor(state, dtype=torch.float32, device=self.device)
            return self.model(s.unsqueeze(0)).argmax().item()

    def store_experience(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.tensor(states, dtype=torch.float32, device=self.device)
        actions = torch.tensor(actions, dtype=torch.long, device=self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        next_states = torch.tensor(next_states, dtype=torch.float32, device=self.device)
        dones = torch.tensor(dones, dtype=torch.float32, device=self.device)

        q_values = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0]

        target = rewards + self.gamma * next_q * (1 - dones)

        loss = self.loss_fn(q_values, target.detach())

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.train_steps_counter += 1

        if self.train_steps_counter % 1000 == 0:
            self.target_model.load_state_dict(self.model.state_dict())

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self):
        if not self.checkpoint_path:
            return

        try:
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            tmp_path = self.checkpoint_path + ".tmp"

            torch.save({
                "model_state": self.model.state_dict(),
                "optimizer_state": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "state_dim": self.state_dim,
                "action_dim": self.action_dim,
            }, tmp_path)

            if os.path.exists(self.checkpoint_path):
                try:
                    os.remove(self.checkpoint_path)
                except OSError:
                    pass

            os.replace(tmp_path, self.checkpoint_path)
        except Exception as e:
            print(f"[DQN] Save failed: {e}")

    def _load_checkpoint(self):
        try:
            data = torch.load(self.checkpoint_path, map_location=self.device)
            if data["state_dim"] == self.state_dim:
                self.model.load_state_dict(data["model_state"])
                self.target_model.load_state_dict(data["model_state"])
                self.optimizer.load_state_dict(data["optimizer_state"])
                self.epsilon = data["epsilon"]
                print(f"[DQN] Loaded checkpoint -> {self.checkpoint_path}")
        except Exception as e:
            print(f"[DQN] Checkpoint load failed, starting fresh: {e}")

    def reset_training(self):
        """Resets the model and epsilon to initial state"""
        self.epsilon = 1.0
        self.model = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_model = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3) # Re-init optimizer
        self.memory.clear()
        print("[DQN] Training RESET.")