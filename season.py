from game import Game
import random
import os


class Season(object):

    def __init__(self, league):

        self.league = league
        league.current_season = self
        league.seasons.append(self)
        self.year = league.country.year
        self.teams = league.teams
        self.records = {}
        self.champion = None

        for t in self.teams:
            t.wins = 0
            t.losses = 0
            t.record = '0-0'

        for team in league.teams:
            for player in team.players:
                player.teams_timeline[self.league.country.year] = team

        for team in self.league.teams:
            team.times_played = {}
            for other_team in self.league.teams:
                if team is not other_team:
                    team.times_played[other_team] = 0

        self.sim_season()


    def __str__(self):

        rep = str(self.year) + ' ' + self.league.name + ' season'
        return rep

    def sim_season(self):

        while any(team for team in self.league.teams if team.wins+team.losses < 152):
            random.shuffle(self.league.teams)
            home_team = next(team for team in self.league.teams if team.wins+team.losses < 152)
            away_team = min([o for o in self.league.teams if o is not home_team],
                            key=lambda t: home_team.times_played[t])
            game = Game(ballpark=home_team.city.ballpark, league=self.league, home_team=home_team,
                        away_team=away_team, rules=self.league.rules, radio=False, trace=True)
            self.league.error_game = game
            game.enact()
            home_team.times_played[away_team] += 1
            away_team.times_played[home_team] += 1
        for team in self.league.teams:
            self.records[team] = [team.wins, team.losses]
        self.champion = self.determine_champ()
        self.champion.pennants.append(self.year)

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
            tiebreaker.enact()
            champion = tiebreaker.winner

        os.system('say and the champions of the {} {} season are the {} and {} {}'.format(
            self.league.country.year, self.league.name, champion.wins, champion.losses, champion.name
        ))

        return champion