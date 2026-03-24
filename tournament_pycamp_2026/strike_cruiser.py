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
from tv.game import (
    Position,
    FLY_TO, POWER_TO,
    ENGINES, SHIELDS, LASERS,
    HOME_BASE_RADIUS,
    ASTEROID, SPACESHIP
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

    # Bottom: right → left  (y = cy + radius, x goes from cx+radius to cx-radius)
    for x in range(cx + radius, cx - radius, -1):
        positions.append(Position(x, cy + radius))

    # Left: bottom → top  (x = cx - radius, y goes from cy+radius to cy-radius)
    for y in range(cy + radius, cy - radius, -1):
        positions.append(Position(cx - radius, y))

    # Top: left → right  (y = cy - radius, x goes from cx-radius to cx+radius)
    for x in range(cx - radius, cx + radius):
        positions.append(Position(x, cy - radius))

    # Right: top → bottom  (x = cx + radius, y goes from cy-radius to cy+radius)
    for y in range(cy - radius, cy + radius):
        positions.append(Position(cx + radius, y))

    return positions

def is_free(pos, radar, floor=None):
    """
    Check if a position is free of heresy
    """
    if floor:
        return floor is not SPACESHIP

    radar_pos = radar.get(pos, None)

    if radar_pos:
        return radar_pos is not SPACESHIP

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


def scan_asteroids(radar, position):
    """
    Scan for asteroids in radar
    """
    asteroids = defaultdict(list)

    for pos, floor in radar.items():
        if floor == ASTEROID:
            asteroids[position.distance_to(pos)].append(pos)

    asteroids_found = bool(asteroids)
    return asteroids, asteroids_found


def closest_base(base, position):
    """
    Return closest base to a position
    """
    if not base:
        return position, False

    distances = defaultdict(list)
    for pos in base:
        distances[position.distance_to(pos)].append((pos, pos in base))

    return distances[min(distances)][0]


class BotLogic:
    """
    EMPEROR's STRIKE CRUISER
    Versatile and aggresive ship, loots and shoots, following a patrol pattern

    FOR THE EMPEROR!
    """
    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.TURNS = turns
        self.BASE = home_base_positions

        # --- MODES AND STRATEGY ---
        # Recognize the faithful ones to the emperor by the EMPEROR's CODE
        self.RECOGNITION = "RECOGNITION"
        self.RECOGNITION_TURNS = 4
        RECOGNITION_DISTRIBUTION = {
            ENGINES: 3,
            LASERS: 0,
            SHIELDS: 0
        }

        # Search for heretics and relics
        self.SEARCH = "SEARCH"
        SEARCH_DISTRIBUTION = {
            ENGINES: 2,
            LASERS: 1,
            SHIELDS: 0
        }
        SEARCH_RADIUS = HOME_BASE_RADIUS + 3
        self.SEARCH_PATTERN = generate_patrol_pattern(SEARCH_RADIUS, Position(0, 0))
        self.SEARCH_PATTERN_LEN = len(self.SEARCH_PATTERN)

        # Capture relics
        self.CAPTURE = "CAPTURE"
        CAPTURE_DISTRIBUTION = {
            ENGINES: 3,
            LASERS: 0,
            SHIELDS: 0
        }

        # EXTERMINATUS
        self.EXTERMINATUS = "EXTERMINATUS"
        EXTERMINATUS_DISTRIBUTION = {
            ENGINES: 0,
            LASERS: 3,
            SHIELDS: 0
        }
        self.EXTERMINATUS_MOMENTUM = 10  # %
        self.EXTERMINATUS_ROUND = turns - turns * (self.EXTERMINATUS_MOMENTUM / 100)

        self.DISTRIBUTIONS = {
            self.RECOGNITION: RECOGNITION_DISTRIBUTION,
            self.SEARCH: SEARCH_DISTRIBUTION,
            self.CAPTURE: CAPTURE_DISTRIBUTION,
            self.EXTERMINATUS: EXTERMINATUS_DISTRIBUTION
        }

        self.regroup = False
        self.in_base = False
        self.mode = self.RECOGNITION
        self.distribution = RECOGNITION_DISTRIBUTION
        self.recognition_results = []

    @property
    def loyals_recognized(self):
        return (
            Counter(self.recognition_results).most_common(1)[0][0]
            if self.recognition_results else 0
        )

    def solve_actual_mode(self, turn_n):
        """
        Change self.mode of ship, depending on turn
        """
        if turn_n <= self.RECOGNITION_TURNS:
            self.mode = self.RECOGNITION
            self.distribution = self.DISTRIBUTIONS[self.mode]
            return

        if self.mode == self.RECOGNITION:
            self.mode = self.SEARCH
            return

    def recognition(self, position, turn_number, radar_contacts):
        """
        Recognize brothers
        """
        EMPEROR_CODE = [
            Position(-1, 1),
            Position(-1, 0),
            Position(1, 1),
            Position(1, 0),
        ]

        change = 0
        code = None
        possible_allies = 0

        for change, _ in enumerate(EMPEROR_CODE):
            code_idx = (turn_number + change) % len(EMPEROR_CODE)
            code_step = EMPEROR_CODE[code_idx]

            if position.distance_to(code_step) > 3:
                continue

            if radar_contacts.get(code_step) == SPACESHIP:
                possible_allies += 1
            else:
                code = code_step

        if code is None:
            code = position

        self.recognition_results.append(possible_allies)
        return FLY_TO, code

    def prepatrol(self, turn_number):
        self.patrol_starts_in = turn_number + 3
        self.patrol_idx = 1

    def search(self, position, radar, turn_number, power_distribution, cargo):
        """
        Follow patrol pattern
        """
        engines = power_distribution[ENGINES]
        pattern_idx = self.patrol_idx % self.SEARCH_PATTERN_LEN

        if turn_number < self.patrol_starts_in:
            # Patrol didn't start yet, go to starting point
            movement = warp_closest_possible(
                position=position,
                destination=self.SEARCH_PATTERN[0],
                radar=radar,
                movement=engines
            )
            return FLY_TO, movement

        # Patrol started, follow the pattern
        if turn_number == self.patrol_starts_in:
            self.distribution = self.DISTRIBUTIONS[self.SEARCH]

        asteroids, asteroids_found = scan_asteroids(radar, position)
        if asteroids_found and not cargo:
            if self.mode != self.CAPTURE:
                self.mode = self.CAPTURE
                self.distribution = self.DISTRIBUTIONS[self.mode]
                return POWER_TO, self.distribution

            destination = asteroids[min(asteroids)][0]

        elif cargo:
            data = closest_base(self.BASE, position)
            destination = data[0]
            is_base = data[1]
            self.in_base = True

        elif self.in_base:
            self.in_base = False
            destination = self.SEARCH_PATTERN[pattern_idx]
        else:
            if self.mode != self.SEARCH:
                self.mode = self.SEARCH
                self.distribution = self.DISTRIBUTIONS[self.mode]
                return POWER_TO, self.distribution

            destination = self.SEARCH_PATTERN[pattern_idx]

        movement = warp_closest_possible(
            position=position,
            destination=destination,
            radar=radar,
            movement=engines - cargo,
        )
        self.patrol_idx += 1

        return FLY_TO, movement


    def turn(
        self, turn_number, hp, ship_number,
        cargo, position, power_distribution, radar_contacts, leader_board
    ):
        self.solve_actual_mode(turn_number)

        if self.mode in (self.RECOGNITION, self.SEARCH, self.CAPTURE):
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

        if turn_number >= self.EXTERMINATUS_ROUND and self.mode != self.EXTERMINATUS:
            self.mode = self.EXTERMINATUS
            self.distribution = self.DISTRIBUTIONS[self.mode]
            return POWER_TO, self.distribution

        if self.mode in (self.SEARCH, self.CAPTURE):
            return self.search(position, radar_contacts, turn_number, power_distribution, cargo)
