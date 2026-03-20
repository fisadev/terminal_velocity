import random


class BotLogic:
    """
    A bot that just moves randomly trying to hurt enemies, doesn't care about anything else.
    """
    def initialize(self):
        """
        This bot doesn't need to initialize anything.
        """
        pass

    def turn(self, hp, cargo, position, power_distribution, radar_contacts):
        """
        This bot sets up power to the lasers and just moves randomly, expecting to hurt other ships
        in the process.
        """
        desired_distribution = {"engines": 1, "shields": 0, "lasers": 2}

        if power_distribution != desired_distribution:
            return "power_to", desired_distribution
        else:
            # move to a random destination
            return "fly_to", random.choice(list(position.positions_in_range(1)))
