# coding=utf-8
import os
import random
from game import Game
from schedule import LeagueSchedule
from award import Pennant
from printout import compose_league_leaders as COMPOSE_LEAGUE_LEADERS
from printout import compose_league_standings as COMPOSE_LEAGUE_STANDINGS


class LeagueSeason(object):
    """An individual season in the history of a baseball league."""

    def __init__(self, league):
        """Initialize a LeagueSeason object."""
        # Set basic attributes
        self.league = league
        league.season = self
        league.history.seasons.append(self)
        self.year = league.cosmos.year
        # Record name, league offices, and commissioner, since this could change later (i.e.,
        # we can't rely on accessing these attributes of the franchise itself)
        self.league_name = league.name
        self.league_offices = league.offices
        self.commissioner = league.commissioner
        self.umpires = league.umpires
        # These may be set by self.review()
        self.champion = None
        self.standings = None
        self.league_leaders = None
        # Prepare award attributes
        self.championship_trophy = None
        self.pennants = []
        self.division_titles = []
        # Attribute a TeamSeason object for each team, and attribute these objects to this one
        self.teams = []
        for team in league.teams:
            team.season = TeamSeason(team=team)
            self.teams.append(team.season)
        # Devise a league schedule
        self.schedule = LeagueSchedule(league)

    def __str__(self):
        """Return string representation."""
        return "{year} {league_name} Season".format(
            year=self.year,
            league_name=self.league_name
        )

    def review(self):
        """Review this season to effect outcomes and record statistics."""
        # Compile standings
        self.standings = COMPOSE_LEAGUE_STANDINGS(season=self)
        # Name a champion
        self.champion = self._name_champion()
        self.league.history.champions_timeline[self.year] = self.champion
        print "THE {} HAVE WON THE {} {} CHAMPIONSHIP!".format(
            self.champion.team.name.upper(), self.year, self.league.name.upper()
        )
        # Compile league leaders
        # self.league_leaders = COMPOSE_LEAGUE_LEADERS(season=self)
        # Have each team review its season, as well
        for team_season in self.teams:
            team_season.review()
        # Send the league into the offseason
        self.league.season = None

    def _name_champion(self):
        """Name the league champion for this season."""
        # TODO BREAK TIES
        return max(self.teams, key=lambda team: len(team.wins))

    def terminate(self):
        """Terminate this season after its conclusion; this will prompt the offseason."""
        self.league.season = None
        for team in self.teams:
            team.team.season = None


class TeamSeason(object):
    """An individual season in the history of a baseball franchise."""

    def __init__(self, team):
        """Initialize a TeamSeason object."""
        # Set basic attributes
        self.team = team
        team.season = self
        team.history.seasons.append(self)
        self.league = team.league
        self.year = team.cosmos.year
        # Record city, nickname, and organization, since this could change later (i.e.,
        # we can't rely on accessing these attributes of the franchise itself)
        self.city = team.city
        self.nickname = team.nickname
        self.organization = team.organization
        self.owner = team.owner
        self.manager = team.manager
        self.scout = team.scout
        self.players = team.players
        # Prepare attributes
        self.games = []
        # Prepare award attributes
        self.championship = None
        self.pennant = None
        self.division_title = None
        self.wild_card_berth = None

    def __str__(self):
        """Return string representation."""
        return "{year} {city} {nickname} Season ({record}){championship}{pennant}{division}{wild_card}".format(
            year=self.year,
            city=self.city.name,
            nickname=self.nickname,
            record=self.record,
            championship='†' if self.championship else '',
            pennant='*' if self.pennant else '',
            division='^' if self.division_title else '',
            wild_card='¤' if self.wild_card_berth else ''
        )

    @property
    def wins(self):
        """Return the games this team won this season."""
        return [g for g in self.games if g.winner is self.team]

    @property
    def losses(self):
        """Return the games this team lost this season."""
        return [g for g in self.games if g.winner is not self.team]

    @property
    def record(self):
        """Return this team's record."""
        return "{wins}-{losses}".format(wins=len(self.wins), losses=len(self.losses))

    @property
    def winning_percentage(self):
        """Return the team's winning percentage this season."""
        return float(len(self.wins))/len((self.wins+self.losses))

    def review(self):
        """Review this season to effect outcomes and record statistics."""
        for player in self.team.players:
            player.career.potentially_retire()


class PlayerSeason(object):
    """An individual season in the career of a baseball player."""

    def __init__(self, player):
        """Initialize a PlayerSeason object."""
        self.player = player
        player.career.seasons.append(self)
        self.team = player.team
        self.league = self.team.league
        self.year = self.team.cosmos.year


class ManagerSeason(object):
    """An individual season in the career of a baseball manager."""

    def __init__(self, manager):
        """Initialize a PlayerSeason object."""
        self.player = manager
        manager.career.seasons.append(self)
        self.team = manager.team
        self.league = self.team.league
        self.year = self.team.cosmos.year