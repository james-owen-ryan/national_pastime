import os
import pickle
import math
import heapq
from scipy import spatial


def compute_nearest_cities_ranking_for_all_us_cities():
    """Precompute for each city a ranking of all other U.S. cities according to their distance from that city."""
    # Read in the file specifying city latitudes and longitudes
    f = open('/Users/jamesryan/Desktop/Projects/Personal/national_pastime/data/all_us_cities_data.tsv', 'r')
    city_data = f.read().split('\n')
    city_data = [line.strip('\n').split('\t') for line in city_data]
    # Make sure it's the structured how we think it is
    header = city_data[0]
    assert header == [
        'city_name', 'state_abbrev', 'county_name', 'latitude', 'longitude',
        'timezone', 'dst', 'zipcodes', 'year_incorporated', 'year_founded'
    ]
    # Throw away the header
    del city_data[0]
    # Prepare a dictionary to hold the rankings
    city_distance_rankings = {}
    # Compute and save the rankings
    n_cities = len(city_data)
    for i in xrange(len(city_data)):
        if i % 100 == 0:
            print "{}/{}".format(i/100, n_cities/100)
        # Prepare data
        city = city_data[i]
        city_name, city_state, city_latitude, city_longitude = city[0], city[1], city[3], city[4]
        city_latitude = float(city_latitude)
        city_longitude = -float(city_longitude)  # Easier to calculate with a positive longitude
        city_coordinates = (city_latitude, city_longitude)
        all_other_cities_ranked_by_distance = []
        for other_city in city_data:
            if other_city != city:
                # Prepare data
                other_city_name, other_city_state, other_city_latitude, other_city_longitude = (
                    other_city[0], other_city[1], other_city[3], other_city[4]
                )
                other_city_latitude = float(other_city_latitude)
                other_city_longitude = -float(other_city_longitude)
                other_city_coordinates = (other_city_latitude, other_city_longitude)
                # Calculate and record the distance (unless we already have)
                distance = spatial.distance.euclidean(city_coordinates, other_city_coordinates)
                all_other_cities_ranked_by_distance.append(
                    (distance, (other_city_name, other_city_state))
                )
        # Sort the list into a ranking
        all_other_cities_ranked_by_distance.sort(key=lambda entry: entry[0])
        # Save the ranking
        city_distance_rankings[(city_name, city_state)] = all_other_cities_ranked_by_distance
    # Pickle the rankings dictionary and save it to national_pastime/data
    out_file = open(os.getcwd()+'/city_distance_rankings.dat', 'wb')
    pickle.dump(city_distance_rankings, out_file)
    out_file.close()