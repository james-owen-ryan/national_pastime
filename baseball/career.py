from statistics import PlayerStatistics, UmpireStatistics


class PlayerCareer(object):
    """A person's baseball playing career."""

    def __init__(self, player):
        """Initialize a PlayerCareer object."""
        self.player = player  # The player to whom this career pertains
        self.team = None
        self.retired = False
        self.teams_timeline = {}
        self.statistics = PlayerStatistics(player=player)


class ManagerCareer(object):
    """A person's baseball managerial career."""

    def __init__(self, manager):
        """Initialize a ManagerCareer object."""
        self.manager = manager  # The manager to whom this career pertains


class OwnerCareer(object):
    """A person's baseball ownership career."""

    def __init__(self, owner):
        """Initialize a OwnerCareer object."""
        self.owner = owner  # The owner to whom this career pertains


class AnnouncerCareer(object):
    """A person's baseball announcing career."""

    def __init__(self, announcer):
        """Initialize a AnnouncerCareer object."""
        self.announcer = announcer  # The announcer to whom this career pertains


class UmpireCareer(object):
    """A person's baseball umpiring career."""

    def __init__(self, umpire):
        """Initialize a UmpireCareer object."""
        self.umpire = umpire  # The umpire to whom this career pertains
        self.statistics = UmpireStatistics(umpire=umpire)