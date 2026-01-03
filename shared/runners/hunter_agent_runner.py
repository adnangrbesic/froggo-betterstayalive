import random
from collections import deque
from shared.domain.actions import Action
from core.tick_result import TickResult
from core.software_agent import SoftwareAgent

class HunterAgentRunner(SoftwareAgent):
    def __init__(self, hunter, prey, episode, world, reward_service, metrics, trainer):
        self.hunter = hunter
        self.prey = prey
        self.episode = episode
        self.world = world
        self.reward_service = reward_service
        self.metrics = metrics
        self.trainer = trainer

        self.pos_history = deque(maxlen=12)
        self.prey_pos_history = deque(maxlen=4)
        self.dist_history = deque(maxlen=10)
        self.closer_combo = 0
        self.last_action = None
        
        # PERCEPTION MEMORY
        self.last_known_pos = prey.position 
        self.is_prey_visible = True

    def _get_raycast_dist(self, dr, dc):
        """Vraća normalizovanu udaljenost do prve prepreke u datom smjeru"""
        grid = self.world.grid
        r, c = self.hunter.position
        for dist in range(1, 6):
            p = (r + dr * dist, c + dc * dist)
            if not grid.in_bounds(p) or p in grid.walls or grid.is_pallet_active(p):
                return dist / 5.0
        return 1.0

    def _update_perception(self):
        # 1. Check Line of Sight
        self.is_prey_visible = self.world.grid.has_line_of_sight(self.hunter.position, self.prey.position)
        
        # 2. Update Memory
        if self.is_prey_visible:
            self.last_known_pos = self.prey.position
        elif self.hunter.position == self.last_known_pos:
            # Stigao na mesto gde je mislio da je plen, ali ga nema.
            # SEARCH MODE: Biraj random tacku na mapi da istrazis
            self.last_known_pos = self.world.grid.random_free_pos()

    def _get_state(self):
        self._update_perception()
        
        hr, hc = self.hunter.position
        # TARGET je sada last_known_pos, ne prava pozicija!
        tr, tc = self.last_known_pos
        grid = self.world.grid

        # 1-2: Trenutna relativna pozicija do CILJA (ne nuzno do plena)
        dx, dy = (tr - hr) / grid.height, (tc - hc) / grid.width

        # 3-4: Miris plena (pozicija od pre 3 koraka)
        if len(self.prey_pos_history) == 4:
            old_p = self.prey_pos_history[0]
            odx, ody = (old_p[0] - hr) / grid.height, (old_p[1] - hc) / grid.width
        else:
            odx, ody = dx, dy

        # 5-8: Raycast senzori (vidokrug kroz lavirint)
        rays = [
            self._get_raycast_dist(-1, 0), # Gore
            self._get_raycast_dist(1, 0),  # Dole
            self._get_raycast_dist(0, -1), # Lijevo
            self._get_raycast_dist(0, 1)   # Desno
        ]

        # 9: EFFICIENCY BIT (Pravilo #1)
        # 1.0 ako je efikasan, -1.0 ako "pleše" na istoj razdaljini
        efficiency = 1.0
        if len(self.dist_history) >= 3:
            if self.dist_history[-1] >= self.dist_history[-3]:
                efficiency = -1.0

        # 10: STAGNATION BIT (Oscilacije pozicije)
        stagnation_bit = 0.0
        if len(self.pos_history) >= 4:
            if list(self.pos_history).count(self.hunter.position) >= 2:
                stagnation_bit = 1.0

        # 11: VISIBILITY BIT (Da li zapravo vidim plen?)
        vis_bit = 1.0 if self.is_prey_visible else 0.0

        return [dx, dy, odx, ody] + rays + [efficiency, stagnation_bit, vis_bit]

    def tick(self):
        if self.episode.done: return None

        # =====================================================
        # 1. SENSE (Percepcija)
        # =====================================================
        state = self._get_state()
        self.prey_pos_history.append(self.prey.position)
        
        # =====================================================
        # 2. THINK (Odlučivanje)
        # =====================================================
        action_idx = self.trainer.select_action(state)
        action = list(Action)[action_idx]

        # Provjera naglog okretanja (180 stepeni)
        is_reversing = False
        if self.last_action and action == self.last_action.opposite():
            is_reversing = True

        # Koristimo realnu BFS putanju za preciznu nagradu navigacije
        prev_real_dist = self.world.real_path_distance(self.hunter.position, self.prey.position)
        old_pos = self.hunter.position 

        # =====================================================
        # 3. ACT (Djelovanje)
        # =====================================================
        valid, bumped = self.world.move_agent(self.hunter, action)

        new_pos = self.hunter.position
        new_real_dist = self.world.real_path_distance(new_pos, self.prey.position)
        caught = self.world.check_collision(self.hunter, self.prey)

        # Provjera fizičkog kretanja i tragova
        pos_stagnation = (old_pos == new_pos)
        was_on_trail = list(self.pos_history).count(new_pos) > 0
        
        self.dist_history.append(new_real_dist)

        # Računanje stagnacije realne distance
        stagnation_count = 0
        if len(self.dist_history) >= 2:
            for d in reversed(list(self.dist_history)[:-1]):
                if abs(d - new_real_dist) < 0.1:
                    stagnation_count += 1
                else:
                    break

        if new_real_dist < prev_real_dist:
            self.closer_combo += 1
        else:
            self.closer_combo = 0

        # Detekcija loop-a i čuvanje akcije
        is_looped = list(self.pos_history).count(new_pos) >= 2
        self.pos_history.append(new_pos)
        self.last_action = action

        # =====================================================
        # 4. LEARN (Učenje)
        # =====================================================
        reward = self.reward_service.hunter_reward(
            prev_real_dist, new_real_dist, caught, not pos_stagnation,
            new_pos, self.world.grid.height,
            is_reversing, is_looped, bumped, self.closer_combo,
            stagnation_count, pos_stagnation, was_on_trail
        )

        self.trainer.store_experience(state, action_idx, reward, self._get_state(), self.episode.done or caught)
        self.trainer.train_step()

        if caught:
            self.episode.done = True

        return TickResult("hunter", action, reward, caught, new_real_dist)

    def reset_episode_state(self):
        self.pos_history.clear()
        self.prey_pos_history.clear()
        self.dist_history.clear()
        self.closer_combo = 0
        self.last_action = None
        self.last_known_pos = self.prey.position
        self.is_prey_visible = True