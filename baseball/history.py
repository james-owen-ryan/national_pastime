class LeagueHistory(object):
    """The compiled history of a baseball league."""

    def __init__(self, league):
        """Initialize a LeagueHistory object."""
        self.league = league
        self.defunct_teams = set()  # Populated as teams _fold
        self.charter_teams = set(league.teams)
        self.seasons = []  # Appended to by LeagueSeason.__init__()
        self.champions_timeline = {}  # Maps year to champion that year

    @property
    def years_in_existence(self):
        """Return the number of years this league has existed."""
        return self.league.cosmos.year-self.league.founded


class FranchiseHistory(object):
    """The compiled history of a baseball franchise."""

    def __init__(self, franchise):
        """Initialize a FranchiseHistory object."""
        self.franchise = franchise
        self.seasons = []  # Appended to by TeamSeason.__init__()
        self.championships = []

    @property
    def years_in_existence(self):
        """Return the number of years this franchise has existed."""
        return self.franchise.cosmos.year-self.franchise.founded

    @property
    def tradition(self):
        """The accumulated tradition of this franchise (in its current city)."""
        if not self.seasons:
            return 0
        tradition = self.franchise.cosmos.config.calculate_franchise_tradition(
            n_championships=len(self.championships), n_years_in_town=self.number_of_years_in_town
        )
        return tradition

    @property
    def cumulative_wins(self):
        """Return the cumulative number of wins this franchise has accumulated across its entire history."""
        return sum(s.wins for s in self.seasons)

    @property
    def cumulative_losses(self):
        """Return the cumulative number of losses this franchise has accumulated across its entire history."""
        return sum(s.losses for s in self.seasons)

    @property
    def cumulative_winning_percentage(self):
        """Return this franchise's cumulative winning percentage."""
        return float(self.cumulative_wins)/(self.cumulative_wins+self.cumulative_losses)

    @property
    def number_of_years_in_town(self):
        """Return the number of years this franchise has been located in its current city."""
        if not self.seasons:
            return 0
        else:
            first_season_in_this_town = next(s for s in self.seasons if s.city is self.franchise.city)
            year_of_that_season = first_season_in_this_town.year
            number_of_years_in_town = self.franchise.cosmos.year-year_of_that_season
            return number_of_years_in_town

    def get_season(self, year, city=None):
        """Return this franchise's season for the given year."""
        city = self.franchise.city if not city else city
        try:
            return next(s for s in self.seasons if s.year == year and s.city is city)
        except StopIteration:
            return None

    def winning_percentage_during_window(self, start_year, end_year, city=None):
        """Return this team's cumulative winning percentage across the specified window.

        Note: This method quietly ignores any years in the specified window that are not
        applicable for this franchise (either because the franchise did not exist yet, or
        it was not in the specified city yet).
        """
        city = self.franchise.city if not city else city
        wins_during_the_window = 0
        losses_during_the_window = 0
        for year in xrange(start_year, end_year):
            season_that_year = self.get_season(year=year, city=city)
            if season_that_year:
                wins_during_the_window += season_that_year.wins
                losses_during_the_window += season_that_year.losses
        return float(wins_during_the_window)/(wins_during_the_window+losses_during_the_window)
