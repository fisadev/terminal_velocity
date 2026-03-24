from random import shuffle
from tv.game import Position, POWER_TO, FLY_TO, LASERS, ENGINES, SHIELDS, SPACESHIP, ASTEROID, HOME_BASE, RADAR_RADIUS, ATTACK_RADIUS

EMPTY = 'empty'

GENESIS_ICON = 'GE'
ACCELERATE_ICON = 'AC'
FIND_ICON = 'FI'
BACK_ICON = '<-'
EXPLORE_ICON = ':)'
ANGRY_ICON = ':('

SHOOT_CONFIG = {ENGINES: 0, SHIELDS: 0, LASERS: 3}
MOVE_CONFIG = {ENGINES: 3, SHIELDS: 0, LASERS: 0}

class BotLogic:
    def initialize(self, map_radius, players, turns, home_base_positions, player_name):
        self.icon = GENESIS_ICON
        self.map_radius = map_radius
        self.players = players
        self.turns = turns
        self.home_base_positions = home_base_positions
        self.player_name = player_name
        self.map = {
            Position(i, j): (EMPTY, 0)
            for i in range(-map_radius, map_radius+1)
            for j in range(-map_radius, map_radius+1)
        }
        self.hp = 5
        self.turn_number = 0
        self.ship_number = 1
        self.cargo = 0
        self.position = Position(-1000, -1000)
        self.power_distribution = { ENGINES: 1, SHIELDS: 1, LASERS: 1 }
        self.radar_contacts = []
        self.leader_board = { player: 0 for player in players }

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution, radar_contacts, leader_board):
        self.turn_number = turn_number
        self.hp = hp
        self.ship_number = ship_number
        self.cargo = cargo
        self.position = position
        self.power_distribution = power_distribution
        self.radar_contacts = radar_contacts
        self.leader_board = leader_board

        for p in position.positions_in_range(RADAR_RADIUS):
            self.map[p] = (EMPTY, turn_number)
        for contact_pos, contact_type in radar_contacts.items():
            self.map[contact_pos] = (contact_type, turn_number)

        if cargo:
            self.icon = BACK_ICON
            return self.fly_to_home(position)

        closest_asteroid = self.closest(ASTEROID)

        if self.ñapi_time() and not self.aunque_me_maten_voy_primero():
            if closest_asteroid and closest_asteroid.distance_to(position) <= power_distribution[ENGINES]:
                self.icon = FIND_ICON
                return self.fly_to(position, closest_asteroid, [SPACESHIP])

            if position not in self.home_base_positions:
                closest_spaceship = self.closest(SPACESHIP, search_in_home=False)
                if closest_spaceship and closest_spaceship.distance_to(position) <= ATTACK_RADIUS:
                    self.icon = ANGRY_ICON
                    return POWER_TO, SHOOT_CONFIG

        if closest_asteroid:
            self.icon = FIND_ICON
            return self.fly_to(position, closest_asteroid, [SPACESHIP])

        ## Go to the least known close place
        weirdest_place = self.closest(EMPTY, recent=False)
        self.icon = EXPLORE_ICON
        return self.fly_to(position, weirdest_place, [SPACESHIP])

    def fly_to(self, src, dst, forbidden=[]):
        if self.power_distribution != MOVE_CONFIG:
            self.icon = ACCELERATE_ICON
            return POWER_TO, MOVE_CONFIG

        speed = self.power_distribution[ENGINES] - self.cargo

        possible_positions = (
            p for p in src.positions_in_range(speed)
            if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius and self.map[p][0] not in forbidden
        )
        return FLY_TO, min(possible_positions, key=lambda p: p.distance_to(dst))

    def fly_to_home(self, src):
        dst = min(
            (
                p for p in self.home_base_positions
                if self.map[p][0] != SPACESHIP
            ),
            key=lambda p: p.distance_to(src)
        )
        return self.fly_to(src, dst, [SPACESHIP, ASTEROID])

    def ñapi_time(self):
        average_score = sum(
            score for name, score in self.leader_board.items()
            if name != self.player_name
        )
        average_score /= (len(self.leader_board) - 1)
        return 350 < average_score

    def aunque_me_maten_voy_primero(self):
        current_score = self.leader_board[self.player_name]
        score_after_death = int(current_score * 0.9)
        gain = current_score - score_after_death + (50 if self.cargo else 0)
        return all(score + gain < score_after_death for name, score in self.leader_board.items() if name != self.player_name)

    def closest(self, expected_kind, recent=True, search_in_home=False):
        map = list(self.map.items())
        shuffle(map)

        if recent:
            criteria = lambda v: (v[0].distance_to(self.position), -v[1])
        else:
            criteria = lambda v: (v[1], v[0].distance_to(self.position))

        closest, _ = min(
            (
                (position, seen)
                for (position, (kind, seen)) in map
                if kind == expected_kind and (search_in_home or position not in self.home_base_positions)
            ),
            key=criteria,
            default=(None, None)
        )
        return closest
