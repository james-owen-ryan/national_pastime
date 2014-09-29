import pickle
import math
import os
import random

from person import Person
from league import League
from data import CityData


CITY_DATA = CityData()


class Country(object):
    """A country in a baseball-centric game world."""

    def __init__(self, year):
        """Instantiate a country object."""
        self.year = year
        self.name = 'United States of America'
        self.states, self.federal_district = self.init_states_and_federal_district()
        self.capital = self.federal_district
        self.cities = []
        for state in self.states+[self.federal_district]:
            self.cities += state.cities
        self.players = []
        for city in self.cities:
            self.players += city.players
        self.free_agents = self.players
        self.leagues = []
        League(country=self)

    def init_states_and_federal_district(self):
        """Instantiate objects for all 50 states."""
        states = []
        state_names = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
                       'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Iowa', 'Kansas', 'Kentucky',
                       'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
                       'Missouri', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
                       'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'South Carolina',
                       'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
                       'West Virginia', 'Wisconsin', 'Wyoming', 'Montana', 'Nebraska', 'Rhode Island',
                       'Pennsylvania', 'Illinois', 'Indiana']
        for state_name in state_names:
            states.append(State(name=state_name, country=self))
        federal_district = FederalDistrict(name="District of Columbia", country=self)
        return states, federal_district

    def __str__(self):
        return self.name

    @property
    def league_names(self):
        return set(league.name for league in self.leagues)

    @property
    def major_nicknames(self):
        major_nicknames = set()
        for league in self.leagues:
            for team in league.teams:
                major_nicknames.add(team.nickname)
        return major_nicknames


class State(object):
    """A state in a country in a baseball-centric game world."""

    def __init__(self, name, country):
        self.name = name
        self.country = country
        self.cities = self.init_cities()
        self.players = []
        for city in self.cities:
            self.players += city.players
        self.free_agents = self.players

    def init_cities(self):
        """Instantiate objects for all cities currently in our database."""
        cities_in_this_state = []
        for city_and_state in CITY_DATA.cities:
            city_name, state_name = city_and_state.split(', ')
            if state_name == self.name:
                cities_in_this_state.append(City(state=self, name=city_name))
        return cities_in_this_state

    def __str__(self):
        return self.name


class FederalDistrict(object):
    """A district in a country in a baseball-centric game world."""

    def __init__(self, name, country):
        self.name = name
        self.country = country
        self.cities = self.init_cities()
        self.players = []
        for city in self.cities:
            self.players += city.players
        self.free_agents = self.players

    def init_cities(self):
        """Instantiate objects for all cities currently in our database."""
        cities_in_this_district = []
        for city_and_state_or_district in CITY_DATA.cities:
            city_name, state_or_district_name = city_and_state_or_district.split(', ')
            if state_or_district_name == self.name:
                cities_in_this_district.append(City(state=self, name=city_name))
        return cities_in_this_district

    def __str__(self):
        return self.name


class City(object):
    """A city in a state or district in a baseball-centric game world."""

    def __init__(self, name, state):
        self.name = name
        self.state = state
        self.country = state.country
        # Attribute data about this city
        key = "{}, {}".format(self.name, self.state.name)
        self.coordinates = CITY_DATA.coordinates[key]
        self.latitude, self.longitude = self.coordinates
        self.yearly_populations = CITY_DATA.yearly_populations[key]
        self.population = self.yearly_populations[self.country.year]
        if self.population > 0:
            self.pop = max(self.population/1000, 1)  # Used variously as a convenience
        else:
            self.pop = 0
        if key in CITY_DATA.apt_nicknames:
            self.yearly_apt_team_nicknames = CITY_DATA.apt_nicknames[key]
        else:
            self.yearly_apt_team_nicknames = []
        # Prepare various baseball lists about this city
        self.free_agents = self.players = self.init_players()
        self.teams = []

    def init_players(self):
        players_in_this_city = []
        for i in range(self.pop * 5):
            players_in_this_city.append(Person(birthplace=self))
        return players_in_this_city

    def __str__(self):
        """Return the city's name and population in a readable format."""
        readable_pop = ''
        for i in xrange(len(str(self.population)[::-1])):
            if i and not i % 3:
                readable_pop += ','
            readable_pop += str(self.population)[::-1][i]
        return "{}, {} (pop. {})".format(self.name, self.state.name, readable_pop[::-1])

    def get_dist(self, city):
        """Return Pythagorean distance between another city and this one."""
        lat_dist = self.latitude-city.latitude
        long_dist = self.longitude-city.longitude
        dist = math.sqrt((lat_dist * lat_dist) + (long_dist * long_dist))
        return dist

    def progress(self):
        self.population = self.yearly_populations[self.country.year]
        self.pop = max(self.population/1000, 1)
