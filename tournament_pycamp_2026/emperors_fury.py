"""
________          ________
 ______/ /* ||  \ \______
  _____\___\\//___/_____
     ////|\//\\/|\\\\
           //\\
          <>\/<>

For the EMPEROR!
"""
from collections import Counter, defaultdict

from tv.game import(
    Position,
    POWER_TO, FLY_TO,
    LASERS, ENGINES, SHIELDS,
    ASTEROID, SPACESHIP,
    HOME_BASE_RADIUS,
)

def scroll_phrase(phrase, turn_number):
    """
    Scroll a phrase by turn number, so it can be used to create patterns.
    """
    seen_text = 2
    idx = turn_number % len(phrase)
    return phrase[idx:idx+seen_text].ljust(seen_text)


def generate_patrol_pattern(radius, center):
    """
    Generates patrol pattern based on radius.
    - Orthogonal movements only, no diagonals
    - Clockwise order starting from top-left corner
    """
    cx, cy = center.x, center.y
    positions = []

    # Top: left → right  (y = cy - radius, x goes from cx-radius to cx+radius)
    for x in range(cx - radius, cx + radius):
        positions.append(Position(x, cy - radius))

    # Right: top → bottom  (x = cx + radius, y goes from cy-radius to cy+radius)
    for y in range(cy - radius, cy + radius):
        positions.append(Position(cx + radius, y))

    # Bottom: right → left  (y = cy + radius, x goes from cx+radius to cx-radius)
    for x in range(cx + radius, cx - radius, -1):
        positions.append(Position(x, cy + radius))

    # Left: bottom → top  (x = cx - radius, y goes from cy+radius to cy-radius)
    for y in range(cy + radius, cy - radius, -1):
        positions.append(Position(cx - radius, y))

    return positions


def is_free(pos, radar, floor=None):
    """
    Check if a position is free of heresy
    """
    if floor:
        return floor not in (SPACESHIP, ASTEROID)

    radar_pos = radar.get(pos, None)

    if radar_pos:
        return radar_pos not in (SPACESHIP, ASTEROID)

    return True


def warp_closest_possible(position, destination, radar, movement):
    """
    Return closest Position possible to another one
    See if movement is possible to WARP to

    movement max possible value should be inside radar range
    """
    distances = defaultdict(list)

    positions_in_range = position.positions_in_range(movement)
    for pos in positions_in_range:
        if is_free(pos, radar):
            distance_to_destination = pos.distance_to(destination)
            distances[int(distance_to_destination)].append(pos)

    if distances:
        min_distance = min(distances)
        return distances[min_distance][0]

    return position


class BotLogic:
    """
    FURY INTERCEPTOR
    Main ship, patrols and shoot everyone who passes by

    FOR THE EMPEROR!
    """

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        """
        To be recognized to the others ships, the recognition pattern will be:
        Go to the center for 4 turns
        """
        self.TURNS = turns
        self.BASE = home_base_positions

        # --- MODES AND STRATEGY ---
        # Recognize the faithful ones to the emperor
        self.RECOGNITION = "RECOGNITION"
        self.RECOGNITION_TURNS = 4
        RECOGNITION_DISTRIBUTION = {
            ENGINES: 3,
            LASERS: 0,
            SHIELDS: 0
        }

        # Search for heretics
        self.HERETIC_SEARCH = "HERETIC_SEARCH"
        self.GO_TO_SEARCH = Position(0, HOME_BASE_RADIUS + 2)
        HERETIC_SEARCH_DISTRIBUTION = {
            ENGINES: 1,
            LASERS: 2,
            SHIELDS: 0
        }
        self.HERETIC_SEARCH_RADIUS = HOME_BASE_RADIUS + 3
        self.HERETIC_SEARCH_PATTERN = generate_patrol_pattern(self.HERETIC_SEARCH_RADIUS, Position(0, 0))
        self.SEARCH_PATTERN_LEN = len(self.HERETIC_SEARCH_PATTERN)

        # KILL HERETICS
        self.EXTERMINATUS = "EXTERMINATUS"
        EXTERMINATUS_DISTRIBUTION = {
            ENGINES: 0,
            LASERS: 3,
            SHIELDS: 0
        }
        self.EXTERMINATUS_MOMENTUM = 15  # %
        self.EXTERMINATUS_ROUND = turns - turns * (self.EXTERMINATUS_MOMENTUM / 100)

        self.loyals_recognized = 0
        self.regroup = False
        self.mode = self.RECOGNITION
        self.distribution = RECOGNITION_DISTRIBUTION

        self.DISTRIBUTIONS = {
            self.RECOGNITION: RECOGNITION_DISTRIBUTION,
            self.HERETIC_SEARCH: HERETIC_SEARCH_DISTRIBUTION,
            self.EXTERMINATUS: EXTERMINATUS_DISTRIBUTION,
            #self.STAND_BY: STAND_BY_DISTRIBUTION
        }

        self.recognition_results = []

    def solve_actual_mode(self, turns):
        if turns <= self.RECOGNITION_TURNS:
            self.mode = self.RECOGNITION
            self.distribution = self.DISTRIBUTIONS[self.mode]
            return

        if self.mode == self.RECOGNITION:
            self.mode = self.HERETIC_SEARCH
            return

    def recognition(self, position, turn_number, radar_contacts):
        """
        Recognize brothers
        """
        EMPEROR_CODE = [
            Position(1, 1),
            Position(1, 0),
            Position(-1, 1),
            Position(-1, 0)
        ]

        change = 0
        code = None
        possible_allies = 0

        for change in range(len(EMPEROR_CODE)):
            code_idx = (turn_number + change) % len(EMPEROR_CODE)
            code_step = EMPEROR_CODE[code_idx]

            if position.distance_to(code_step) > 3:
                continue

            if radar_contacts[code_step] == SPACESHIP:
                possible_allies += 1
            else:
                code = code_step

        if code is None:
            code = position

        self.recognition_results.append(possible_allies)
        return FLY_TO, code

    def heretic_search(self, position, radar, turn_number, power_distribution):
        """
        Follow patrol pattern
        """
        engines = power_distribution[ENGINES]

        if turn_number < self.patrol_starts_in:
            # Patrol didn't start yet, go to starting point
            movement = warp_closest_possible(
                position=position,
                destination=self.HERETIC_SEARCH_PATTERN[0],
                radar=radar,
                movement=engines
            )
        else:
            # Patrol started, follow the pattern
            if turn_number == self.patrol_starts_in:
                self.distribution = self.DISTRIBUTIONS[self.HERETIC_SEARCH]

            pattern_idx = self.patrol_idx % self.SEARCH_PATTERN_LEN
            movement = warp_closest_possible(
                position=position,
                destination=self.HERETIC_SEARCH_PATTERN[pattern_idx],
                radar=radar,
                movement=engines
            )
            self.patrol_idx += 1

        return FLY_TO, movement

    def prepatrol(self, turn_number):
        self.loyals_recognized = Counter(self.recognition_results).most_common(1)[0][0]
        self.patrol_starts_in = turn_number + 3
        self.patrol_idx = 1
        #self.icon = f"L{self.loyals_recognized}"

    def turn(
        self, turn_number, hp,
        ship_number, cargo, position,
        power_distribution, radar_contacts,
        leader_board
    ):
        new_pos = Position(position.x, position.y + 1)
        self.solve_actual_mode(turn_number)

        if self.mode in (self.RECOGNITION, self.HERETIC_SEARCH):
            phrase = "FOR THE EMPEROR! "

            self.icon = scroll_phrase(phrase, turn_number)
        else:
            self.icon = scroll_phrase("EXTERMINATUS! ", turn_number)

        if power_distribution != self.distribution:
            return POWER_TO, self.distribution

        if self.mode == self.RECOGNITION:
            return self.recognition(position, turn_number, radar_contacts)

        if turn_number == self.RECOGNITION_TURNS+1:
            self.prepatrol(turn_number)

        if position == Position(0, 0):
            # We failed the Emperor, we died. We must return to battle brothers!
            self.mode = self.HERETIC_SEARCH
            self.regroup = True
            self.regroup_countdown = 3
            return self.heretic_search(position, radar_contacts, turn_number, power_distribution)

        if self.regroup:
            if self.regroup_countdown > 0:
                self.regroup_countdown -= 1
                return self.heretic_search(position, radar_contacts, turn_number, power_distribution)

            self.regroup = False

        if turn_number >= self.EXTERMINATUS_ROUND and self.mode != self.EXTERMINATUS:
            self.mode = self.EXTERMINATUS
            self.distribution = self.DISTRIBUTIONS[self.mode]
            return POWER_TO, self.distribution

        if self.mode == self.HERETIC_SEARCH:
            return self.heretic_search(position, radar_contacts, turn_number, power_distribution)

