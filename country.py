import pickle
import os
import random

from city import City
from league import League
from ballpark import Ballpark
from game import Game, Inning, Frame, AtBat
from rules import Rules


# POSSIBLE HARD-CODERS:
#       "Single hit by Cyrille Buroker"
#       "Home run hit by Steward Wainer!"  [Was waiting a long time to see this finally]
#       FINALLY, a double is hit! By Bob McKibben (Philadelphia).


class Country(object):
    """A country in a baseball-centric game world."""

    def __init__(self, year):
        """Instantiate a country object."""
        self.name = 'United States of America'
        self.year = year
        self.players = []
        self.leagues = []
        self.league_names = []
        # Nicknames for major league teams, used to prevent duplicates
        self.major_nicknames = []
        self.champions = []
        self.champions_timeline = []
        self.cities = self.init_cities()
        self.leagues = self.init_leagues()

    def init_cities(self):
        """Instantiate objects for all cities in the database.

        This method..."""
        # Load all of our city data
        city_names = self.load_city_names()
        city_latitudes, city_longitudes = (
            self.load_city_geographic_coordinates()
        )
        city_yearly_populations = self.load_city_yearly_populations()
        city_unique_team_nicknames = self.load_city_unique_team_nicknames(
            city_names=city_names
        )
        # Instantiate a City object for each city, and append each of
        # these objects to a list
        cities = []
        for city in city_names:
            latitude = city_latitudes[city]
            longitude = city_longitudes[city]
            populations = city_yearly_populations[city]
            unique_team_nicknames = city_unique_team_nicknames[city]
            city = City(country=self, name=city, latitude=latitude,
                        longitude=longitude, populations=populations,
                        yearly_unique_team_nicknames=unique_team_nicknames)
            cities.append(city)
        # Return the list of City objects
        return cities

    def init_leagues(self):
        leagues = []
        # for i in range(int(round(normal(1, 0.35)))):
        for i in xrange(1):
            l = League(country=self)
            leagues.append(l)
        return leagues

    def __str__(self):

        rep = self.name
        return rep

    def progress(self, following=None):

        if len(self.leagues) == 0:
            x = random.randint(0,2)
            if x == 0:
                League(self)
        if len(self.leagues) == 1:
            x = random.randint(0,19)
            if x == 0:
                League(self)

        for l in self.leagues:
            l.conduct_season(following=following)

        if len(self.leagues) == 2:
            l1 = self.leagues[0]
            l2 = self.leagues[1]

            # Print marquee
            matchup = l1.champion.name + ' vs. ' + l2.champion.name
            print '\n\t' + '#' * (len(matchup) + 4)
            print ('\t' + ' '*((((len(matchup)+4)-17)/2)+1) + str(self.year)
                   + ' World Series' + ' '*((((len(matchup)+4)-17)/2)+1))
            print '\t  ' + matchup
            print '\t' + '#' * (len(matchup) + 4) + '\n'

            # Alternate World Series home field advantage each year
            if self.year % 2 == 0:
                l1.seasons[-1].sim_world_series(adv=l1.champion,
                                                dis=l2.champion)
            if self.year % 2 == 1:
                l2.seasons[-1].sim_world_series(adv=l2.champion,
                                                dis=l1.champion)

        if len(self.leagues) == 1:
            self.champion = self.leagues[0].champion
            self.champions.append(self.leagues[0].champion)
            self.champions_timeline.append(str(self.year) + ': ' +
                                           self.leagues[0].champion.name)
            self.leagues[0].champion.records_timeline[-1] += '*'

        if self.champion:
            self.champion.city.champions.add(self.champion)
            self.champion.city.champions_timeline.append(str(self.year) +
                                                  ': ' + self.champion.name)

        self.year += 1

        for l in self.leagues:
            l.conduct_offseason()

        for city in self.cities:
            try:
                city.progress()
            except KeyError:
                pass

    @staticmethod
    def load_city_names():
        # Load the list of city names for which we currently have data
        city_names = [name.strip('\n') for name in open(
            os.getcwd()+'/data/city_names.txt', 'r')
        ]
        return city_names

    @staticmethod
    def load_city_geographic_coordinates():
        # Load city geographic coordinates
        city_latitudes = pickle.load(
            open(os.getcwd()+'/data/city_latitudes.dat', 'rb')
        )
        city_longitudes = pickle.load(
            open(os.getcwd()+'/data/city_longitudes.dat', 'rb')
        )
        return city_latitudes, city_longitudes

    @staticmethod
    def load_city_yearly_populations():
        # Load city yearly populations
        city_yearly_populations = pickle.load(
            open(os.getcwd()+'/data/city_yearly_populations.dat', 'rb')
        )
        return city_yearly_populations

    @staticmethod
    def load_city_unique_team_nicknames(city_names):
        # This is a list that I've curated myself that associates
        # cities with peculiar nicknames that would work especially
        # well for that city, e.g., Minneapolis Millers
        raw_file = open(
            os.getcwd() + "/data/city_unique_team_nicknames.txt"
        )
        lines = [line.strip('\n') for line in raw_file.readlines()]
        city_unique_nicknames = {}
        for city in city_names:
            city_index = lines.index(city)
            # If there is no entry for this city, assign to this city
            # a dictionary mapping each year to an empty list
            if city_index+1 == len(lines) or not lines[city_index+1]:
                city_unique_nicknames[city] = {
                    year: [] for year in xrange(1845, 1990)
                }
            # If there is an entry for this city, read the part of the
            # file pertaining to the city line by line
            current_index = city_index
            unique_nicknames = {}
            while current_index+1 < len(lines) and lines[current_index+1]:
                current_index += 1
                current_line = lines[current_index]
                if current_line[1] != '\t':  # Reached a new year
                    current_year = int(current_line[1:])
                    unique_nicknames[current_year] = []
                elif current_line[1] == '\t':  # Reached a new nickname
                    unique_nicknames[current_year].append(current_line[2:])
            # Once we've reached a blank line, we've exhaustively assembled
            # all the city's nicknames -- now we need to fill in entries for
            # missing years, for which we'll copy the entry from the most
            # recent year that has an entry
            years = unique_nicknames.keys()
            years.sort()
            for year in xrange(1845, 1990):
                if year not in unique_nicknames:
                    if not any(y for y in years if year > y):
                        unique_nicknames[year] = []
                    else:
                        # Copy the most recent yearly entry
                        year_to_copy = min([y for y in years if year > y],
                                           key=lambda q: year-q)
                        unique_nicknames[year] = unique_nicknames[year_to_copy]
            city_unique_nicknames[city] = unique_nicknames
        return city_unique_nicknames

us = Country(year=1890)
pitcher = min(us.players, key=lambda p: p.pitch_control)
slap = min(us.players, key=lambda b: b.swing_timing_error)
random.shuffle(us.players)
fatty = next(p for p in us.players if p.weight > 200 and p.swing_timing_error < .1)
random.shuffle(us.players)
ump = next(z for z in us.players if z.hometown.name in ("Minneapolis", "St. Paul", "Duluth"))
catcher = max(us.players, key=lambda qqq: qqq.pitch_receiving)
other_fielders = random.sample(us.players, 7)
for i in xrange(len(other_fielders)):
    d = {0: "1B", 1: "2B", 2: "SS", 3: "3B", 4: "RF", 5: "CF", 6: "LF"}
    other_fielders[i].position = d[i]
fielders = other_fielders + [pitcher, catcher]
catcher.position = "C"
pitcher.position = "P"
l = us.leagues[0]
home_team = l.teams[0]
ballpark = Ballpark(city=l.teams[0].city, tenants=[home_team])
if any(t for t in l.teams if t.city.name in ("Minneapolis", "St. Paul", "Duluth") and t is not home_team):
    away_team = next(t for t in l.teams if t.city.name in ("Minneapolis", "St. Paul", "Duluth") and
                     t is not home_team)
else:
    away_team = l.teams[1]
game = Game(ballpark=ballpark, league=l, home_team=home_team, away_team=away_team, rules=Rules()); game.enact()
# inning = Inning(game=game, number=5); frame = Frame(inning=inning, bottom=True); ab = AtBat(frame=frame); ab.enact(); print ab.result
# ab.draw_playing_field()
# frame = Frame(inning=inning, bottom=True); ab = AtBat(frame=frame);