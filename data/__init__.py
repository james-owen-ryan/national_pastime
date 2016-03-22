import os
import pickle
import random
import datetime


class CityData(object):
    """A class holding data pertaining to cities that will be simulated in the game."""

    def __init__(self):
        """Initialize a CityData object."""
        # Prepare a dictionary mapping U.S. state abbreviations to their full names
        self.state_abbreviation_to_state_name = {
            line.strip('\n').split('\t')[0]: line.strip('\n').split('\t')[1] for
            line in open(os.getcwd()+'/data/state_abbreviation_to_state_name.tsv', 'r').readlines()
        }
        # Prepare a dictionary mapping each U.S. state to the mean year of establishment
        # for its cities (this will be approximately the year that cities in this state
        # for which we have no establishment year will be introduced into the simulation)
        self.state_name_to_mean_city_establishment_year = {
            line.strip('\n').split('\t')[0]: int(line.strip('\n').split('\t')[1]) for
            line in open(os.getcwd()+'/data/mean_city_establishment_years_by_state.tsv', 'r').readlines()
        }
        # Load yearly populations, which represent (often incomplete) figures from 1840-1996
        # for (one-time) major cities only; for all other cities, we'll maintain populations
        # that hover around the minor-city cap (specified in config.py) at all times
        self.yearly_populations_for_major_cities = pickle.load(
            open(os.getcwd()+'/data/city_yearly_populations.dat', 'rb')
        )
        for major_city in self.yearly_populations_for_major_cities:
            # Fill in missing values (especially ones in the range 1790-1839, which
            # aren't included in the data) with -99, the code for minor city
            for year in xrange(1790, 1990):
                if year not in self.yearly_populations_for_major_cities[major_city]:
                    self.yearly_populations_for_major_cities[major_city][year] = -99
        self.yearly_populations_for_minor_cities = {year: -99 for year in xrange(1790, 1990)}
        # Prepare specifications holding all the pertinent data for each city in the U.S.
        self.city_specifications = []
        for line in open(os.getcwd()+'/data/all_us_cities_data.tsv', 'r').readlines()[1:]:  # Skip header
            raw_city_specification = line.strip('\n')
            self.city_specifications.append(
                CitySpecification(city_data_object=self, raw_specification=raw_city_specification)
            )
        # Prepare a dictionary mapping ordinal dates that cities should be established
        # to the CitySpecification objects corresponding to those cities
        self.ordinal_dates_of_city_establishment = {}
        for city_specification in self.city_specifications:
            if city_specification.ordinal_date_to_establish not in self.ordinal_dates_of_city_establishment:
                self.ordinal_dates_of_city_establishment[city_specification.ordinal_date_to_establish] = set()
            self.ordinal_dates_of_city_establishment[city_specification.ordinal_date_to_establish].add(
                city_specification
            )


class CitySpecification(object):
    """Data pertaining to a specific city that will be simulated in the game."""

    def __init__(self, city_data_object, raw_specification):
        """Initialize a CitySpecification object."""
        # For now, we're only including U.S. cities, though of course this may
        # change (in which case, this whole module will need to be modified)
        self.country_name = "United States of America"
        # These attributes will be set by self._init_parse_raw_specification()
        self.city_name = None
        self.state_name = None
        self.county_name = None
        self.latitude = None
        self.longitude = None
        self.timezone = None
        self.dst_participants = None  # Whether this city participates in daylight saving time
        self.zip_codes = None
        self.year_incorporated = None
        self.year_founded = None
        # Parse the raw specification
        self._init_parse_raw_specification(city_data_object=city_data_object, raw_specification=raw_specification)
        # Specify a date on which this city should be founded
        self.ordinal_date_to_establish = self._determine_date_to_establish(city_data_object=city_data_object)
        # Specify the true yearly populations for this city, if we have such data (we only
        # have it for major cities)
        key = '{}, {}'.format(self.city_name, self.state_name)
        if key in city_data_object.yearly_populations_for_major_cities:
            self.yearly_populations = city_data_object.yearly_populations_for_major_cities[key]
        else:
            self.yearly_populations = city_data_object.yearly_populations_for_minor_cities

    def _init_parse_raw_specification(self, city_data_object, raw_specification):
        """Parse the raw specification for this city's data to set the core attributes of this object."""
        raw_specification = raw_specification.split('\t')
        self.city_name = raw_specification[0]
        self.state_name = city_data_object.state_abbreviation_to_state_name[raw_specification[1]]
        self.county_name = raw_specification[2]
        self.latitude = float(raw_specification[3])
        self.longitude = float(raw_specification[4])
        self.timezone = int(raw_specification[5])
        self.dst_participants = True if int(raw_specification[6]) else False
        self.zip_codes = raw_specification[7].split(',')
        self.year_incorporated = int(raw_specification[8]) if raw_specification[8] else None
        self.year_founded = int(raw_specification[9]) if raw_specification[9] else None

    def _determine_date_to_establish(self, city_data_object):
        """Determine a date that this city should be established (i.e., introduced into the simulation)."""
        if self.year_incorporated and self.year_founded:
            year = min(self.year_incorporated, self.year_founded)
        elif self.year_incorporated or self.year_founded:
            year = self.year_incorporated or self.year_founded
        else:
            # Go with the mean year of establishment for all cities in this city's
            # state, plus or minus ten or so years
            year = city_data_object.state_name_to_mean_city_establishment_year[self.state_name]
            year += int(random.random()*10) if random.random() < 0.5 else -int(random.random()*10)
        # Lastly, roll a random day of the year (so that all cities aren't established on
        # Jan 1), and return this (as an ordinal date)
        ordinal_date_this_city_will_be_established = self._get_random_ordinal_date_of_year(year=year)
        return ordinal_date_this_city_will_be_established

    @staticmethod
    def _get_random_ordinal_date_of_year(year):
        """Return a random ordinal date in the given year."""
        ordinal_date_on_jan_1_of_this_year = datetime.date(year, 1, 1).toordinal()
        ordinal_date = (
            ordinal_date_on_jan_1_of_this_year + random.randint(0, 365)
        )
        return ordinal_date