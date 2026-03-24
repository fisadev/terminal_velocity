from itertools import combinations
from random import shuffle
from uuid import uuid4


def opponent_coverage(matches, players):
    """
    Measure how much each player will play against the whole roster of opponents.
    1 = the player will play against all other players
    0 = the player will play against none of the other players
    This function returns the min factor for all the players.
    """
    opponents_per_player = {player: set() for player in players}

    for match in matches:
        for player1, player2 in combinations(match, 2):
            opponents_per_player[player1].add(player2)
            opponents_per_player[player2].add(player1)

    coverages = {
        player: len(opponents) / (len(players) - 1)
        for player, opponents in opponents_per_player.items()
    }

    return min(coverages.values())


def build_matches(players, match_size=6, min_opponent_coverage=0.5, max_matches=20):
    """
    Build matches until all players have played the same number of matches and they
    have a decent variety of opponents. The matches are built randomly.
    """
    matches = []

    # simple random sampling approach
    pending_players = players[:]
    shuffle(pending_players)
    while True:
        match = pending_players[:match_size]
        pending_players = pending_players[match_size:]

        if len(match) < match_size:
            # complete it with a new mini batch but without repeating them
            extra_batch_size = match_size - len(match)
            pending_players = [p for p in players if p not in match]
            pending_players_for_afterwards = match[:]

            shuffle(pending_players)
            match.extend(pending_players[:extra_batch_size])
            pending_players = pending_players[extra_batch_size:]

            pending_players.extend(pending_players_for_afterwards)
            shuffle(pending_players)

        matches.append(match)

        if not pending_players:
            if opponent_coverage(matches, players) >= min_opponent_coverage:
                break

            if len(matches) > max_matches:
                raise ValueError("Could not achieve the specified parameters")

    return matches


def test_all_matches_same_player_count():
    matches = build_matches([f"Player {i}" for i in range(15)])

    for match in matches:
        assert len(match) == 6


def test_all_players_same_match_count():
    matches = build_matches([f"Player {i}" for i in range(15)])

    players_match_count = {player: 0 for player in SAMPLE_PLAYERS}

    for match in matches:
        for player in match:
            players_match_count[player] += 1

    match_counts = set(players_match_count.values())
    assert len(match_counts) == 1


def test_all_players_with_decent_coverage_of_opponents():
    acceptable_factor = 0.5
    players = [f"Player {i}" for i in range(15)]

    matches = build_matches(players)

    assert opponent_coverage(matches, players) >= acceptable_factor


def snake_to_short_camel_case(name):
    """
    Transform something_like_this into SomLikThi.
    """
    return "".join(word.capitalize()[:3] for word in name.split("_"))


def build_players_arg(players):
    """
    Convert a dict of player names -> bot types, into the string format for
    the --players argument of the game.
    """
    return ",".join(
        f"{player_name}:{bot_type}"
        for player_name, bot_type in sorted(players.items())
    )


def main():
    bot_types = [
        "doble_efe_miner",  # facu+felu
        "doble_efe_std",  # facu+felu
        "emperors_fury",  # feli
        "strike_cruiser",  # feli
        "mega",  # mega
        "planet_express_fry",  # nadia
        "planet_express_leela",  # nadia
        "sofi_miner",  # sofi
        "sofibot",  # sofi
        "vieja_mula",  # charly
        "mula_luma",  # charly
        #"gandhibot",  # sebis
        "marian",  # marian
        "juani",  # juani
        "santa_claude",  # alexis
        "pacific_queen",  # zoe
        "conserva",  # pancho
    ]

    players = {
        snake_to_short_camel_case(bot_type): bot_type
        for bot_type in bot_types
    }
    assert len(players) == len(bot_types), "Some bot types yield the same player name"

    match_cmd_template = "uv run play.py --players {players_arg} --isolated --ui-turn-delay 0.3 {extra_args}"

    print()
    print("# Official matches")
    print()

    matches = build_matches(list(players.keys()), min_opponent_coverage=0.8)
    for match_n, match_players in enumerate(matches):
        print("Match", match_n + 1, "of", len(matches))
        match_players = {player: players[player] for player in match_players}
        print(match_cmd_template.format(players_arg=build_players_arg(match_players), extra_args=""))
        print()

    print()
    print("# Special events")
    print()

    print("All players together!")
    print(match_cmd_template.format(players_arg=build_players_arg(players), extra_args="--turns 300 --map-radius 25"))
    print()


if __name__ == "__main__":
    main()
