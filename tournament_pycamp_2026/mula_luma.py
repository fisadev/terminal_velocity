import random
from tv.game import (
    Position,
    POWER_TO,
    FLY_TO,
    ENGINES,
    SHIELDS,
    LASERS,
    ASTEROID,
    SPACESHIP,
    RADAR_RADIUS,
    ATTACK_RADIUS,
    PIRATING_REWARD,
)

MOVE_CONFIG = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
ATTACK_CONFIG = {ENGINES: 0, SHIELDS: 0, LASERS: 3}


class BotLogic:
    """
    Mula Luma: Optimized for speed and tactical aggression.
    Inspired by Marce's exploration and Tom Yorke's persistence.
    """

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.player_name = player_name
        self.map_radius = map_radius
        self.players = players
        self.total_turns = turns
        self.home_base_positions = list(home_base_positions)
        self.icon = "🐴👵"

        # Memory
        self.map_memory = {}  # Position -> (type, last_seen_turn)
        # Initialize map with "Unknown"
        for x in range(-map_radius, map_radius + 1):
            for y in range(-map_radius, map_radius + 1):
                self.map_memory[Position(x, y)] = ("unknown", -1)

    def turn(
        self,
        turn_number,
        hp,
        ship_number,
        cargo,
        position,
        power_distribution,
        radar_contacts,
        leader_board,
    ):
        # 1. Update Memory
        self.update_memory(turn_number, position, radar_contacts)

        # 2. Context Analysis
        enemies_in_radar = [
            pos for pos, type in radar_contacts.items() if type == SPACESHIP
        ]
        closest_enemy = (
            min(enemies_in_radar, key=lambda e: position.distance_to(e))
            if enemies_in_radar
            else None
        )
        enemy_dist = (
            position.distance_to(closest_enemy) if closest_enemy else float("inf")
        )

        # Find enemy names from leader_board and find their positions in radar
        potential_loot = 0
        if closest_enemy:
            # We don't know the name of the enemy at that position, but we can see the leader_board
            # If anyone has lots of credits, it's worth attacking
            max_enemy_credits = max(
                [c for n, c in leader_board.items() if n != self.player_name] + [0]
            )
            potential_loot = max_enemy_credits * PIRATING_REWARD

        # 3. Decision Tree

        # Priority 1: Combat (If we can steal a lot of money and they are close)
        if closest_enemy and enemy_dist <= ATTACK_RADIUS and potential_loot > 50:
            if power_distribution != ATTACK_CONFIG:
                return POWER_TO, ATTACK_CONFIG
            return None  # Stay and shoot automatically

        # Priority 2: Return Cargo (Speed is king)
        if cargo > 0:
            if power_distribution != MOVE_CONFIG:
                return POWER_TO, MOVE_CONFIG
            target_home = min(
                self.home_base_positions, key=lambda p: p.distance_to(position)
            )
            return self.navigate(position, target_home, power_distribution, cargo)

        # Priority 3: Harvest
        target_asteroid = self.find_closest(ASTEROID, position)
        if target_asteroid:
            if power_distribution != MOVE_CONFIG:
                return POWER_TO, MOVE_CONFIG
            return self.navigate(position, target_asteroid, power_distribution, cargo)

        # Priority 4: Exploration (Go to the least recently seen place)
        target_explore = self.find_least_seen(position)
        if target_explore:
            if power_distribution != MOVE_CONFIG:
                return POWER_TO, MOVE_CONFIG
            return self.navigate(position, target_explore, power_distribution, cargo)

        return None

    def update_memory(self, turn_number, position, radar_contacts):
        # Update everything in radar range
        for p in position.positions_in_range(RADAR_RADIUS):
            # Mark as empty first
            self.map_memory[p] = ("empty", turn_number)

        # Add actual contacts
        for pos, type in radar_contacts.items():
            self.map_memory[pos] = (type, turn_number)

    def find_closest(self, target_type, position):
        candidates = [
            pos for pos, (t, turn) in self.map_memory.items() if t == target_type
        ]
        if not candidates:
            return None
        # Sort by distance and recency
        return min(candidates, key=lambda p: p.distance_to(position))

    def find_least_seen(self, position):
        items = list(self.map_memory.items())
        # Filter out home base positions
        items = [i for i in items if i[0] not in self.home_base_positions]

        # Score = TurnSeen + (Distance / MapRadius * 10)
        # We want LOW score (oldest and closest)
        def score_explore(item):
            pos, (type, turn) = item
            dist = pos.distance_to(position)
            return turn + (dist / self.map_radius)

        best_pos, _ = min(items, key=score_explore)
        return best_pos

    def navigate(self, src, dst, power_dist, cargo):
        speed = max(0, power_dist[ENGINES] - cargo)
        if speed == 0:
            return FLY_TO, src

        possible_moves = list(src.positions_in_range(speed))
        possible_moves = [
            p
            for p in possible_moves
            if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius
        ]

        if not possible_moves:
            return FLY_TO, src

        # Go to destination, add a tiny bit of random to avoid deadlocks
        return FLY_TO, min(
            possible_moves, key=lambda p: p.distance_to(dst) + random.uniform(0, 0.1)
        )
