import logging
import random
from collections import namedtuple

from tv.game import (
    ASTEROID,
    ENGINES,
    FLY_TO,
    LASERS,
    POWER_TO,
    Position,
    SHIELDS,
    SPACESHIP,
)

logger = logging.getLogger(__name__)

TurnInfo = namedtuple(
    "TurnInfo",
    "turn_number hp ship_number cargo position power_distribution radar_contacts "
    "leader_board speed"
)

# modes
AGGRESIVE = "agressive"
CONSERVAT = "conservat"

# HOME
HOME_BASE_POSITION = Position(0, 0)


def log(*objs):
    logger.info(" ".join(map(str, objs)))


class BotLogic:
    """No contaban con nuestra astucia."""

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.player_name = player_name
        self.mode = None
        self.map_radius = map_radius
        self.total_game_turns = turns
        self.home_base_positions = set(home_base_positions)
        log("========= base", home_base_positions)

        self.journey_target = None

    def _recalculate_mode(self, turn_info):
        """Set the mode."""
        log("======== recalculate mode, prv", self.mode)
        _my_money = turn_info.leader_board[self.player_name]
        _total_money = sum(turn_info.leader_board.values())
        if _my_money >= 1000:
            i_am_rich = (_my_money / _total_money) > 0.5
        else:
            i_am_rich = False
        i_am_loaded = turn_info.cargo > 0
        log(f"=============== mode! rich={i_am_rich} loaded={i_am_loaded}")

        # base decision
        if i_am_rich or i_am_loaded:
            self.mode = CONSERVAT
        else:
            self.mode = AGGRESIVE

        # adjust
        near_to_end = turn_info.turn_number > self.total_game_turns * 0.8
        _top_player = sorted(turn_info.leader_board.items(), key=lambda kv: kv[1])[-1][0]
        i_am_losing = _top_player != self.player_name
        log(f"=============== mode! nearend={near_to_end} losing={i_am_losing}")
        if near_to_end and i_am_losing:
            self.mode = AGGRESIVE

        # fix icon
        if self.mode == CONSERVAT:
            self.icon = "=="
        else:
            self.icon = "++"

        log("======== recalculate mode, new", self.mode)

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
        """Move."""
        turn_info = TurnInfo(
            turn_number=turn_number,
            hp=hp,
            ship_number=ship_number,
            cargo=cargo,
            position=position,
            power_distribution=power_distribution,
            radar_contacts=radar_contacts,
            leader_board=leader_board,
            speed=power_distribution[ENGINES] - cargo,
        )
        log("=========== turn!", turn_info)
        self._recalculate_mode(turn_info)

        # short-circuit: if transporting back, and base is reachable, go for it
        shortest_distance, base_position = self._get_nearest_base(turn_info)
        if shortest_distance <= turn_info.speed and cargo > 0:
            # reachable! go for the base
            log("========== short-circuit to base")
            return FLY_TO, base_position

        return self._turn_alone(turn_info)

    def _calculate_next_target(self):
        """Calculate the position that will be the target for a new journey."""
        rad = self.map_radius
        x = random.randint(int(rad * 0.5), int(rad * 0.8))
        if random.random() > 0.5:
            x *= -1
        y = random.randint(int(rad * 0.5), int(rad * 0.8))
        if random.random() > 0.5:
            y *= -1
        self.journey_target = Position(x, y)

    def _turn_alone(self, turn_info):
        """Move in a scenario where we're alone."""
        log("============== turn, alone")
        desired_power = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
        if turn_info.power_distribution != desired_power and turn_info.turn_number > 2:
            log("================ setting power distrib to", desired_power)
            return POWER_TO, desired_power

        # moving as usual... decide if return to base or explore the space
        if turn_info.cargo > 0:
            log("=================== moving as usual, back to home")
            return self._escape_to_base(turn_info)
        log("=================== moving as usual, explore")

        # explore the space! if there is any asteroid, go for it
        all_asteroid_positions = {
            pos for pos, thing in turn_info.radar_contacts.items() if thing == ASTEROID
        }
        log("=========== asteroids? all:", all_asteroid_positions)
        if all_asteroid_positions:
            distances = [
                (turn_info.position.distance_to(pos), pos)
                for pos in all_asteroid_positions
            ]
            log("=========== asteroids? distances:", distances)
            shortest_distance, asteroid_position = sorted(distances)[0]
            if shortest_distance <= turn_info.speed:
                # reachable! go for the asteroid
                log("========== asteroid REACHABLE")
                return FLY_TO, asteroid_position

            # can't get to the asteroid in this move, find how to get closer
            reacheable = list(turn_info.position.positions_in_range(turn_info.speed))
            closest_to_asteroid = min(reacheable, key=lambda p: p.distance_to(asteroid_position))
            log("========== asteroid not reachable now, closest move:", closest_to_asteroid)
            return FLY_TO, closest_to_asteroid

        # no asteroids in sight, just keep moving to the target
        if self.journey_target is None or turn_info.position == self.journey_target:
            self._calculate_next_target()
        log("======== explore, target:", self.journey_target)

        distance = turn_info.position.distance_to(self.journey_target)
        if distance <= turn_info.speed:
            # reachable! go to target
            log("========== target REACHABLE")
            return FLY_TO, self.journey_target

        # can't get to the target in this move, find how to get closer
        reacheable = list(turn_info.position.positions_in_range(turn_info.speed))
        closest = min(reacheable, key=lambda p: p.distance_to(self.journey_target))
        log("========== target not reachable now, closest move:", closest)
        return FLY_TO, closest

    def _get_nearest_base(self, turn_info):
        """Find the closest spot in the base."""
        enemy_positions = {
            pos
            for pos, thing in turn_info.radar_contacts.items()
            if thing == SPACESHIP
        }
        available_positions = self.home_base_positions - enemy_positions
        log("============== escape available:", available_positions)
        distances = [
            (turn_info.position.distance_to(pos), pos)
            for pos in available_positions
        ]
        shortest_distance, base_position = sorted(distances)[0]
        return shortest_distance, base_position

    def _escape_to_base(self, turn_info):
        """Move to the base as fast as possible."""
        log("============== escape to base!")
        shortest_distance, base_position = self._get_nearest_base(turn_info)
        if shortest_distance <= turn_info.speed:
            # reachable! go for the base
            log("========== base REACHABLE")
            return FLY_TO, base_position

        # get a second asteroid if close to the base
        distance_from_center = turn_info.position.distance_to(HOME_BASE_POSITION)
        all_asteroid_positions = {
            pos for pos, thing in turn_info.radar_contacts.items() if thing == ASTEROID
        }
        if all_asteroid_positions and distance_from_center < 5:
            distances = [
                (turn_info.position.distance_to(pos), pos)
                for pos in all_asteroid_positions
            ]
            log("=========== asteroids? distances:", distances)
            shortest_distance, asteroid_position = sorted(distances)[0]
            if shortest_distance <= turn_info.speed:
                # reachable! go for the asteroid
                log("========== asteroid REACHABLE")
                return FLY_TO, asteroid_position

        if turn_info.speed == 0:
            cur_lasers = turn_info.power_distribution[LASERS]
            cur_shields = turn_info.power_distribution[SHIELDS]
            cur_engines = turn_info.power_distribution[ENGINES]
            if cur_lasers:
                desired = {ENGINES: cur_engines + 1, SHIELDS: cur_shields, LASERS: cur_lasers - 1}
            else:
                desired = {ENGINES: cur_engines + 1, SHIELDS: cur_shields - 1, LASERS: cur_lasers}
            return POWER_TO, desired

        # can't get to the base in this move, find how to get closer
        reacheable = list(turn_info.position.positions_in_range(turn_info.speed))
        closest_to_base = min(reacheable, key=lambda p: p.distance_to(base_position))
        log("========== base not reachable now, closest move:", closest_to_base)
        return FLY_TO, closest_to_base
