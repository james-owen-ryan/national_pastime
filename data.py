import os
import pickle
import random


class CityData(object):

    def __init__(self):
        # Load the list of city names for which we currently have data
        self.cities = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/data/city_names.txt', 'r')
        )
        # Load geographic coordinates of the form (latitude, longitude)
        # for these cities
        self.coordinates = pickle.load(
            open(os.getcwd()+'/data/city_coordinates.dat', 'rb')
        )
        # Load yearly populations, which represent (often incomplete) figures
        # from 1840-1996
        self.yearly_populations = pickle.load(
            open(os.getcwd()+'/data/city_yearly_populations.dat', 'rb')
        )
        # Load apt team nicknames for cities that have them -- these are
        # specified in city_apt_team_nicknames
        self.apt_nicknames = self.load_city_unique_team_nicknames(
            city_names=self.cities
        )

    @staticmethod
    def load_city_unique_team_nicknames(city_names):
        # This is a list that I've curated myself that associates
        # cities with peculiar nicknames that would work especially
        # well for that city, e.g., Minneapolis Millers
        raw_file = open(
            os.getcwd() + "/data/city_apt_team_nicknames.txt"
        )
        lines = [line.strip('\n') for line in raw_file.readlines()]
        city_apt_nicknames = {}
        for city in city_names:
            if city in lines:
                city_index = lines.index(city)
                # If there is no entry for this city, assign to this city
                # a dictionary mapping each year to an empty list
                if city_index+1 == len(lines) or not lines[city_index+1]:
                    city_apt_nicknames[city] = {
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
                city_apt_nicknames[city] = unique_nicknames
        return city_apt_nicknames


class Names(object):

    def __init__(self):
        self.masculine_forenames = tuple(
            name[:-1] for name in
            open(os.getcwd()+'/corpora/masculine_names.txt', 'r')
        )
        self.feminine_forenames = tuple(
            name[:-1] for name in
            open(os.getcwd()+'/corpora/feminine_names.txt', 'r')
        )
        self.english_surnames = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/corpora/english_surnames.txt', 'r')
        )
        self.french_surnames = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/corpora/french_surnames.txt', 'r')
        )
        self.german_surnames = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/corpora/german_surnames.txt', 'r')
        )
        self.irish_surnames = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/corpora/irish_surnames.txt', 'r')
        )
        self.scandinavian_surnames = tuple(
            name.strip('\n') for name in
            open(os.getcwd()+'/corpora/scandinavian_surnames.txt', 'r')
        )
        self.all_surnames = (
            self.english_surnames + self.french_surnames + self.irish_surnames +
            self.scandinavian_surnames
        )

    @property
    def a_masculine_name(self):
        return random.choice(self.masculine_forenames)

    @property
    def a_feminine_name(self):
        return random.choice(self.feminine_forenames)

    @property
    def an_english_surname(self):
        return random.choice(self.english_surnames)

    @property
    def a_french_surname(self):
        return random.choice(self.french_surnames)

    @property
    def a_german_surname(self):
        return random.choice(self.german_surnames)

    @property
    def an_irish_surname(self):
        return random.choice(self.irish_surnames)

    @property
    def a_scandinavian_surname(self):
        return random.choice(self.scandinavian_surnames)

    @property
    def any_surname(self):
        return random.choice(self.all_surnames)
