import random
from tv.game import (
    Position,
    POWER_TO,
    FLY_TO,
    ENGINES,
    SHIELDS,
    LASERS,
    ASTEROID,
    SPACESHIP,
    RADAR_RADIUS,
    ATTACK_RADIUS,
)

# Configuraciones de Poder
SPEED_CONFIG = {ENGINES: 3, SHIELDS: 0, LASERS: 0}  # Velocidad Máxima
DEFENSE_CONFIG = {ENGINES: 1, SHIELDS: 2, LASERS: 0}  # Máximo Escudo
ATTACK_CONFIG = {ENGINES: 0, SHIELDS: 0, LASERS: 3}  # Máximo Ataque


class BotLogic:
    """
    Vieja Mula: Estrategia Equilibrada.
    - Velocidad máxima para buscar y entregar.
    - Escudos reactivos solo si hay peligro real.
    - Exploración sistemática de zonas desconocidas.
    """

    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        self.player_name = player_name
        self.map_radius = map_radius
        self.home_base_positions = list(home_base_positions)
        self.icon = "👵🐴"

        # Memoria persistente del mapa
        self.map_memory = {}
        for x in range(-map_radius, map_radius + 1):
            for y in range(-map_radius, map_radius + 1):
                self.map_memory[Position(x, y)] = ("unknown", -1)

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
        # 1. Actualizar Memoria
        self.update_memory(turn_number, position, radar_contacts)

        # 2. Análisis del entorno
        enemies_in_radar = [
            pos for pos, type in radar_contacts.items() if type == SPACESHIP
        ]
        closest_enemy = (
            min(enemies_in_radar, key=lambda e: position.distance_to(e))
            if enemies_in_radar
            else None
        )
        enemy_dist = (
            position.distance_to(closest_enemy) if closest_enemy else float("inf")
        )

        # 3. Decisiones de Poder (Reactividad)
        # Si un enemigo está en rango de ataque, nos defendemos
        if enemy_dist <= ATTACK_RADIUS:
            if hp <= 2:  # Si estamos muriendo, escudo a tope
                target_power = DEFENSE_CONFIG
            else:  # Si tenemos vida, atacamos de vuelta
                target_power = ATTACK_CONFIG

            if power_distribution != target_power:
                return POWER_TO, target_power
            if target_power == ATTACK_CONFIG:
                return None  # Disparo automático

        # Por defecto, máxima velocidad
        if power_distribution != SPEED_CONFIG:
            return POWER_TO, SPEED_CONFIG

        # 4. Decisiones de Movimiento
        # Prioridad 1: Entregar si tenemos carga
        if cargo >= 1:
            target_home = min(
                self.home_base_positions, key=lambda p: p.distance_to(position)
            )
            return self.navigate(position, target_home, cargo)

        # Prioridad 2: Ir al asteroide más cercano recordado
        target_asteroid = self.find_closest_in_memory(ASTEROID, position)
        if target_asteroid:
            return self.navigate(position, target_asteroid, cargo)

        # Prioridad 3: Explorar el lugar menos visto recientemente
        target_explore = self.find_least_seen(position)
        return self.navigate(position, target_explore, cargo)

    def update_memory(self, turn_number, position, radar_contacts):
        for p in position.positions_in_range(RADAR_RADIUS):
            self.map_memory[p] = ("empty", turn_number)
        for pos, type in radar_contacts.items():
            self.map_memory[pos] = (type, turn_number)

    def find_closest_in_memory(self, target_type, position):
        candidates = [p for p, (t, turn) in self.map_memory.items() if t == target_type]
        if not candidates:
            return None
        return min(candidates, key=lambda p: p.distance_to(position))

    def find_least_seen(self, position):
        # Priorizar celdas lejanas y antiguas para cubrir el mapa
        items = list(self.map_memory.items())
        # No explorar la base
        items = [i for i in items if i[0] not in self.home_base_positions]

        def score_explore(item):
            pos, (type, turn) = item
            dist = pos.distance_to(position)
            # Queremos el turno más bajo (antiguo) y distancia equilibrada
            return turn + (dist / self.map_radius)

        best_pos, _ = min(items, key=score_explore)
        return best_pos

    def navigate(self, src, dst, cargo):
        # Velocidad real = Motores (3) - Peso del cargo
        speed = max(0, 3 - cargo)
        if speed == 0:
            return FLY_TO, src

        possible_moves = [
            p
            for p in src.positions_in_range(speed)
            if abs(p.x) <= self.map_radius and abs(p.y) <= self.map_radius
        ]

        if not possible_moves:
            return FLY_TO, src

        # Moverse hacia el objetivo con un poco de aleatoriedad para evitar bloqueos
        return FLY_TO, min(
            possible_moves, key=lambda p: p.distance_to(dst) + random.uniform(0, 0.1)
        )
