import os
import pickle


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
        # Load the first year each city will become present in the simulation, i.e.,
        # the first year for which we have population data for that city
        self.city_instantiation_years = pickle.load(
            open(os.getcwd()+'/data/city_first_year_in_sim.dat', 'rb')
        )