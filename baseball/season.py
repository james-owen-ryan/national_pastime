# coding=utf-8
import os
import random
from game import Game
from schedule import LeagueSchedule
from printout import compose_league_leaders as COMPOSE_LEAGUE_LEADERS
from printout import compose_league_standings as COMPOSE_LEAGUE_STANDINGS


class LeagueSeason(object):
    """An individual season in the history of a baseball league."""

    def __init__(self, league):
        """Initialize a LeagueSeason object."""
        # Set basic attributes
        self.league = league
        league.history.seasons.append(self)
        self.year = league.cosmos.year
        # Prepare award attributes
        self.championship = None
        self.pennants = []
        self.division_titles = []
        # Record name, league offices, and commissioner, since this could change later (i.e.,
        # we can't rely on accessing these attributes of the franchise itself)
        self.league_name = league.name
        self.league_offices = league.offices
        self.commissioner = league.commissioner
        self.umpires = league.umpires
        # Attribute a TeamSeason object for each team, and attribute these objects to this one
        self.teams = []
        for team in league.teams:
            team.season = TeamSeason(team=team)
            self.teams.append(team.season)
        # Devise a league schedule
        self.schedule = LeagueSchedule(league)
        # These may be set by self.review()
        self.standings = None
        self.league_leaders = None

    def __str__(self):
        """Return string representation."""
        return "{year} {league_name} Season".format(
            year=self.year,
            league_name=self.league_name
        )

    def progress(self):

        while any(team for team in self.league.teams if team.wins+team.losses < 152):
            random.shuffle(self.league.teams)
            home_team = next(team for team in self.league.teams if team.wins+team.losses < 152)
            away_team = min([o for o in self.league.teams if o is not home_team],
                            key=lambda t: home_team.times_played[t])
            game = Game(ballpark=home_team.city.ballpark, league=self.league, home_team=home_team,
                        away_team=away_team, rules=self.league.rules, radio=False, trace=False)
            self.league.error_game = game
            game.transpire()
            home_team.times_played[away_team] += 1
            away_team.times_played[home_team] += 1
        for team in self.league.teams:
            self.records[team] = [team.wins, team.losses]
        self.championship = self.determine_champ()
        self.championship.pennants.append(self.year)

    def determine_champ(self):

        champion = max(self.teams, key=lambda team: team.wins)

        if any(team for team in self.teams if team is not champion and team.wins == champion.wins):
            print "\n--\tTIEBREAKER GAME TO DETERMINE WORLD'S CHAMPIONS\t--"
            other_champion = next(team for team in self.teams if team is not champion and
                                  team.wins == champion.wins)
            if random.random() > 0.5:
                home_team, away_team = champion, other_champion
            else:
                home_team, away_team = other_champion, champion
            tiebreaker = Game(ballpark=home_team.city.ballpark, league=self.league, home_team=home_team,
                              away_team=away_team, rules=self.league.rules, radio=False)
            tiebreaker.transpire()
            champion = tiebreaker.winner

        os.system('say and the champions of the {} {} season are the {} and {} {}'.format(
            self.league.country.year, self.league.name, champion.wins, champion.losses, champion.name
        ))

        return champion

    def review(self):
        """Review this season to effect outcomes and record statistics."""
        self.standings = COMPOSE_LEAGUE_STANDINGS(season=self)
        self.league_leaders = COMPOSE_LEAGUE_LEADERS(season=self)


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
        return "{year} {city} {nickname} Season ({wins}-{losses}{championship}{pennant}{division}{wild_card}".format(
            year=self.year,
            city=self.city.name,
            nickname=self.nickname,
            wins=self.wins,
            losses=self.losses,
            championship='†' if self.championship else '',
            pennant='*' if self.pennant else '',
            division='^' if self.division_title else '',
            wild_card='¤' if self.wild_card_berth else ''
        )

    @property
    def wins(self):
        """Return the number of wins this team has/had this season."""
        return len([g for g in self.games if g.winner is self.team])

    @property
    def losses(self):
        """Return the number of losses this team has/had this season."""
        return len([g for g in self.games if g.winner is not self.team])

    @property
    def winning_percentage(self):
        """Return the team's winning percentage this season."""
        return float(self.wins)/(self.wins+self.losses)

    @property
    def record(self):
        """Return this team's record."""
        return "{wins}-{losses}".format(wins=self.wins, losses=self.losses)


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