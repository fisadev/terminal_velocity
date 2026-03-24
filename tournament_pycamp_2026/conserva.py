import random

from tv.game import Position, ASTEROID, POWER_TO, FLY_TO, ENGINES, SHIELDS, LASERS, RADAR_RADIUS

class BotLogic:
    """
    A bot that just moves randomly trying to hurt enemies, doesn't care about anything else.
    """
    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.map_init = [[False for _ in range(0 - map_radius, 0 + map_radius)] for _ in range(0 - map_radius, 0 + map_radius)]
        self.world = [Position(x,y) for x in range(0-map_radius, 0+map_radius+1) for y in range(0-map_radius,0+map_radius+1)]
        for position in home_base_positions:
            self.map_init[position.x][position.y] = True 
        self.map = self.map_init
        self.turns = turns
        self.home_base_positions = home_base_positions
        self.speed = 1
        self.current_position = Position(0,0)
        self.map_radius = map_radius
        self.asteroids = []
        self.first = True
        self.largo_recorrido = 5
        self.patron_movimiento = self.espiral_radio(0, 0, self.largo_recorrido, self.map_radius)
        self.voy_a_buscarlo = 6
        pass

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution, radar_contacts, leader_board):
        """
        This bot sets up power to the lasers and just moves randomly, expecting to hurt other ships
        in the process.
        """
        self.map[position.x][position.y] = True
        self.speed = power_distribution[ENGINES] - cargo
        self.current_position = position
        if self.first:
            self.first = False
            self.patron_movimiento = self.espiral_radio(position.x, position.y, self.largo_recorrido, self.map_radius)
            desired_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
            if power_distribution != desired_distribution:
                return POWER_TO, desired_distribution 
        
        # Limpio asteroides que ya no estan
        refresh_matches = [x for x in self.asteroids if x in position.positions_in_range(RADAR_RADIUS)]
        for obj_matched in refresh_matches:
            if obj_matched not in list(radar_contacts.keys()):
                self.asteroids.remove(obj_matched)
        if cargo:
            self.vengo_caliente = True
            self.map = self.map_init
            # desired_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
            # if power_distribution != desired_distribution:
            #     return POWER_TO, desired_distribution
            # run home
            home_base_position = Position(0, 0)
            reacheable_positions = list(position.positions_in_range(self.speed))
            closest_to_home = min(reacheable_positions, key=lambda p: p.distance_to(home_base_position))
            return FLY_TO, closest_to_home
        else:
            # desired_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
            # if power_distribution != desired_distribution:
            #     return POWER_TO, desired_distribution
            for contact_pos, contact_type in radar_contacts.items():
                if contact_type == ASTEROID:
                    if contact_pos not in self.asteroids:
                        self.asteroids.append(contact_pos)
            if self.asteroids:            
              self.asteroids.sort(key=lambda x:self.current_position.distance_to(x))
              obj = self.asteroids[0]
              if position.distance_to(obj) < self.voy_a_buscarlo:
                # fly to the closest asteroid we see
                reacheable_positions = list(position.positions_in_range(self.speed))
                closest_to_asteroid = min(reacheable_positions, key=lambda p: p.distance_to(obj))
                if obj.distance_to(closest_to_asteroid) == 0:
                    self.asteroids.remove(obj)
                return FLY_TO, closest_to_asteroid
            # explore
            return FLY_TO, self.next_step()

    def next_step(self):
        reacheable_positions = list(self.current_position.positions_in_range(self.speed))
        posibles = [x for x in reacheable_positions if x in self.world]
        obj = self.patron_movimiento[0]
        closest_to_obj = min(posibles, key=lambda p: p.distance_to(obj))
        if closest_to_obj.distance_to(obj) < 2:
            self.patron_movimiento.remove(obj)
        return closest_to_obj

    def espiral_radio(self, x0, y0, N, R):
        x, y = x0, y0
        d = self.movimiento()
        d = [1, 0]
        dx, dy = d[0], d[1]
        limite = 1
        pasos = 0
        cambios = 0

        resultado = []

        while True:
            # avanzar
            x += dx * N
            y += dy * N
            pasos += 1

            # condición: dentro del radio (cuadrado)
            if abs(x - x0) <= R and abs(y - y0) <= R:
                resultado.append(Position(x, y))
            else:
                # si ya salimos del rango en esta expansión, cortamos
                break

            # lógica de giro
            if pasos == limite:
                pasos = 0
                dx, dy = -dy, dx
                cambios += 1

                if cambios % 2 == 0:
                    limite += 1

        return resultado

    def movimiento(self):
        if random.random() < 0.5:
            return (0, random.choice([-1, 1]))
        else:
            return (random.choice([-1, 1]), 0)

class Espiral:

    def espiral_radio(self, x0, y0, N, R):
        x, y = x0, y0
        d = self.movimiento()
        dx, dy = d[0], d[1]
        limite = 1
        pasos = 0
        cambios = 0

        resultado = []

        while True:
            # avanzar
            x += dx * N
            y += dy * N
            pasos += 1

            # condición: dentro del radio (cuadrado)
            if abs(x - x0) <= R and abs(y - y0) <= R:
                resultado.append(Position(x, y))
            else:
                # si ya salimos del rango en esta expansión, cortamos
                break

            # lógica de giro
            if pasos == limite:
                pasos = 0
                dx, dy = -dy, dx
                cambios += 1

                if cambios % 2 == 0:
                    limite += 1

        return resultado

    def movimiento(self):
        if random.random() < 0.5:
            return (0, random.choice([-1, 1]))
        else:
            return (random.choice([-1, 1]), 0)
