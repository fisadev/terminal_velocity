import random

from tv.game import MAX_POWER


class BotLogic:
    """
    A bot that just moves randomly and reconfigures the spaceship randomly.
    """
    def initialize(self):
        """
        This bot doesn't need to initialize anything.
        """
        pass

    def turn(self, hp, cargo, position, power_distribution, radar_contacts):
        """
        This bot chooses its actions completely at random.
        """
        if random.random() < 0.8:
            # move to a random destination
            speed = power_distribution["engines"]
            possible_destinations = list(position.positions_in_range(speed))
            destination = random.choice(possible_destinations)

            return "fly_to", destination
        else:
            # randomly distribute power
            power_distribution = {"engines": 0, "shields": 0, "lasers": 0}
            for _ in range(MAX_POWER):
                system = random.choice(["engines", "shields", "lasers"])
                power_distribution[system] += 1

            return "power_to", power_distribution
