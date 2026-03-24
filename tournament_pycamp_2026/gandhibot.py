import random
from tv.game import (Position, SPACESHIP, ASTEROID, HOME_BASE, FLY_TO, POWER_TO, VALID_ACTIONS, ENGINES, SHIELDS,
LASERS, POWERED_SYSTEMS, MAX_HP, MAX_POWER, MAX_CARGO, MINING_REWARD, PIRATING_REWARD, HOME_BASE_RADIUS, RADAR_RADIUS,
ATTACK_RADIUS, ASTEROIDS_DENSITY)
EMPTY = 'empty'


class BotLogic:

    def initialize(self, player_name, map_radius, players, turns, home_base_positions, player_name):

        self.icon = ' ඞ'
        self.map_radius = map_radius
        self.players = players
        self.path = []
        self.map = {Position(i, j): (EMPTY, 0)
                    for i in range(-map_radius, map_radius+1)
                    for j in range(-map_radius, map_radius+1)}

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution, radar_contacts, leader_board):

        def generate_path(position, bound, step):

            # Initialize coordinates and path
            x, y = position
            path = []
            step_length = 1
            directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

            while True:
                # for every direction
                for i in range(4):
                    dx, dy = directions[i]

                    # move step_length times in this direction
                    for _ in range(step_length):
                        x += dx * step
                        y += dy * step

                        # stop if out of map bounds
                        if abs(x) > bound or abs(y) > bound:
                            return path

                        # append this position to the path
                        path.append(Position(x, y))

                    # Increase step_length every 2 directions
                    if i % 2 == 1:
                        step_length += 1

        # define some stuff
        speed = power_distribution[ENGINES] - cargo
        home_base_position = Position(0, 0)
        reacheable_positions = list(position.positions_in_range(speed))
        closest_to_home = min(reacheable_positions, key=lambda p: p.distance_to(home_base_position))
        speed_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}

        # speed is life
        if power_distribution != speed_distribution:
            return POWER_TO, speed_distribution

        # fill memory map as you go
        for p in position.positions_in_range(RADAR_RADIUS):
            self.map[p] = (EMPTY, turn_number)
        for contact_pos, contact_type in radar_contacts.items():
            self.map[contact_pos] = (contact_type, turn_number)

        # generate spiral path
        if not self.path or position == home_base_position:
            self.path = generate_path(position, self.map_radius, speed)

        # if cargo return home
        if cargo:
            return FLY_TO, closest_to_home

        # otherwise find recent asteroids
        recent_asteroids = [pos for pos, (kind, seen) in self.map.items()
                            if kind == ASTEROID and turn_number - seen < 20]

        # if there are, get as close as possible to it
        if recent_asteroids:
            target = min(recent_asteroids, key=lambda p: p.distance_to(position))
            new_tile = min(reacheable_positions, key=lambda p: p.distance_to(target))

        else:

            # otherwise get target from spiral path
            target = self.path[0]

            # build occupied set
            occupied = {pos for pos, t in radar_contacts.items()if t == SPACESHIP}

            # move to safest position in distance
            safe_positions = [p for p in reacheable_positions if p not in occupied]
            if not safe_positions:
                safe_positions = reacheable_positions
            new_tile = min(safe_positions,key=lambda p: p.distance_to(target))

            # advance path if we reached (or close enough)
            if new_tile.distance_to(target) <= speed:
                self.path.pop(0)

        # go to next target
        return FLY_TO, new_tile



