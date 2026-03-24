import random

from tv.game import Position, ASTEROID, POWER_TO, FLY_TO, ENGINES, SHIELDS, LASERS, SPACESHIP

class BotLogic:
    """
    A bot that just moves randomly trying to hurt enemies, doesn't care about anything else.
    """
    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        """
        This bot doesn't need to initialize anything.
        """
        self.home_base_position = Position(0, 0)
        self.home_base = home_base_positions
        self.last_reacheable_positions = home_base_positions
        self.map_radius = map_radius
        self.corners = [
                        Position(map_radius-1,map_radius-1),
                        Position(-map_radius+1,map_radius-1),
                        Position(map_radius-1, -map_radius+1),
                        Position(-map_radius-1, -map_radius-1),
                        Position(map_radius-2,map_radius-2),
                        Position(-map_radius+2,map_radius-2),
                        Position(map_radius-2, -map_radius+2),
                        Position(-map_radius-2, -map_radius-2)
                        ]


        old_positions_in_range_func = Position.positions_in_range


        def positions_in_range_fixed_to_map_size(_self, radius):
            positions = old_positions_in_range_func(_self, radius)

            for x, y in positions:
                if abs(x) > map_radius or abs(y) > map_radius:
                    continue
                yield Position(x, y)
        Position.positions_in_range = positions_in_range_fixed_to_map_size


    def ocupied(self, radar_contacts, destination):
        enemies_positions = set(position for position, thing in radar_contacts.items() if thing == SPACESHIP)
        return destination in enemies_positions

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution, radar_contacts, leader_board):
        """
        This bot sets up power to the lasers and just moves randomly, expecting to hurt other ships
        in the process.
        """
        speed = power_distribution[ENGINES] - cargo
        asteroid_positions = set(position for position, thing in radar_contacts.items() if thing == ASTEROID)
        reacheable_positions = list(position.positions_in_range(speed))
        asterods_inrange = set(position.positions_in_range(speed)).intersection(asteroid_positions)


        if turn_number == 0:
            initial_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
            self.last_reacheable_positions = reacheable_positions
            return POWER_TO, initial_distribution

        elif cargo == 1:
            # walk home
            asterod_close = set(position.positions_in_range(3)).intersection(asteroid_positions)

            if asterods_inrange:
                self.last_reacheable_positions = reacheable_positions
                return FLY_TO, min(asterod_close, key=lambda p: p.distance_to(position))

            else:
                go_to = min(reacheable_positions, key=lambda p: p.distance_to(self.home_base_position))
                # if self.ocupied(radar_contacts, go_to):
                #     go_to = min(max(reacheable_positions, key=lambda p: p.distance_to(self.home_base_position)))

                self.last_reacheable_positions = reacheable_positions
                return FLY_TO, go_to



        elif cargo == 2:
            # run home
            closest_to_home = min(reacheable_positions, key=lambda p: p.distance_to(self.home_base_position))
            self.last_reacheable_positions = reacheable_positions
            return FLY_TO, closest_to_home

        else:
            # find closest asteriod and run to it

            if asterods_inrange:
                closest_asterod = min(asterods_inrange, key=lambda p: p.distance_to(position))
                self.last_reacheable_positions = reacheable_positions
                return FLY_TO, closest_asterod

            else:
              #  position_range = list(position.positions_in_range(speed))
                go_to = random.choice(list(set(position.positions_in_range_exactly(speed)) - self.home_base - set(self.last_reacheable_positions)- set(self.corners)))
                if not go_to:
                    go_to = random.choice(list(set(position.positions_in_range_exactly(speed)) - self.home_base - self.corners))

                self.last_reacheable_positions = reacheable_positions
                return FLY_TO, go_to

        #Already Won strategy
