from random import normalvariate as normal
from statistics import PlayerStatistics, UmpireStatistics


class Career(object):
    """A baseball career."""

    def __init__(self):
        """Initialize a Career object."""
        self.retired = False
        self.seasons = []  # Appended to by season object's __init__()


class PlayerCareer(Career):
    """A person's baseball playing career."""

    def __init__(self, player):
        """Initialize a PlayerCareer object."""
        super(PlayerCareer, self).__init__()
        self.player = player  # The player to whom this career pertains
        self.team = None
        self.statistics = PlayerStatistics(player=player)
        self.planning_to_retire = False  # Modified during a PitchInterim potentially

    @property
    def debut(self):
        """Return this player's debut game."""
        try:
            return self.statistics.games_played[0]
        except IndexError:
            return None

    @property
    def finale(self):
        """Return this player's final game."""
        try:
            return self.statistics.games_played[-1] if self.retired else None
        except IndexError:
            return None

    def potentially_retire(self):
        """Consider retirement."""
        if not self.retired and self.planning_to_retire:
            self.retire()

    def consider_retirement(self):
        """Consider retirement."""
        if self.player.person.age > 36 and len(self.statistics.games_played) > 100:
            self.planning_to_retire = True

    def retire(self):
        """Retire from professional baseball."""
        self.planning_to_retire = False
        self.retired = True
        self.team.process_a_retirement(player=self.player)


class ManagerCareer(Career):
    """A person's baseball managerial career."""

    def __init__(self, manager):
        """Initialize a ManagerCareer object."""
        super(ManagerCareer, self).__init__()
        self.team = None
        self.manager = manager  # The manager to whom this career pertains


class OwnerCareer(Career):
    """A person's baseball ownership career."""

    def __init__(self, owner):
        """Initialize a OwnerCareer object."""
        super(OwnerCareer, self).__init__()
        self.owner = owner  # The owner to whom this career pertains
        self.team = None


class AnnouncerCareer(Career):
    """A person's baseball announcing career."""

    def __init__(self, announcer):
        """Initialize a AnnouncerCareer object."""
        super(AnnouncerCareer, self).__init__()
        self.announcer = announcer  # The announcer to whom this career pertains
        self.team = None


class ScoutCareer(Career):
    """A person's baseball scouting career."""

    def __init__(self, scout):
        """Initialize a ScoutCareer object."""
        super(ScoutCareer, self).__init__()
        self.scout = scout  # The scout to whom this career pertains
        self.team = None


class CommissionerCareer(Career):
    """A person's baseball-commissioner career."""

    def __init__(self, commissioner):
        """Initialize a CommissionerCareer object."""
        super(CommissionerCareer, self).__init__()
        self.commissioner = commissioner  # The commissioner to whom this career pertains
        self.league = None


class UmpireCareer(Career):
    """A person's baseball umpiring career."""

    def __init__(self, umpire):
        """Initialize a UmpireCareer object."""
        super(UmpireCareer, self).__init__()
        self.umpire = umpire  # The umpire to whom this career pertains
        self.league = None
        self.statistics = UmpireStatistics(umpire=umpire)