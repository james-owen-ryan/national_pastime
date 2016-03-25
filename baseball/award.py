# Remember how OOTP does this when you're thinking about it; key is
# to allow leagues to name the individual awards (e.g., after players),
# because that would rule


class TeamAward(object):
    """An award given to a team."""

    def __init__(self, team):
        """Initialize a TeamAward object."""
        self.team = team
        self.league = team.league
        self.year = team.cosmos.year


class IndividualAward(object):
    """An award given to an individual."""

    def __init__(self, team):
        """Initialize a TeamAward object."""
        self.team = team
        self.league = team.league
        self.year = team.cosmos.year


class Pennant(TeamAward):
    """A league pennant awarded to the league's best team."""

    def __init__(self, team):
        """Initialize a Pennant object."""
        super(Pennant, self).__init__(team)
        self.team.season.pennant = self