from rules import Rules


class Class(object):
    """A classification of the level of play in a baseball league."""

    def __init__(self, cosmos, level):
        """Initialize a Class object."""
        self.cosmos = cosmos
        self.level = level  # E.g., 'AA'
        self.roster_limit = cosmos.config.temp_roster_limit
        self.rules = Rules()


class InformalPlay(object):
    """An anti-classification that characterizes informal, pick-up baseball play."""

    def __init__(self, cosmos):
        """Initialize an InformalPlay object."""
        self.cosmos = cosmos