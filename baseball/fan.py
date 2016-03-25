class Fan(object):
    """The baseball-fan layer of a person's being."""

    def __init__(self, person):
        """Initialize a Fan object."""
        self.person = person  # The person in whom this fan layer embeds
        self.games_attended = []

    def attend_game(self, game):
        """Attend a baseball game."""
        # Update attributes
        self.games_attended.append(game)
        game.audience.append(self)
        # Actually go there

    def heckle(self, player):
        """Heckle a player, thus affecting the player's internal state."""
        # TODO
        pass