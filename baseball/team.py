import os
import random
import heapq
from random import normalvariate as normal

from equipment import Mitt

COLORS = ['Blue', 'Blue', 'Blue', 'Gray', 'Gray', 'Gray', 'Red', 'Red',
          'Red', 'Brown', 'Brown', 'Brown',  'Green', 'Green', 'Orange',
          'Silver', 'Maroon', 'Black', 'Gold', 'Yellow', 'White', 'White',
          'White']
ANIMAL_NAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/animal_names_reg.txt','r')
]
ANIMAL_NAMES_IRREG = [name[:-1] for name in open(
    os.getcwd()+'/corpora/animal_names_irreg.txt','r')
]
GEN_TEAM_NAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/gen_team_names.txt','r')
]


class Team(object):
    """A baseball team in a baseball cosmos."""

    def __init__(self, city, league, expansion=False):
        """Initialize a Team object."""
        self.city = city
        self.state = city.state
        self.country = city.country
        self.cosmos = city.cosmos
        self.league = league

        self.ballpark = self.city.ballpark

        self.founded = self.cosmos.year
        self.folded = False
        self.tradition = 0
        self.charter_team, self.expansion = (True, False) if not expansion else (False, True)

        self.players = []

        self.wins = 0
        self.losses = 0
        self.record = '0-0'
        self.win_diffs = []

        self.pitcher = None
        self.fielders = []

        self.records_timeline = {}
        self.pennants = []
        self.championships = []

        self.cumulative_wins = 0
        self.cumulative_losses = 0

        self.in_city_since = self.cosmos.year

        nickname = self.init_name()
        if nickname in self.cosmos.major_league_team_nicknames:
            self.nickname = "Generics"
        else:
            self.nickname = nickname

        city.teams.append(self)
        league.teams.append(self)
        league.cities.append(city)

        self.sign_players()

        self.names_timeline = [self.name + ' ' + str(self.cosmos.year) + '-']

        if expansion:
            print '{team} ({league}) have been enfranchised.'.format(team=self.name, league=self.league.name)
            os.system('say a new franchise called the {} have been added to the league'.format(self.name))
        # if not expansion:
        #     print '\n {team} have been enfranchised.'.format(team=self.name)

        # Statistical stuff
        self.games_played = []
        self.left_on_base = []

    @property
    def name(self):
        return "{} {}".format(self.city.name, self.nickname)

    def init_name(self):
        # city_apt_team_nicknames = None
        # if self.city.yearly_apt_team_nicknames:
        #     if any(year for year in self.city.yearly_apt_team_nicknames.keys() if self.cosmos.year <= year):
        #         year = min(self.city.yearly_apt_team_nicknames.keys(), key=lambda year: self.cosmos.year-year)
        #         city_apt_team_nicknames = self.city.yearly_apt_team_nicknames[year]
        # if city_apt_team_nicknames:
        #     x = random.randint(4, 23)
        # else:
        #     x = random.randint(4, 14)
        x = random.randint(4, 14)
        if x in (0, 1):
            nickname = random.choice(COLORS) + ' Stockings'
        if x == 2:
            nickname = random.choice(COLORS) + ' Legs'
        if x == 3:
            nickname = random.choice(COLORS) + ' Caps'
        if x == 4:
            nickname = random.choice(COLORS[:-6]) + 's'
        if 4 < x < 13:
            nickname = random.choice(ANIMAL_NAMES) + 's'
        if x == 13:
            nickname = random.choice(ANIMAL_NAMES_IRREG)
        else:
            nickname = random.choice(GEN_TEAM_NAMES) + 's'
        # if x > 14:
        #     nickname = random.choice(self.city.yearly_apt_team_nicknames[self.cosmos.year])
        return nickname

    def sign_players(self):
        print "\nA new franchise in {} is fielding a team".format(self.city.name)
        pool = self.state.free_agents + random.sample(self.country.free_agents, 1000)
        pool = [p for p in pool if 16 < p.person.age < 41]
        pool = set(pool)
        # Find pitcher
        subpool = [player for player in pool if player.pitch_speed > 85]
        self.pitcher = max(subpool, key=lambda p: self.grade_pitcher(p))
        pool.remove(self.pitcher)
        print "\t{} has been signed as a pitcher".format(self.pitcher)
        # Find catcher
        self.catcher = max(pool, key=lambda p: self.grade_catcher(p))
        pool.remove(self.catcher)
        print "\t{} has been signed as a catcher".format(self.catcher)
        # Find outfielders
        lf = max(pool, key=lambda p: self.grade_left_fielder(p))
        pool.remove(lf)
        print "\t{} has been signed as a left fielder".format(lf)
        cf = max(pool, key=lambda p: self.grade_center_fielder(p))
        pool.remove(cf)
        print "\t{} has been signed as a center fielder".format(cf)
        rf = max(pool, key=lambda p: self.grade_right_fielder(p))
        pool.remove(rf)
        print "\t{} has been signed as a right fielder".format(rf)
        # Find infielders
        first = max(pool, key=lambda p: self.grade_first_baseman(p))
        pool.remove(first)
        print "\t{} has been signed as a first baseman".format(first)
        second = max(pool, key=lambda p: self.grade_second_baseman(p))
        pool.remove(second)
        print "\t{} has been signed as a second baseman".format(second)
        third = max(pool, key=lambda p: self.grade_third_baseman(p))
        pool.remove(third)
        print "\t{} has been signed as a third baseman".format(third)
        ss = max(pool, key=lambda p: self.grade_shortstop(p))
        print "\t{} has been signed as a shortstop".format(ss)
        self.players = self.fielders = [self.pitcher, self.catcher, first, second, third, ss, lf, cf, rf]
        for player in self.players:
            player.team = self
        self.pitcher.position = "P"
        self.catcher.position = "C"
        self.catcher.glove = Mitt()
        self.fielders[2].position = "1B"
        self.fielders[3].position = "2B"
        self.fielders[4].position = "3B"
        self.fielders[5].position = "SS"
        for f in self.fielders[2:6]:
            f.infielder = True
        self.pitcher.infielder = self.catcher.infielder = True
        self.fielders[6].position = "LF"
        self.fielders[7].position = "CF"
        self.fielders[8].position = "RF"
        for f in self.fielders[6:]:
            f.outfielder = True
        for p in self.players:
            p.career.team = self
            p.primary_position = p.position

    def sign_replacement(self, replacement_for):
        print "{} are looking for a replacement for {} ({})".format(
            self.name, replacement_for.name, replacement_for.position
        )
        position_of_need = replacement_for.position
        pool = self.state.free_agents + random.sample(self.country.free_agents, 10000)
        pool = [p for p in pool if 16 < p.person.age < 41]
        pool = set(pool)
        if position_of_need == "P":
            # Find pitcher
            subpool = [player for player in pool if player.pitch_speed > 85]
            self.pitcher = max(subpool, key=lambda p: self.grade_pitcher(p))
            print "{} has been signed as a pitcher".format(self.pitcher)
            self.players[0] = self.fielders[0] = self.pitcher
            self.pitcher.position = "P"
            self.pitcher.infielder = True
        elif position_of_need == "C":
            # Find catcher
            self.catcher = max(pool, key=lambda p: self.grade_catcher(p))
            print "{} has been signed as a catcher".format(self.catcher)
            self.players[1] = self.fielders[1] = self.catcher
            self.catcher.position = "C"
            self.catcher.infielder = True
        elif position_of_need == "LF":
            # Find outfielders
            lf = max(pool, key=lambda p: self.grade_left_fielder(p))
            print "{} has been signed as a left fielder".format(lf)
            self.players[-3] = self.fielders[-3] = lf
            lf.position = "LF"
            lf.outfielder = True
        elif position_of_need == "CF":
            cf = max(pool, key=lambda p: self.grade_center_fielder(p))
            print "{} has been signed as a center fielder".format(cf)
            self.players[-2] = self.fielders[-2] = cf
            cf.position = "CF"
            cf.outfielder = True
        elif position_of_need == "RF":
            rf = max(pool, key=lambda p: self.grade_right_fielder(p))
            print "{} has been signed as a right fielder".format(rf)
            self.players[-1] = self.fielders[-1] = rf
            rf.position = "RF"
            rf.outfielder = True
        elif position_of_need == "1B":
            # Find infielders
            first = max(pool, key=lambda p: self.grade_first_baseman(p))
            print "{} has been signed as a first baseman".format(first)
            self.players[2] = self.fielders[2] = first
            first.position = "1B"
            first.infielder = True
        elif position_of_need == "2B":
            second = max(pool, key=lambda p: self.grade_second_baseman(p))
            print "{} has been signed as a second baseman".format(second)
            self.players[3] = self.fielders[3] = second
            second.position = "2B"
            second.infielder = True
        elif position_of_need == "3B":
            third = max(pool, key=lambda p: self.grade_third_baseman(p))
            print "{} has been signed as a third baseman".format(third)
            self.players[4] = self.fielders[4] = third
            third.position = "3B"
            third.infielder = True
        elif position_of_need == "SS":
            ss = max(pool, key=lambda p: self.grade_shortstop(p))
            print "{} has been signed as a shortstop".format(ss)
            self.players[5] = self.fielders[5] = ss
            ss.position = "SS"
            ss.infielder = True
        for player in self.players:
            player.team = self

    def __str__(self):
        """Return string representation."""
        return self.name

    @staticmethod
    def grade_pitcher(player):
        rating = (
            (1.4-player.pitch_control) + 1.3*(player.pitch_speed/67.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_catcher(player):
        rating = (
            1.5*player.pitch_receiving + 0.75*(player.throwing_velocity_mph/72.0) +
            (2-player.swing_timing_error/0.14) + (player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_first_baseman(player):
        rating = (
            player.ground_ball_fielding +
            1.7*(2-player.swing_timing_error/0.14) + 1.5*(player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_second_baseman(player):
        rating = (
            player.ground_ball_fielding +
            1.25*(2-player.swing_timing_error/0.14) + 0.5*(player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_third_baseman(player):
        rating = (
            player.ground_ball_fielding +
            1.25*(2-player.swing_timing_error/0.14) + 0.5*(player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_shortstop(player):
        rating = (
            player.ground_ball_fielding +
            0.9*(2-player.swing_timing_error/0.14) + 0.33*(player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_left_fielder(player):
        rating = (
            player.fly_ball_fielding + 0.75*(player.throwing_velocity_mph/72.0) +
            1.5*(2-player.swing_timing_error/0.14) + (player.person.body.full_speed_seconds_per_foot/0.040623) +
            player.bat_speed/2.0 + player.composure
        )
        return rating

    @staticmethod
    def grade_center_fielder(player):
        rating = (
            player.fly_ball_fielding + 0.75*(player.throwing_velocity_mph/72.0) +
            1.75*(2-player.swing_timing_error/0.14) + 0.75*(player.person.body.full_speed_seconds_per_foot/0.040623) +
            1.5*(player.bat_speed/2.0) + player.composure
        )
        return rating

    @staticmethod
    def grade_right_fielder(player):
        rating = (
            0.75*player.fly_ball_fielding + (player.throwing_velocity_mph/72.0) +
            2*(2-player.swing_timing_error/0.14) + 0.75*(player.person.body.full_speed_seconds_per_foot/0.040623) +
            1.75*(player.bat_speed/2.0) + player.composure
        )
        return rating

    def progress(self):

        self.win_diffs.append(self.wins-self.losses)

        self.tradition = (
            (1 + len([c for c in self.championships if c > self.in_city_since])) *
            (self.cosmos.year-self.in_city_since))

        if self.cumulative_wins + self.cumulative_losses:
            # Make sure expansions don't already consider folding, relocation
            self.consider_folding()
            if not self.folded:
                self.consider_relocation()

    def consider_folding(self):

        if (float(self.cumulative_wins)/(
                  self.cumulative_wins+self.cumulative_losses)
            < .45):
            if (self.cosmos.year-self.league.founded <
                int(round(normal(25,2)))):
                y = random.randint(0, self.cosmos.year-self.league.founded)
                if y == 0:
                    self.fold()
                    # League will consider expansion more than usual to
                    # replace folded team
                    self.league.consider_expansion(to_replace=True)

    def consider_relocation(self):

        fanbase_memory = int(round(normal(27, 5)))
        # Newer teams will not relocate, but only will possibly fold, since
        # they would have no more value to another city than an expansion
        if self.cosmos.year-self.in_city_since > fanbase_memory:
            if (not self.championships or
                self.cosmos.year-self.championships[-1] > fanbase_memory):
                # Check if averaging losing season for duration of
                # fanbase memory and prior season losing season
                if (sum([d for d in self.win_diffs[-fanbase_memory:]]) /
                    fanbase_memory < 0 and self.win_diffs[-1] < 0):
                    # Some teams will never act
                    if self.tradition >= int(round(normal(200, 15))):
                        x = random.randint(0, self.tradition/4)
                    else:
                        x = random.randint(0,3)
                    if x == 0:
                        cands = []
                        vals = self.league.evaluate_cities()
                        for city in vals:
                            for i in range(vals[city]):
                                cands.append(city)
                        if cands:
                            self.relocate(city=random.choice(cands))

    def relocate(self, city):

        former_name = self.name
        print (self.name + ' (' + self.league.name +
               ') have relocated to become the...')
        self.city.teams.remove(self)
        self.city.former_teams.append(self)
        self.league.cities.remove(self.city)
        self.league.cities.append(city)
        self.city = city
        city.teams.append(self)

        self.in_city_since = self.league.cosmos.year

        x = random.randint(0,10)
        if x < 8:
            self.nickname = self.init_name()
            while self.nickname in self.country.major_league_team_nicknames:
                self.nickname = self.init_name()

        self.names_timeline[-1] = self.names_timeline[-1] + str(self.cosmos.year)
        self.names_timeline.append(self.name + ' ' + str(self.cosmos.year) + '-')

        print('\t' + self.name + ' ')
        os.system('say the {} have relocated to become the {}'.format(former_name, self.name))

    def fold(self):

        print('\n' + self.name + ' (' + self.league.name +
                  ') have folded. ')
        os.system('say the {} have folded'.format(self.name))
        self.city.teams.remove(self)
        self.city.former_teams.append(self)
        self.league.teams.remove(self)
        self.league.cities.remove(self.city)
        if self.cosmos.year == self.founded:
             self.names_timeline[-1][:-1] += ' (folded)'
        else:
            self.names_timeline[-1] += str(self.cosmos.year) + ' (folded)'
        self.league.defunct.append(self)

        self.folded = True

        for player in self.players:
            player.team = None