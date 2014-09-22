import math
import os
import random
from person import Person

ENGLISH_SURNAMES = [name.strip('\n') for name in open(
    os.getcwd()+'/corpora/english_surnames.txt', 'r')
]
FRENCH_SURNAMES = [name.strip('\n') for name in open(
    os.getcwd()+'/corpora/french_surnames.txt', 'r')
]
GERMAN_SURNAMES = [name.strip('\n') for name in open(
    os.getcwd()+'/corpora/german_surnames.txt', 'r')
]
IRISH_SURNAMES = [name.strip('\n') for name in open(
    os.getcwd()+'/corpora/irish_surnames.txt', 'r')
]
SCANDINAVIAN_SURNAMES = [name.strip('\n') for name in open(
    os.getcwd()+'/corpora/scandinavian_surnames.txt', 'r')
]
ALL_SURNAMES = ENGLISH_SURNAMES+FRENCH_SURNAMES+GERMAN_SURNAMES+IRISH_SURNAMES+SCANDINAVIAN_SURNAMES


class City(object):

    def __init__(self, country, name, latitude, longitude, populations,
                 yearly_unique_team_nicknames):
        self.country = country
        self.year = self.country.year
        self.name = name
        if self.name == 'Portland (OR)':
            self.name = 'Portland'
        self.latitude = latitude
        self.longitude = longitude
        self.yearly_populations = populations
        self.population = populations[self.year]
        self.pop = self.population/1000
        self.yearly_unique_team_nicknames = yearly_unique_team_nicknames
        self.unique_nicknames = yearly_unique_team_nicknames[self.year]

        self.teams = []
        self.former_teams = []
        self.champions = set()
        self.champions_timeline = []

        self.players = []

        self.surnames = self.get_surnames()

        for i in range(self.pop * 5):
            p = Person(birthplace=self)
            self.players.append(p)
            self.country.players.append(p)

    def get_surnames(self):
        if self.name == "Milwaukee":
            return GERMAN_SURNAMES
        elif self.name in ("Minneapolis", "St. Paul", "Duluth"):
            return SCANDINAVIAN_SURNAMES
        elif self.name == "Boston":
            return IRISH_SURNAMES
        elif self.name == "Philadelphia":
            return IRISH_SURNAMES+ENGLISH_SURNAMES
        elif self.name == "New Orleans":
            return FRENCH_SURNAMES
        else:
            return ALL_SURNAMES

    def __str__(self):
        """Return the city's name and population, in a readable format."""
        readable_pop = ''
        for i in xrange(len(str(self.population)[::-1])):
            if i and not i % 3:
                readable_pop += ','
            readable_pop += str(self.population)[::-1][i]
        return self.name + ', pop. ' + readable_pop[::-1]

    def get_dist(self, city):
        """Return Pythagorean distance between city and self."""
        lat_dist = self.latitude-city.latitude
        long_dist = self.longitude-city.longitude
        dist = math.sqrt((lat_dist * lat_dist) + (long_dist * long_dist))
        return dist

    def progress(self):
        self.population = self.yearly_populations[self.country.year]
        self.pop = self.population/1000
        self.unique_nicknames = self.unique_nicknames[self.country.year]