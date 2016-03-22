import os
import pickle
import math
import heapq


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
    already_computed_distances = {}
    for i in xrange(len(city_data)):
        if i % 100 == 0:
            print "{}/{}".format(i/100, n_cities/100)
        # Prepare data
        city = city_data[i]
        city_name, city_state, city_latitude, city_longitude = city[0], city[1], city[3], city[4]
        city_latitude = float(city_latitude)
        city_longitude = -float(city_longitude)  # Easier to calculate with a positive longitude
        all_other_cities_ranked_by_distance = []
        for other_city in city_data:
            if other_city != city:
                # Prepare data
                other_city_name, other_city_state, other_city_latitude, other_city_longitude = (
                    other_city[0], other_city[1], other_city[3], other_city[4]
                )
                other_city_latitude = float(other_city_latitude)
                other_city_longitude = -float(other_city_longitude)
                # Calculate and record the distance
                lat_dist = city_latitude-other_city_latitude
                long_dist = city_longitude-other_city_longitude
                distance = math.sqrt((lat_dist**2) + (long_dist**2))
                heapq.heappush(all_other_cities_ranked_by_distance, (distance, (city_name, city_state)))
                # Save this distance so that we don't have to compute it again
                if (other_city_name, other_city_state) not in already_computed_distances:
                    already_computed_distances[(other_city_name, other_city_state)] = {}
                already_computed_distances[(other_city_name, other_city_state)][city_name, city_state] = distance
        # Save the ranking
        city_distance_rankings[(city_name, city_state)] = all_other_cities_ranked_by_distance
    # Pickle the rankings dictionary and save it to national_pastime/data
    out_file = open(os.getcwd()+'/data/city_distance_rankings.dat', 'wb')
    pickle.dump(city_distance_rankings, out_file)
    out_file.close()