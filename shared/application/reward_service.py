class RewardService:
    INVALID_MOVE_PENALTY = -0.5

    # HUNTER - Drastičan pritisak (Nerfed)
    H_STEP_PENALTY = -0.5  # Lovac gubi poene jako brzo (mora biti munjevit!)
    H_CLOSER_BONUS = +0.3  # Smanjeno: samo blaga motivacija za približavanje
    H_FARTHER_PENALTY = -0.1  # Skoro zanemarljivo: dopušta mu da luta i obilazi
    H_CAUGHT_REWARD = +20.0  # Smanjeno: ulov nije vredniji od 40 koraka života žabe
    H_STAGNATION_PENALTY = -5.0

    # PREY - NERFED (Balanced)
    P_CAUGHT_PENALTY = -50.0  # Smanjeno sa -500 (da ne bude prevelik sok)
    P_SURVIVE_BONUS = +0.1    # Smanjeno sa +5.0 (samo mali poticaj za zivot)
    P_FARTHER_BONUS = +1.0    # Smanjeno sa +15.0 (bjezi, ali ne dobijaj jackpot)
    P_CLOSER_PENALTY = -1.5   # Povecana kazna za priblizavanje (bjezi jace!)
    P_STAGNATION_PENALTY = -0.5

    # GLOBAL
    REVERSING_PENALTY = -2.0
    BORDER_PENALTY = -0.5

    def _is_at_border(self, pos, grid_size):
        r, c = pos
        return r == 0 or r == grid_size - 1 or c == 0 or c == grid_size - 1

    def hunter_reward(self, prev_distance, new_distance, caught, valid_move, pos, grid_size,
                      is_reversing=False, looped=False, bumped_wall=False, combo_count=0,
                      dist_stagnation_count=0, pos_stagnation=False, was_on_trail=False) -> float:
        if caught: return self.H_CAUGHT_REWARD
        if not valid_move or bumped_wall or pos_stagnation or is_reversing or looped or was_on_trail:
            return self.H_STAGNATION_PENALTY

        r = self.H_STEP_PENALTY
        if new_distance < prev_distance:
            # Hunter dobija progresivno više samo ako je BAŠ blizu (finalni sprint)
            proximity = 2.0 if prev_distance < 4 else 1.0
            r += (self.H_CLOSER_BONUS * proximity + min(2.0, combo_count * 0.2))
        else:
            r += self.H_FARTHER_PENALTY
        return r

    def prey_reward(self, prev_distance, new_distance, caught, valid_move, pos, grid_size,
                    is_reversing=False, is_hidden=False) -> float:
        if caught: return self.P_CAUGHT_PENALTY
        if not valid_move: return self.INVALID_MOVE_PENALTY

        # Žaba sme da se okrene ako joj to spašava život (manja kazna)
        if is_reversing and prev_distance < 3: return -1.0

        r = self.P_SURVIVE_BONUS
        if is_hidden and prev_distance < 5: r += 1.0  # Ninja mode (smanjeno sa 5.0)

        if new_distance > prev_distance:
            r += self.P_FARTHER_BONUS
        elif new_distance < prev_distance:
            r += self.P_CLOSER_PENALTY
        else:
            r += self.P_STAGNATION_PENALTY
        return r