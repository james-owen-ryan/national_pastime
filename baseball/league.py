import random
import math
from random import normalvariate as normal
from people.business import BaseballLeagueOffices
from people.occupation import BaseballCommissioner, BaseballUmpire
from history import LeagueHistory
from franchise import Team
from season import LeagueSeason
from commissioner import Commissioner
from umpire import Umpire
from game import Game

# TODO  Make league activity bottom-up once the postal system is implemented -- I'm
# TODO  thinking something like the commissioner sending a letter to city
# TODO  hall in a prospective city and the mayor then forwards the letter
# TODO  to magnates (or other esteemed individuals) in town (when asking to join
# TODO  the league as charter member/expansion franchise)


class League(object):
    """A baseball league in a baseball cosmos."""
    
    def __init__(self, headquarters, league_classification):
        """Initialize a League object."""
        # Attribute geographic attributes
        self.headquarters = headquarters  # City in which the league is based
        self.state = headquarters.state
        self.country = headquarters.country
        self.cosmos = headquarters.cosmos
        # Determine official league playing rules
        self.classification = league_classification  # Level-of-play classification; this is where the rules live
        # Update city, state, country, and cosmos leagues listings
        self.headquarters.leagues.append(self)
        self.state.leagues.append(self)
        self.country.leagues.append(self)
        self.cosmos.leagues.append(self)
        # Attribute founding date
        self.founded = self.cosmos.year
        self.ceased = None
        # This gets set by self.league_offices.__init__()
        self.name = None
        # Form corresponding league offices, which will be a Business object that
        # handles business and other considerations
        self.offices = BaseballLeagueOffices(league=self)
        # Prepare attributes that hold team personnel
        self.commissioner = None
        self.umpires = set()
        self.set_league_personnel()
        # Team attributes will be populated as new teams form
        self.teams = set()  # Appended by Team.__init__()
        # These only hold the current champion and current season
        self.season = None  # Modified by LeagueSeason.__init__() and LeagueSeason.terminate()
        # This is used to hold all the games that need to be played today, because it
        # is the league object's responsibility to instantiate the actual Game object
        self.games_scheduled_for_today = set()
        # Enfranchise a group of charter teams
        self._init_enfranchise_charter_teams()
        # Instantiate history object; do this after enfranchising charter teams so that
        # LeagueHistory.charter_teams() can be inferred in that object's __init__ call
        self.history = LeagueHistory(league=self)
        # Determine the date that a new season will be planned for each year
        self.date_to_plan_next_season = self.cosmos.config.date_for_league_to_plan_next_season  # (month_n, day_n)
        print (
            "\n\nA new baseball major league has been formed in {hq}! It's been christened the "
            "{league}, and features the following charter teams: {all_but_last}, and {last}.".format(
                hq=self.headquarters.name,
                league=self.name,
                all_but_last=', '.join(team.name for team in list(self.teams)[:-1]),
                last=list(self.teams)[-1].name
            )
        )

    def __str__(self):
        """Return string representation."""
        return self.name

    @property
    def cities(self):
        """Return all the cities that have a team in this league."""
        return {team.city for team in self.teams}

    @property
    def players(self):
        """Return all the players that are currently playing in this league."""
        players = []
        for team in self.teams:
            players += team.players
        return players

    @property
    def random_team(self):
        """Return a random team in this league."""
        return random.choice(list(self.teams))

    @property
    def random_player(self):
        """Return a random player on this team."""
        return random.choice(list(self.players))

    @property
    def champion(self):
        """Return the franchise that holds the most recent championship in this league."""
        try:
            year_of_most_recent_championship = max(self.history.champions_timeline.keys())
            return self.history.champions_timeline[year_of_most_recent_championship]
        except IndexError:
            return None

    def _init_enfranchise_charter_teams(self):
        """Enfranchise a set of charter teams."""
        config = self.cosmos.config
        # First, establish a team in the city the league is based in
        Team(city=self.headquarters, league=self)
        # Evaluate prospective cities in which charter teams might be based
        cities_ranked_by_utility = self.rank_prospective_cities()
        # Invite cities to join the league until you have eight that have accepted
        number_of_charter_teams_desired = config.number_of_charter_teams_for_a_league(year=self.cosmos.year)
        for prospective_city in cities_ranked_by_utility:
            if prospective_city is not self.headquarters:
                if random.random() < config.chance_a_city_accepts_offer_to_join_league(city=prospective_city):
                    # Instantiate a baseball team, which will be appended to this league's .teams
                    # attribute (and will cause a BaseballOrganization object to be instantiated)
                    Team(city=prospective_city, league=self)
            # If we now have the desired number of charter teams, stop inviting cities to join
            if len(self.teams) == number_of_charter_teams_desired:
                break

    def rank_prospective_cities(self):
        """Evaluate prospective cities for their utility to this league as a team base."""
        config = self.cosmos.config
        city_evaluations = {}
        for prospective_city in self.country.cities:
            # Calculate a base score for all cities in the cosmos
            city_evaluations[prospective_city] = config.city_utility_to_a_league(city=prospective_city)
            # If air travel is not yet prominent, penalize cities for their distance from
            # league headquarters
            if self.cosmos.year < self.cosmos.config.year_air_travel_becomes_prominent:
                distance_between_this_city_and_league_headquarters = self.headquarters.distance_to(prospective_city)
                if distance_between_this_city_and_league_headquarters > 1:
                    city_evaluations[prospective_city] /= distance_between_this_city_and_league_headquarters
            # Also penalize the city if is already has a team (or multiple teams) in this league
            if prospective_city in self.cities:
                number_of_teams_in_this_city = len([t for t in self.teams if t.city is prospective_city])
                for _ in xrange(number_of_teams_in_this_city):
                    city_evaluations[prospective_city] *= config.city_utility_penalty_for_already_being_in_league
        cities_ranked_by_utility = sorted(city_evaluations, key=lambda city: city_evaluations[city], reverse=True)
        return cities_ranked_by_utility

    def set_league_personnel(self):
        """Set the personnel working for this team.

        In this method, we set attributes pertaining to the actual baseball-class objects
        corresponding to the employees of this organization. This method may be called any
        time an employee in the organization quits, retires, is fired, or dies.
        """
        # Set commissioner
        commissioner_person = next(e for e in self.offices.employees if isinstance(e, BaseballCommissioner)).person
        self.commissioner = (
            Commissioner(person=commissioner_person) if not commissioner_person.commissioner else
            commissioner_person.commissioner
        )
        # Set umpires
        umpire_people = [e.person for e in self.offices.employees if isinstance(e, BaseballUmpire)]
        self.umpires = {
            Umpire(person=ump_person) if not ump_person.umpire else ump_person.umpire for ump_person in umpire_people
        }

    def conduct_offseason_activity(self):
        """Conduct this league's offseason procedures."""
        # Have each team in the league conduct its offseason procedures; because teams could
        # fold during this procedure, which could change the size of 'self.teams', we need
        # to copy the list before iterating
        for team in list(self.teams):
            team.conduct_offseason_activity()
        if self.history.seasons:
            # Potentially expand this league
            self._potentially_expand()
            if len(self.teams) % 2:
                # If you have an odd number of teams, force a team to fold  TODO WTF? BETTER
                worst_team = min(
                    (t for t in self.teams if t.history.seasons),
                    key=lambda t: t.history.cumulative_winning_percentage
                )
                worst_team._fold()

    def _potentially_expand(self):
        """Potentially expand this league by enfranchising additional teams.

        Note: Rather than the conventional notion of expansion, more frequently expansion will occur
        in fledgling leagues as a way of replacing teams that have folded.
        """
        config = self.cosmos.config
        if self._decide_to_expand():
            # Determine how many teams to expand by
            targeted_number_of_expansion_teams = self._determine_how_many_expansion_teams_to_target()
            # Evaluate prospective cities in which expansion teams might be based
            cities_ranked_by_utility = self.rank_prospective_cities()
            # Invite cities to host an expansion team until you've reached the targeted number
            n_teams_already_added = 0
            for prospective_city in cities_ranked_by_utility:
                if prospective_city is not self.headquarters:
                    if random.random() < config.chance_a_city_accepts_offer_to_join_league(city=prospective_city):
                        # Instantiate a baseball team, which will be appended to this league's .teams
                        # attribute (and will cause a BaseballOrganization object to be instantiated)
                        Team(city=prospective_city, league=self)
                        n_teams_already_added += 1
                # If we now have the desired number of charter teams, stop inviting cities to join
                if n_teams_already_added == targeted_number_of_expansion_teams:
                    break

    def _decide_to_expand(self):
        """Decide whether to attempt to expand this league."""
        config = self.cosmos.config
        if len(self.teams) < 6:  # TODO HAVE LEAGUES GO UNDER
            return True
        max_number_of_teams_for_a_league_this_year = config.max_number_of_teams_to_expand_to(year=self.cosmos.year)
        max_number_of_teams_that_could_be_accommodated = max_number_of_teams_for_a_league_this_year - len(self.teams)
        if max_number_of_teams_that_could_be_accommodated >= 2:
            if random.random() < config.chance_a_league_with_room_to_expand_does_expand_some_offseason:
                return True
        return False

    def _determine_how_many_expansion_teams_to_target(self):
        """Return the number of expansion teams this league will target."""
        config = self.cosmos.config
        # Determine how many teams *could* be accommodated in this league at this time
        max_number_of_teams_for_a_league_this_year = config.max_number_of_teams_to_expand_to(year=self.cosmos.year)
        max_number_of_teams_that_could_be_accommodated = max_number_of_teams_for_a_league_this_year - len(self.teams)
        # Our options, then, are all even numbers in the inclusive range between 2 and the
        # max number of teams that the league could viably accommodate
        options = list(xrange(2, max_number_of_teams_that_could_be_accommodated+1, 2))
        # If the only option is two teams, roll with that
        if len(options) == 1:
            assert options[0] == 2, "A league is attempting to expand by {} teams.".format(options[0])
            return 2
        # Reverse this list, and then iterate over it in that order, making a selection from
        # it with greater probability as you approach n=2 (which will be the default pick if
        # no larger n is targeted)
        options.reverse()
        for n in options[:-1]:
            if config.decide_to_target_an_expansion_number(n=n):
                return n
        # If you got through all of those values without returning an n, then it's time to
        # just go with the default number of 2
        assert options[-1] == 2, "A league is attempting to expand by {} teams.".format(options[0])
        return 2

    def assign_umpire(self):
        """Assign an umpire to a game."""
        return random.choice(list(self.umpires))

    def add_to_game_queue(self, series):
        """Add a game to the queue of games that are scheduled to be played today."""
        self.games_scheduled_for_today.add(series)

    def operate(self):
        """Conduct the regular operations of this league."""
        # Have teams conduct regular operations
        for team in self.teams:
            team.operate()  # This will populate self.games_scheduled_for_today (if season underway)
        # Check for special dates
        if not self.season:  # Off-season
            self._operate_during_offseason()
        elif self.season:
            self._operate_during_season()

    def _operate_during_offseason(self):
        """Conduct the regular offseason operations of this league."""
        if (self.cosmos.month, self.cosmos.day) == self.date_to_plan_next_season:
            self.conduct_offseason_activity()
            LeagueSeason(league=self)

    def _operate_during_season(self):
        """Conduct the regular in-season operations of this league."""
        if self.cosmos.ordinal_date == self.season.schedule.regular_season_terminus:
            self.season.review()  # Will kick into offseason mode by setting League.season to None
        # Instantiate Game objects, which will cause the games to transpire
        while self.games_scheduled_for_today:
            series = self.games_scheduled_for_today.pop()
            # Because of doubleheaders, this series may have multiple games that
            # need to be played today
            while (
                    series.dates_scheduled and
                    series.dates_scheduled[0] == (self.cosmos.ordinal_date, self.cosmos.time_of_day)
            ):
                Game(series=series)

    def process_a_retirement(self, player):
        """Handle the retirement of a player."""
        # TODO DETERMINE CEREMONIES, ETC., IF EXCEPTIONAL CAREER
        self.history.former_players.add(player)