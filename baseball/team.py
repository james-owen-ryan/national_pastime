import os
import random
import heapq
from random import normalvariate as normal
from corpora import Names
from people.event import BaseballFranchiseTermination
from people.business import BaseballOrganization, RelocatedBaseballOrganization
from people.occupation import BaseballTeamOwner, BaseballManager, BaseballScout, BaseballPlayer
from owner import Owner
from manager import Manager
from scout import Scout
from history import FranchiseHistory
from roster import Roster


# TODO  MAKE SCOUTING A DURATIVE ACTIVITY THAT SCOUTS CARRY OUT OVER COURSE OF AN OFF-SEASON
# TODO  BY SCOURING THE COUNTRY FOR YOUNG TALENT


class Team(object):
    """A baseball team in a baseball cosmos."""

    def __init__(self, city, league=None):
        """Initialize a Team object."""
        self.cosmos = city.cosmos
        # Attribute the team's league; if None, this means this is an independent
        # club (or something like that)
        self.league = league
        self.league.teams.add(self)
        # Prepare geographic and organizational attributes, which get set by
        # .establish_base_in_city(), a method that will also be called in the case
        # that this franchise relocates
        self.city = None
        self.state = None
        self.country = None
        self.organization = None
        # This gets set by .establish_base_in_city()
        self.nickname = None
        # Prepare attributes that hold team personnel; these will also be updated by
        # .establish_base_in_city()
        self.personnel = set()
        self.owner = None
        self.manager = None
        self.scout = None
        # Prepare a ballpark attribute, which is set by establish_base_in_city() as well
        self.ballpark = None
        # Finally actually establish operations in the city
        self.establish_base_in_city(city=city)
        # Set various attributes
        self.founded = self.cosmos.year
        self.expansion = True if self.cosmos.year > self.league.founded else False
        self.charter_team = True if not self.expansion else False
        # Set history object
        self.history = FranchiseHistory(franchise=self)
        # Prepare various attributes
        self.season = None  # Gets set by TeamSeason.__init__()
        self.defunct = False
        # Assemble a roster of players
        self.players = set()
        self.roster = None
        self._sign_players()
        self._assemble_roster()
        if self.expansion:
            print '{team} have been enfranchised in the {league}.'.format(team=self.name, league=self.league.name)

    def __str__(self):
        """Return string representation."""
        return self.name

    @property
    def name(self):
        """Return the name of this franchise."""
        return "{city} {nickname}".format(city=self.city.name, nickname=self.nickname)

    def establish_base_in_city(self, city, employees_to_relocate=None):
        """Establish operations in a city, either due to enfranchisement or relocation."""
        # Determine whether this is part of a relocation procedure, which is signaled by
        # employees_to_relocate being passed
        relocating = True if employees_to_relocate else False
        tradition_in_the_old_city = None if not relocating else self.history.tradition
        # Set geographic attributes
        self.city = city
        self.state = city.state
        self.country = city.country
        # Update teams listing of new city
        self.city.teams.add(self)
        # Form a corresponding baseball organization, which will be a Business object that
        # handles business and other considerations
        if not relocating:
            self.organization = BaseballOrganization(team=self)
        else:
            self.organization = RelocatedBaseballOrganization(team=self, employees_to_relocate=employees_to_relocate)
        # Come up with a nickname
        self.nickname = self._determine_nickname(tradition_in_the_old_city=tradition_in_the_old_city)
        # Update the organization's name accordingly
        self.organization.set_name()
        # Set your team personnel
        self.set_team_personnel()
        # Set the team's ballpark, which will have been procured by the organization's
        # __init__() method
        self.ballpark = self.organization.ballpark

    def _determine_nickname(self, tradition_in_the_old_city):
        """Determine a nickname for this team."""
        # If you're relocating, consider retaining the name of the team
        if self._decide_to_retain_nickname(tradition_in_the_old_city=tradition_in_the_old_city):
            return self.nickname
        else:
            return self._come_up_with_nickname()

    def _decide_to_retain_nickname(self, tradition_in_the_old_city):
        """Decide whether to retain the nickname of this relocating franchise."""
        if tradition_in_the_old_city:  # This signals relocation
            chance_we_retain_name = self.cosmos.config.chance_a_relocated_team_retains_name(
                tradition_in_the_old_city=tradition_in_the_old_city
            )
            if random.random() < chance_we_retain_name:
                # Make sure the name is not already taken
                if not any(t for t in self.city.teams if t.nickname == self.nickname):
                    return True
        return False

    def _come_up_with_nickname(self):
        """Come up with a nickname for this team."""
        # TODO CITY APT NICKNAMES AND NAMES OF HISTORICAL TEAMS IN THE CITY
        name_already_taken = True
        nickname = None
        while name_already_taken:
            nickname = Names.a_baseball_team_nickname(year=self.city.cosmos.year)
            # Make sure the name is not already taken
            if not any(t for t in self.city.teams if t.nickname == nickname):
                name_already_taken = False
            else:  # TODO fix this duct tape here
                return "Generics"
        return nickname

    def set_team_personnel(self):
        """Set the personnel working for this team.

        In this method, we set attributes pertaining to the actual baseball-class objects
        corresponding to the employees of this organization. This method may be called any
        time an employee in the organization quits, retires, is fired, or dies.
        """
        # Set team owner
        owner_person = next(e for e in self.organization.employees if isinstance(e, BaseballTeamOwner)).person
        self.owner = Owner(person=owner_person) if not owner_person.team_owner else owner_person.team_owner
        # Set manager
        manager_person = next(e for e in self.organization.employees if isinstance(e, BaseballManager)).person
        self.manager = (
            Manager(person=manager_person, team=self) if not manager_person.manager else manager_person.manager
        )
        # Set scout
        scout_person = next(e for e in self.organization.employees if isinstance(e, BaseballScout)).person
        self.scout = Scout(person=scout_person, team=self) if not scout_person.scout else scout_person.scout
        # Set personnel attribute
        self.personnel = {self.owner, self.manager, self.scout}

    def _sign_players(self):
        """Sign players until you have a full roster."""
        print "\t{scout} is signing players...".format(scout=self.scout.person.name)
        roster_limit = self.league.classification.roster_limit
        while len(self.players) < roster_limit:
            position_of_need = self.manager.decide_position_of_greatest_need()
            secured_player = self.scout.secure_a_player(position=position_of_need)
            self._sign_player(player=secured_player, position=position_of_need)

    def _sign_player(self, player, position):
        """Sign the given player to play at the given position."""
        print "\t\tsigning {}...".format(player.person.name)
        player.career.team = self
        player.position = position
        self.players.add(player)
        # Actually hire the player as an employee in the organization
        self.organization.hire(occupation_of_need=BaseballPlayer, shift="special", selected_candidate=player.person)

    def _assemble_roster(self):
        """Assemble a roster for this team."""
        # Prepare some variables that we'll need
        roster_order = ('P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF')
        lineup = []
        available_players = list(self.players)
        # Assemble starters
        for position_to_slot in roster_order:
            available_players_at_that_position = [p for p in available_players if p.position == position_to_slot]
            best_available_at_that_position = max(
                available_players_at_that_position,
                key=lambda player: self.scout.grade(prospect=player, position=position_to_slot)
            )
            lineup.append(best_available_at_that_position)
            available_players.remove(best_available_at_that_position)
        # Assemble bullpen and bench
        bullpen = []
        bench = []
        for bench_player in available_players:
            if bench_player.position == 'P':
                bullpen.append(bench_player)
            else:
                bench.append(bench_player)
        # Instantiate and set a Roster object
        self.roster = Roster(lineup=tuple(lineup), bullpen=tuple(bullpen), bench=tuple(bench))

    def handle_retirement(self, player):
        """Handle the retirement of a player."""
        self.players.remove(player)

    def conduct_offseason_activity(self):
        """Conduct this team's offseason procedures."""
        config = self.cosmos.config
        # If you're a fairly established team in a very established league, consider relocating;
        # newer teams won't consider relocating, since they're still establishing a fan base in
        # their current cities; teams in leagues that aren't established don't relocate because
        # they would have no more value to another city than an expansion team would
        team_is_established_in_town = (
            self.history.number_of_years_in_town >
            config.minimum_number_of_years_in_city_before_considering_relocation(year=self.cosmos.year)
        )
        league_is_established_enough_for_relocation = (
            self.league.history.years_in_existence >
            config.minimum_number_of_years_before_league_established_enough_for_team_relocation()
        )
        if team_is_established_in_town and league_is_established_enough_for_relocation:
            self._potentially_relocate()
        # Otherwise, if you aren't a brand new team and the league isn't established yet,
        # then consider folding
        elif self.history.seasons and not league_is_established_enough_for_relocation:
            self._potentially_fold()

    def _potentially_fold(self):
        """Potentially _fold this franchise."""
        chance_of_folding = self.cosmos.config.chance_of_folding(
            franchise_winning_percentage=self.history.cumulative_winning_percentage,
            league_years_in_existence=self.league.history.years_in_existence
        )
        if random.random() < chance_of_folding:
            self._fold()

    def _fold(self):
        """Cease operations of this franchise."""
        # Have the organization go out of business, which will officially terminate
        # all of the organization's employee occupations -- have to do this first so
        # that the BaseballFranchiseTermination object gets all the attributes it needs
        self.organization.go_out_of_business(reason=BaseballFranchiseTermination(franchise=self))
        # Sever ties with the city you're located in
        self._sever_ties_with_city()
        # Sever ties with the league you're in
        self._sever_ties_with_league()
        # Sever ties with players and personnel
        self._sever_ties_with_players_and_personnel()
        # Update attributes
        self.defunct = True

    def _sever_ties_with_city(self):
        """Sever ties with the city you were located in."""
        self.city.teams.remove(self)
        self.city.former_teams.add(self)

    def _sever_ties_with_league(self):
        """Sever ties with the league you were a member of."""
        self.league.teams.remove(self)
        self.league.history.defunct_teams.add(self)

    def _sever_ties_with_players_and_personnel(self):
        """Sever ties with your players and personnel."""
        for stakeholder in self.players | self.personnel:
            stakeholder.career.team = None

    def _potentially_relocate(self):
        """Potentially _relocate this franchise to a new city."""
        config = self.cosmos.config
        if self._qualified_to_relocate():
            if random.random() < config.chance_a_team_that_qualifies_to_relocate_will_relocate:
                self._relocate()

    def _qualified_to_relocate(self):
        """Return whether this franchise is qualified to relocate."""
        config = self.cosmos.config
        # If your last season was a losing season...
        last_season_was_a_losing_season = self.history.seasons[-1].winning_percentage < 0.5
        if not last_season_was_a_losing_season:
            return False
        # ...and your franchise isn't too storied to ever relocate...
        franchise_is_too_storied_to_relocate = config.franchise_too_storied_to_relocate(
            tradition=self.history.tradition
        )
        if franchise_is_too_storied_to_relocate:
            return False
        # ...and you've averaged a losing season over the duration of your fan base's memory...
        fan_base_memory_window = int(config.fan_base_memory_window())
        beginning_of_that_window = self.cosmos.year-fan_base_memory_window
        winning_percentage_during_fan_base_memory = self.history.winning_percentage_during_window(
            start_year=beginning_of_that_window, end_year=self.cosmos.year, city=self.city
        )
        averaged_losing_season_during_fan_base_memory = winning_percentage_during_fan_base_memory < 0.5
        if not averaged_losing_season_during_fan_base_memory:
            return False
        # ..then you are qualified to relocate
        return True

    def _relocate(self):
        """Relocate this franchise to a new city."""
        # TODO EMBITTER FANS IN THIS CITY
        # Sever ties with the city you are departing
        self._sever_ties_with_city()
        # Decide where to relocate to
        city_to_relocate_to = self._decide_where_to_relocate_to()
        # Shut down the current organization, but save all its employees so
        # that we can offer them the chance to relocate to the new organization
        employees_to_relocate = set(self.organization.employees)
        # Set up operations in the new city
        self.establish_base_in_city(city=city_to_relocate_to, employees_to_relocate=employees_to_relocate)
        print "The {old_name} of the {league} have relocated to become the {new_name}".format(
            # old_name="{} {}".format(self.history.seasons[-1].city.name, self.history.seasons[-1].nickname),
            old_name='LOL HI!',
            league=self.league.name,
            new_name=self.name
        )

    def _decide_where_to_relocate_to(self):
        """Decide which city to relocate this franchise to."""
        cities_ranked_by_utility = self.league.rank_prospective_cities()
        cities_ranked_by_utility.remove(self.city)  # Throw out the city we're leaving
        # If the hometown of the owner of this franchise is a viable city to relocate
        # to, then select that city
        if self.owner.person.hometown in cities_ranked_by_utility:
            return self.owner.person.hometown
        most_appealing_city = cities_ranked_by_utility[0]
        return most_appealing_city

    def operate(self):
        """Carry out the day-to-day operations of this franchise."""
        # TODO MAKE TRAVEL REALISTIC ONCE TRAVEL SYSTEM IMPLEMENTED
        # If it's game day, go to the ballpark and schedule the game with
        # the league, who will instantiate the Game object
        try:
            next_scheduled_game = self.season.schedule.next_game
            date_of_next_game, timestep_of_next_game, away_team_of_next_game, home_team_of_next_game = (
                next_scheduled_game
            )
            ballpark_of_next_game = home_team_of_next_game.ballpark
            if date_of_next_game == self.cosmos.ordinal_date and timestep_of_next_game == self.cosmos.time_of_day:
                for stakeholder in {self.manager, self.scout} | self.players:
                    stakeholder.person.go_to(destination=ballpark_of_next_game, occasion="baseball")
            self.league.add_to_game_queue(away_team_of_next_game, home_team_of_next_game)
        except AttributeError:  # No upcoming games
            pass