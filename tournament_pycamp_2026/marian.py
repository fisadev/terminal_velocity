import random
from math import sqrt

from tv.game import MAX_CARGO, logging
from tv.game import (
    SHIELDS,
    LASERS,
    ENGINES,
    FLY_TO,
    POWER_TO,
    ASTEROID,
    SPACESHIP,
    HOME_BASE,
    RADAR_RADIUS,
    ATTACK_RADIUS,
    ASTEROIDS_DENSITY,
    Position,
)

OPEN_SPACE = "-"


class Turn:
    def __init__(
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
        self.turn_number = turn_number
        self.hp = hp
        self.cargo = cargo
        self.ship_number = ship_number
        self.position = position
        self.power_distribution = power_distribution
        self.radar_contacts = radar_contacts
        self.leader_board = leader_board
        self.speed = max(self.power_distribution[ENGINES] - self.cargo, 0)

    def __repr__(self):
        return f"{self.turn_number}) {self.position} hp:{self.hp} speed:{self.speed} cargo:{self.cargo} #:{self.ship_number}"


class Map:
    def __init__(self, map_radius, home_base_positions):
        self.map_radius = map_radius
        self.home_base_positions = home_base_positions
        self.map = {}
        self._nearest_objects = {}
        for pos in self.home_base_positions:
            self.map[pos] = (HOME_BASE, 0)

    def update(self, turn):
        for x, y in turn.position.positions_in_range(RADAR_RADIUS):
            if abs(x) > self.map_radius or abs(y) > self.map_radius:
                continue
            position = Position(x, y)

            self.map[position] = (
                turn.radar_contacts.get(position, OPEN_SPACE),
                turn.turn_number,
            )

    def remove(self, position):
        return self.map.pop(position, None)

    def get_nearest_objects(self, position):
        """
        creates list of discovered nearest objects
        """
        objets = {}
        for pos, value in self.map.items():
            obj_list = objets.get(value[0], [])
            dist = position.distance_to(pos)
            if dist > 0:
                obj_list.append((dist, pos, value[1]))
                objets[value[0]] = obj_list
        for typ, obj_list in objets.items():
            objets[typ] = sorted(obj_list, key=lambda x: x[0])
        self._nearest_objects = objets
        return objets

    def return_nearest_type(self, typ):
        targets = self._nearest_objects.get(typ, None)
        if targets:
            return targets[0][1]
        return None

    @property
    def nearest_asteroid(self):
        return self.return_nearest_type(ASTEROID)

    @property
    def nearest_home_base(self):
        return self.return_nearest_type(HOME_BASE)

    def compute_asteroids_density(self, turn, jumps):
        for x, y in turn.position.positions_in_range(turn.speed * jumps):
            if abs(x) > self.map_radius or abs(y) > self.map_radius:
                continue

            position = Position(x, y)
            counters = {}

            if value := self.map.get(position, None):
                if value not in counters:
                    counters[value] = 0
                counters[value] += 1
            if counters:
                return counters.get(ASTEROID, 0) / sum(counters.values())
            return 0

    def compute_asteroids_density_by_quadrant(self):
        q = int(self.map_radius / 2)
        quadrants = {}
        for y1 in range(-self.map_radius, self.map_radius + 1, q):
            for x1 in range(-self.map_radius, self.map_radius + 1, q):
                counters = {}
                unknown = 0
                for y in range(y1, y1 + q):
                    for x in range(x1, x1 + q):
                        position = Position(x, y)

                        if value := self.map.get(position, None):
                            if value not in counters:
                                counters[value] = 0
                            counters[value] += 1
                        else:
                            unknown += 1

                density = ASTEROIDS_DENSITY
                if counters:
                    if (unknown / (unknown + sum(counters.values()))) < 0.5:
                        density = counters.get(ASTEROID, 0) / sum(counters.values())
                quadrants[(x1, y1)] = density
                logging.info(f"density in quadrant {x1} {y1} {density}")

        self.quadrants = quadrants

    def distance_to_quadrants(self, position):
        q = int(self.map_radius / 2)
        distances = {}
        for y1 in range(-self.map_radius, self.map_radius + 1, q):
            for x1 in range(-self.map_radius, self.map_radius + 1, q):
                target = None
                for y in range(y1, y1 + q):
                    for x in range(x1, x1 + q):
                        distance = position.distance_to(Position(x, y))
                        if not target:
                            target = (Position(x, y), distance)
                        elif distance < target[1]:
                            target = (Position(x, y), distance)
                distances[(x1, y1)] = target
                logging.info(f"nearest in quadrant {x1} {y1} {target}")
        q = []
        for pos, density in self.quadrants.items():
            q.append((density, distances[pos][1], pos))
        q.sort(key=lambda x: (x[0] * 50 + x[1]))
        logging.info(f"selected {q[0]}")
        for q0 in q:
            if position := distances[q0[2]]:
                return position[0]

    def __str__(self):
        xx = [pos.x for pos in self.map.keys()]
        yy = [pos.y for pos in self.map.keys()]
        lines = []
        for y in range(min(yy), max(yy) + 1):
            line = ""
            for x in range(min(xx), max(xx) + 1):
                if content := self.map.get(Position(x, y)):
                    line += content[0][0]
                else:
                    line += "·"
            lines.append(line)
        return "\n".join(lines)

    def show_q(self, x, y):
        self.compute_asteroids_density_by_quadrant()



class BotLogic:
    """
    A bot that just moves randomly trying to hurt enemies, doesn't care about anything else.
    """

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        """
        This bot doesn't need to initialize anything except using a custom icon.
        """
        self.icon = "MA"
        self.map_radius = map_radius
        self.players = players
        self.turns = turns
        self.home_base_positions = home_base_positions
        self.map = Map(map_radius, home_base_positions)
        self.player_name = player_name
        self.turns = []
        self.memory = None

    def jump_towards(self, origin, destination, speed, reverse=False):
        dest = []
        for pos in origin.positions_in_range(speed):
            if abs(pos.x) <= self.map_radius and abs(pos.y) <= self.map_radius:
                dest.append((pos.distance_to(destination), pos))
        dest.sort(key=lambda x: x[0], reverse=reverse)
        return dest[0][1]

    def strategy_harvest(self, turn):
        """
        Just put all the enery on engines, grab all the asteroids and came back home.
        """
        self.icon = "aa"
        self.map.get_nearest_objects(turn.position)
        asteroid = self.map.nearest_asteroid
        home_base = self.map.nearest_home_base

        target = None
        if turn.cargo:
            if home_base and asteroid and turn.cargo < MAX_CARGO:
                if turn.position.distance_to(asteroid) > turn.speed:
                    target = home_base
                else:
                    target = asteroid
        elif asteroid:
            target = asteroid

        if turn.cargo > 0 and home_base:
            target = home_base

        if target:
            logging.info(f"Flying towards {target} {turn.position =}")
            if target in turn.position.positions_in_range(turn.speed):
                if target == asteroid:
                    self.map.remove(target)
                return FLY_TO, target
        desired_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
        if turn.power_distribution != desired_distribution:
            logging.info(f"{turn.power_distribution =} {desired_distribution =}")
            return POWER_TO, desired_distribution

        if self.memory:
            return self.fly_distant(turn, self.memory)

        self.map.compute_asteroids_density_by_quadrant()
        if targetq := self.map.distance_to_quadrants(turn.position):
            return self.fly_distant(turn, targetq)
        if target:
            return self.fly_distant(turn, target)

        return

    def fly_distant(self, turn, destinity):
        self.icon = "xx"
        next_target = self.jump_towards(turn.position, destinity, turn.speed)
        if next_target not in turn.position.positions_in_range(turn.speed) \
                or turn.position.distance_to(next_target) < turn.speed:
            selected, max_dist = None, 0
            for destination in turn.position.positions_in_range(turn.speed):
                if turn.position.distance_to(destination) > max_dist:
                    selected = destination
                    max_dist =turn.position.distance_to(destination)
            next_target = selected

        logging.info(f"Flying towards  {next_target} {turn.position =}")
        self.memory = destinity
        return FLY_TO, next_target

    def strategy_attack(self, turn):
        # move to a random destination, but avoid asteroids so we can keep pirating
        asteroid_positions = set(
            position
            for position, thing in turn.radar_contacts.items()
            if thing == ASTEROID
        )
        # keep trying until you get a clear position
        for destination in turn.position.positions_in_range(1):
            if destination not in asteroid_positions:
                return FLY_TO, destination

    def strategy_miner(self, turn):
        if turn.cargo:
            # run home
            home_base_position = Position(0, 0)
            reacheable_positions = list(turn.position.positions_in_range(turn.speed))
            closest_to_home = min(
                reacheable_positions, key=lambda p: p.distance_to(home_base_position)
            )
            return FLY_TO, closest_to_home
        else:
            for contact_pos, contact_type in turn.radar_contacts.items():
                if contact_type == ASTEROID:
                    # fly to the first asteroid we see
                    reacheable_positions = list(
                        turn.position.positions_in_range(turn.speed)
                    )
                    closest_to_asteroid = min(
                        reacheable_positions, key=lambda p: p.distance_to(contact_pos)
                    )
                    return FLY_TO, closest_to_asteroid
            # explore randomly
            return FLY_TO, random.choice(
                list(turn.position.positions_in_range(turn.speed))
            )

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
        """
        This bot sets up power to the lasers and just moves randomly, expecting to hurt other ships
        in the process.
        """

        turn = Turn(
            turn_number,
            hp,
            ship_number,
            cargo,
            position,
            power_distribution,
            radar_contacts,
            leader_board,
        )
        self.map.update(turn)

        action = self.strategy_harvest(turn)
        if not action:
            action = self.strategy_attack(turn)
        if self.turns:
            lastturn, lastaction = self.turns[-1]
            if lastturn.position == turn.position and lastaction[0] == FLY_TO:
                logging.info(f"ERROR: last turn {lastturn =} {lastaction =} {turn =}")
                # breakpoint()
                action = self.strategy_miner(turn)

        self.turns.append((turn, action))
        return action
