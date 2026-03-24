import random
from tv.game import (
    Position, POWER_TO, FLY_TO, ENGINES, SHIELDS, LASERS,
    ASTEROID, SPACESHIP,
    MAX_CARGO, RADAR_RADIUS, ATTACK_RADIUS, PIRATING_REWARD,
)

EMPTY = "empty"
MOVE_CONFIG = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
SHOOT_CONFIG = {ENGINES: 0, SHIELDS: 0, LASERS: 3}


class BotLogic:
    """
    FRESHNESS KING: penalización agresiva a asteroides stale (x1.0 por turno).
    Casi siempre va a asteroides vistos recientemente → casi nunca viaja en vano.
    Cargo-2. Freshness ship avoidance. Combat selectivo.
    """

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.name = player_name
        self.map_radius = map_radius
        self.total_turns = turns
        self.home_base_positions = home_base_positions
        self.home = Position(0, 0)
        self.icon = "~~"
        self.map = {
            Position(i, j): (EMPTY, 0)
            for i in range(-map_radius, map_radius + 1)
            for j in range(-map_radius, map_radius + 1)
        }

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution,
             radar_contacts, leader_board):
        for p in position.positions_in_range(RADAR_RADIUS):
            if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius:
                self.map[p] = (EMPTY, turn_number)
        for cp, ct in radar_contacts.items():
            self.map[cp] = (ct, turn_number)

        speed = power_distribution[ENGINES] - cargo
        nearby_enemies = [p for p, t in radar_contacts.items() if t == SPACESHIP]
        enemies_in_range = [p for p in nearby_enemies if position.distance_to(p) <= ATTACK_RADIUS]

        # Combat
        if enemies_in_range and position not in self.home_base_positions:
            my_credits = leader_board.get(self.name, 0)
            max_enemy = max((c for n, c in leader_board.items() if n != self.name), default=0)
            progress = turn_number / max(self.total_turns, 1)
            winning_big = my_credits > max_enemy * 1.3 and progress > 0.7
            if max_enemy * PIRATING_REWARD > 30 and max_enemy >= my_credits * 0.5 and not winning_big:
                close_ast = [p for p, t in radar_contacts.items()
                             if t == ASTEROID and position.distance_to(p) <= ATTACK_RADIUS]
                if not (close_ast and cargo < MAX_CARGO):
                    if power_distribution != SHOOT_CONFIG:
                        return POWER_TO, SHOOT_CONFIG
                    return None

        if power_distribution != MOVE_CONFIG:
            return POWER_TO, MOVE_CONFIG
        if speed <= 0:
            return None

        danger_zone = set()
        for enemy in nearby_enemies:
            for p in enemy.positions_in_range(ATTACK_RADIUS):
                danger_zone.add(p)

        # Cargo-2 con evaluación de $/turno
        if cargo == 1:
            my_dist = position.distance_to(self.home)
            best_second, best_ev = None, 100.0 / max(my_dist / 2.0, 0.1)  # EV de ir directo
            for p, t in radar_contacts.items():
                if t != ASTEROID:
                    continue
                detour = position.distance_to(p) / 2.0 + p.distance_to(self.home) / 1.0
                ev = 200.0 / max(detour, 0.1)
                if ev > best_ev:
                    best_ev = ev
                    best_second = p
            if best_second:
                return self._fly_to(position, best_second, speed, turn_number, danger_zone=danger_zone)
            return self._fly_home(position, speed, turn_number, danger_zone)

        if cargo >= MAX_CARGO:
            return self._fly_home(position, speed, turn_number, danger_zone)

        # FRESHNESS KING: penalty agresiva x1.0 por turno
        best_ast = self._best_asteroid(position, turn_number)
        if best_ast:
            return self._fly_to(position, best_ast, speed, turn_number, danger_zone=danger_zone)

        target = self._closest_least_seen(position)
        if target:
            return self._fly_to(position, target, speed, turn_number, danger_zone=danger_zone)
        return None

    def _best_asteroid(self, position, turn_number):
        best, best_cost = None, float("inf")
        for pos, (kind, seen) in self.map.items():
            if kind != ASTEROID:
                continue
            base_cost = position.distance_to(pos) / 3.0 + pos.distance_to(self.home) / 2.0
            # AGRESIVO: cada turno sin ver el asteroide suma 1.0 al costo
            staleness = (turn_number - seen) * 1.0
            cost = base_cost + staleness
            if cost < best_cost:
                best_cost = cost
                best = pos
        return best

    def _closest_least_seen(self, position):
        candidates = [(p, s) for p, (k, s) in self.map.items()
                       if k == EMPTY and p not in self.home_base_positions]
        if not candidates:
            return None
        random.shuffle(candidates)
        return min(candidates, key=lambda v: (v[1], v[0].distance_to(position)))[0]

    def _fly_home(self, position, speed, turn_number, danger_zone):
        safe = [p for p in self.home_base_positions
                if self.map.get(p, (EMPTY, 0))[0] != SPACESHIP]
        if not safe:
            safe = list(self.home_base_positions)
        target = min(safe, key=lambda p: position.distance_to(p))
        return self._fly_to(position, target, speed, turn_number,
                            avoid_asteroids=True, danger_zone=danger_zone)

    def _fly_to(self, position, target, speed, turn_number,
                avoid_asteroids=False, danger_zone=frozenset()):
        if speed <= 0:
            return None

        # Solo evitar naves frescas (≤3 turnos)
        forbidden = set()
        for pos, (kind, seen) in self.map.items():
            if kind == SPACESHIP and (turn_number - seen) <= 3:
                forbidden.add(pos)
            if avoid_asteroids and kind == ASTEROID:
                forbidden.add(pos)

        reachable = list(position.positions_in_range(speed))
        valid = [p for p in reachable
                 if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius
                 and p not in forbidden]
        if not valid:
            valid = [p for p in reachable
                     if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius]
        if not valid:
            return None

        def score(p):
            d = p.distance_to(target)
            if p in danger_zone and p not in self.home_base_positions:
                d += 2
            return d
        return FLY_TO, min(valid, key=score)
