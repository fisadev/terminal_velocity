import random
from dataclasses import dataclass
from tv.game import (
    ENGINES, SHIELDS, LASERS,  # names of the powered systems
    FLY_TO, POWER_TO,  # action names
    MAX_CARGO, MAX_HP, MAX_POWER,  # game limits
    HOME_BASE, ASTEROID, SPACESHIP,  # radar contact types
    Position,
)

@dataclass
class BotContext:
    turn_number: int
    hp:int
    ship_number: int 
    cargo: int
    position: Position
    power_distribution: dict
    radar_contacts: dict[Position, str]
    leader_board: any
    available_moves: int

from dataclasses import dataclass



class BotLogic:
    def initialize(self, player_name, map_radius, players, turns, home_base_positions):
        """
        Here you can prepare your bot for the game.
        Use it to initialize variables, prepare strategies, etc.
        You can keep all the attributes you like in `self`.
        """
        self.icon = "]["
        self.PLAYER_NAME: str = player_name
        self.MAP_RADIUS: int = map_radius
        self.PLAYERS: list[str] = players
        self.TURNS: int = turns
        self.HOME_BASE_POSITIONS: set[Position] = home_base_positions
        self.map = {Position(x,y): (0, None) for x in range(-map_radius, map_radius) for y in range(-map_radius, map_radius) }
        self.visited_points: list = []
        self.reference_points = [Position(int(self.MAP_RADIUS*-0.8), int(self.MAP_RADIUS*-0.8)),
                                 Position(int(self.MAP_RADIUS*0.8), int(self.MAP_RADIUS*-0.8)),
                                 Position(int(self.MAP_RADIUS*0.8), int(self.MAP_RADIUS*0.8)),
                                 Position(int(self.MAP_RADIUS*-0.8), int(self.MAP_RADIUS*0.8))]

    def asteroids_in_map(self, context:BotContext):
        return [point for point, (turn, thing) in self.map.items() if thing == ASTEROID]

    def asteroids_in_radar(self,context:BotContext):
        '''Devuelve asteroides en radar'''
        return [point for point, thing in context.radar_contacts.items() if thing == ASTEROID]

    def spaceships_in_radar(self,context:BotContext):
        '''Devuelve spaceships en radar'''
        return [point for point, thing in context.radar_contacts.items() if thing == SPACESHIP]

    def valid_points_to_move_in_map(self,context:BotContext):
        return [point for point in context.position.positions_in_range(context.available_moves) 
                                        if abs(point.x) <= self.MAP_RADIUS and abs(point.y) <= self.MAP_RADIUS]

    def valid_point_to_explore(self,context:BotContext):
        points_to_avoid = [point for point, thing in context.radar_contacts.items() if thing in (HOME_BASE, SPACESHIP)]
        valid_points_to_move = self.valid_points_to_move_in_map(context)
        points_to_avoid.extend(self.visited_points)
        return [point for point in valid_points_to_move if point not in points_to_avoid] 

    def closest_asteroid_at_range(self, context:BotContext)-> None | list[Position]:
        '''Devolver la lista de posiciones de asteoides a los que puedo llegar con la configuracion actual'''
        close_asteroides = self.asteroids_in_radar(context)
        return min(close_asteroides, key=lambda p: p.distance_to(context.position))

    def closest_asteroid_in_map(self, context:BotContext)-> Position:
        '''Lista de asteroides vistos en el mapa'''
        asteorids = self.asteroids_in_map(context)
        return min(asteorids, key=lambda p: p.distance_to(context.position))

    def closest_point_to_closest_asteroid(self, context:BotContext):
        # check points available
        spaceships_points = self.spaceships_in_radar(context)
        valid_points_to_move = self.valid_points_to_move_in_map(context)
        valid_points_to_move_empty = [point for point in valid_points_to_move if point not in spaceships_points]
        # check closest homebase point
        closest_asteroid = self.closest_asteroid_in_map(context) 
        closest_point_to_asteroid = min(valid_points_to_move_empty, key= lambda p: p.distance_to(closest_asteroid))
        return closest_point_to_asteroid   

    def clousest_route_to_point(self, context:BotContext, destination_point: Position):
        spaceships_points = self.spaceships_in_radar(context)
        valid_points_to_move = self.valid_points_to_move_in_map(context)
        valid_points_to_move_empty = [point for point in valid_points_to_move if point not in spaceships_points]
        # check closest homebase point 
        closest_point_to_destination = min(valid_points_to_move_empty, key= lambda p: p.distance_to(destination_point))
        return closest_point_to_destination

    def closest_point_to_return_base(self, context:BotContext) -> Position:
        ''''Retorna el o los puntos del radas que nos dejen más cerca de la base'''
        # check points available
        asteroids_and_spaceships_points = [point for point, thing in context.radar_contacts.items() if thing in (ASTEROID, SPACESHIP)]
        valid_points_to_move = self.valid_points_to_move_in_map(context)
        valid_points_to_move_empty = [point for point in valid_points_to_move if point not in asteroids_and_spaceships_points]
        # check closest homebase point
        closest_homebase_point = min(self.HOME_BASE_POSITIONS, key= lambda p: p.distance_to(context.position)) 
        closest_point_to_return_home = min(valid_points_to_move_empty, key= lambda p: p.distance_to(closest_homebase_point))
        return closest_point_to_return_home

    def fill_map(self, context:BotContext) -> None:
        '''Completa el mapa con el radar actual'''
        for position, thing in context.radar_contacts.items():
            self.map[position] = (context.turn_number, thing)
        

    def turn(self, turn_number, hp, ship_number, cargo, position, power_distribution, radar_contacts, leader_board):
        """
        Here you write the logic of your bot.
        On each turn the game will call this function of your bot, giving you all the info about
        your current status in the game, and your bot should return what it wants to do during this
        turn.
        If your bot returns an action, the game will try to run that action (might be ignored if
        you ask for something impossible!). If your bot returns None, then it does nothing on this
        turn.
        """
        self.visited_points.append(position)

        desired_distribution = {ENGINES: 3, SHIELDS: 0, LASERS: 0}
        if power_distribution != desired_distribution:
            return POWER_TO, desired_distribution
        
        moves = power_distribution['engines'] - cargo

        context = BotContext(
            turn_number,
            hp,
            ship_number,
            cargo,
            position,
            power_distribution,
            radar_contacts, 
            leader_board,
            moves
            )
        
        self.fill_map(context)
        self.map[position] = (turn_number, None)
        
        if cargo:
            return FLY_TO, self.closest_point_to_return_base(context)
        
        if self.asteroids_in_radar(context):
            return FLY_TO, self.closest_asteroid_at_range(context)
        
        known_asteroid = self.asteroids_in_map(context)

        if known_asteroid:
            return FLY_TO, self.closest_point_to_closest_asteroid(context)
        
        for destination in self.reference_points:
            if destination not in self.visited_points:
                return FLY_TO, random.choice(self.valid_point_to_explore(context))
        

