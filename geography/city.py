import math
import heapq
import random
from city_planning import CityPlan
from people.business import *
from people.person import PersonExNihilo
from utils import utilities
from people.event import Fate
from baseball.ballpark import Ballpark


class City(object):
    """A city in a baseball cosmos."""

    def __init__(self, cosmos, specification):
        """Initialize a City object."""
        self.cosmos = cosmos
        self.name = specification.city_name
        self.country = next(c for c in cosmos.countries if c.name == specification.country_name)
        print specification.state_name
        self.state = next(s for s in self.country.states+[self.country.capital] if s.name == specification.state_name)
        self.full_name = '{}, {}'.format(self.name, self.state.name)
        print "Establishing {}".format(self.full_name)
        self.founded = self.cosmos.year
        # Set various data
        self.latitude = specification.latitude
        self.longitude = -specification.longitude  # Convert to a positive float (makes distance calculation easier)
        self.coordinates = self.latitude, self.longitude
        self.true_yearly_populations = specification.yearly_populations
        # Update geographic listings
        self.state.cities.append(self)
        self.country.cities.append(self)
        self.cosmos.cities.append(self)
        # Prepare various listings
        self.settlers = set()  # First people to live in this city
        self.residents = set()
        self.departed = set()  # People who left the city (i.e., left the simulation)
        self.deceased = set()  # People who died in in the city
        self.companies = set()
        self.former_companies = set()
        self.dwelling_places = set()  # Both houses and apartment units (not complexes)
        self.former_dwelling_places = set()
        # Prepare baseball-related attributes
        self.teams = []
        # Generate a city plan
        city_plan = CityPlan(city=self)
        while len(city_plan.tracts) < 2:
            print "Re-rolling on a city plan for {} (not enough tracts)".format(self.full_name)
            city_plan = CityPlan(city=self)
        self.streets = city_plan.streets
        self.parcels = city_plan.parcels
        self.lots = city_plan.lots
        self.tracts = city_plan.tracts
        self.travel_distances_between_blocks = city_plan.travel_distances_between_parcels
        for lot in self.lots | self.tracts:
            lot.set_neighboring_lots()
            lot.init_generate_address()
        city_plan.determine_conventional_city_blocks()
        self.blocks = city_plan.blocks
        self.downtown = self._init_determine_downtown_lot()
        self.mayor = None  # Currently being set by _init_get_established()
        self.last_simulated_day = self.cosmos.ordinal_date
        # These get set when these businesses get established (by their __init__() magic methods)
        self.cemetery = None
        self.city_hall = None
        self.fire_station = None
        self.hospital = None
        self.police_station = None
        self.school = None
        self.university = None
        # This gets set by a call to set_ten_nearest_cities() upon new cities getting established
        self.nearest_cities = []
        self.set_nearest_cities()  # Necessary to do now so that people from other cities may start businesses here
        # This represents whether a city has redundant businesses that could be shut down
        # to reduce the population of the city
        self.minimal_infrastructure = False
        self.overpopulated = False
        self.underpopulated = True
        # Establish the city -- have people move in and start up businesses
        self._init_get_established()

        # TODO MAKE THIS COOL (PROB BY HAVING THE BALLPARK BE AT THE BASEBALL HQ, A BUSINESS OBJECT?)
        self.ballpark = Ballpark(city=self)

    def _init_determine_downtown_lot(self):
        """Return the lot located among the greatest density of lots."""
        downtown = None
        highest_density = float("-inf")
        for lot in self.lots:
            density = self.tertiary_density(lot)
            if density > highest_density:
                highest_density = density
                downtown = lot
        return downtown

    def _init_get_established(self):
        """Establish the city in which this gameplay instance will take place."""
        # Have at least one farm be established, and make its owner the mayor
        farm = Farm(city=self)
        self.mayor = farm.owner.person  # TODO actual mayor stuff
        # JOR 03-21-16: COMMENTING THIS OUT TO SEE IF CITIES WILL STILL REACH THEIR IDEAL POPS FAIRLY QUICKLY
        # AND MORE NATURALLY -- CAN DELETE IT THIS SEEMS ACHIEVED
        # while self.underpopulated:
        #     self.manipulate_population()
        # Set the city's 'settlers' attribute
        self.settlers = set(self.residents)

    def __str__(self):
        """Return string representation."""
        return "{}, {} (pop. {})".format(self.name, self.state.name, self.pop)

    def dist_from_downtown(self, lot):
        """Return the number of a blocks between a given lot and the center of downtown."""
        return self.distance_between(lot, self.downtown)

    def distance_between(self, lot1, lot2):
        """Return travel distance in blocks (given street layouts) between the given lots."""
        min_dist = float("inf")
        for parcel in lot1.parcels:
            for other_parcel in lot2.parcels:
                try:
                    if self.travel_distances_between_blocks[(parcel, other_parcel)] < min_dist:
                        min_dist = self.travel_distances_between_blocks[(parcel, other_parcel)]
                except KeyError:
                    print "Trying to find distance between a lot in {} and one in {} -- lol?".format(
                        lot1.city, lot2.city
                    )
        return min_dist

    def nearest_business_of_type(self, lot, business_type):
        """Return the Manhattan distance between a given lot and the nearest company of the given type.

        @lot: The lot for which the nearest business of this type is being determined.
        @param business_type: The Class representing the type of company in question.
        """
        businesses_of_this_type = self.businesses_of_type(business_type)
        if businesses_of_this_type:
            return min(businesses_of_this_type, key=lambda b: self.distance_between(lot, b.lot))
        else:
            return None

    def dist_to_nearest_business_of_type(self, lot, business_type, exclusion):
        """Return the Manhattan distance between a given lot and the nearest company of the given type.

        @lot: The lot from which distance to a company is being measured.
        @param business_type: The Class representing the type of company in question.
        @param exclusion: A company who is being excluded from this determination because they
                          are the ones making the call to this method, as they try to decide where
                          to put their lot.
        """
        distances = [
            self.distance_between(lot, company.lot) for company in self.companies if isinstance(company, business_type)
            and company is not exclusion
        ]
        if distances:
            return max(99, min(distances))  # Elsewhere, a max of 99 is relied on
        else:
            return None

    @staticmethod
    def secondary_population(lot):
        """Return the total population of this lot and its neighbors."""
        secondary_population = 0
        for neighbor in {lot} | lot.neighboring_lots:
            secondary_population += neighbor.population
        return secondary_population

    @staticmethod
    def tertiary_population(lot):
        lots_already_considered = set()
        tertiary_population = 0
        for neighbor in {lot} | lot.neighboring_lots:
            if neighbor not in lots_already_considered:
                lots_already_considered.add(neighbor)
                tertiary_population += neighbor.population
                for neighbor_to_that_lot in neighbor.neighboring_lots:
                    if neighbor_to_that_lot not in lots_already_considered:
                        lots_already_considered.add(neighbor_to_that_lot)
                        tertiary_population += neighbor.population
        return tertiary_population

    @staticmethod
    def tertiary_density(lot):
        lots_already_considered = set()
        tertiary_density = 0
        for neighbor in {lot} | lot.neighboring_lots:
            if neighbor not in lots_already_considered:
                lots_already_considered.add(neighbor)
                tertiary_density += 1
                for neighbor_to_that_lot in neighbor.neighboring_lots:
                    if neighbor_to_that_lot not in lots_already_considered:
                        lots_already_considered.add(neighbor_to_that_lot)
                        tertiary_density += 1
        return tertiary_density

    def set_nearest_cities(self):
        """Get the ten nearest cities to this one."""
        nearest_cities = heapq.nsmallest(
            21, self.state.country.cities, key=lambda city: self.distance_to(city)
        )
        if self in nearest_cities:
            nearest_cities.remove(self)
        self.nearest_cities = nearest_cities

    @property
    def random_person(self):
        """Return a random person living in this city."""
        return random.choice(list(self.residents))

    @property
    def pop(self):
        """Return the number of NPCs living in the city."""
        return len(self.residents)

    @property
    def population(self):
        """Return the number of NPCs living in the city."""
        return len(self.residents)

    @property
    def vacant_lots(self):
        """Return all vacant lots in the city."""
        vacant_lots = [lot for lot in self.lots if not lot.building]
        return vacant_lots

    @property
    def vacant_tracts(self):
        """Return all vacant tracts in the city."""
        vacant_tracts = [tract for tract in self.tracts if not tract.landmark]
        return vacant_tracts

    @property
    def vacant_homes(self):
        """Return all vacant homes in the city."""
        vacant_homes = [home for home in self.dwelling_places if not home.residents]
        return vacant_homes

    @property
    def all_time_residents(self):
        """Return everyone who has at one time lived in the city."""
        return self.residents | self.deceased | self.departed

    @property
    def unemployed(self):
        """Return unemployed (mostly young) people, excluding retirees."""
        unemployed_people = set()
        for resident in self.residents:
            if resident.searching_for_work:
                unemployed_people.add(resident)
        return unemployed_people

    @property
    def free_agents(self):
        all_players = [resident.player for resident in self.residents if resident.player]
        free_agents = list(all_players)
        for player in all_players:
            if player.career.retired:
                free_agents.remove(player)
            elif player.career.team and player in player.career.team.players:
                free_agents.remove(player)
        return free_agents

    def distance_to(self, city):
        """Return Pythagorean distance between another city and this one."""
        lat_dist = self.latitude-city.latitude
        long_dist = self.longitude-city.longitude
        dist = math.sqrt((lat_dist**2) + (long_dist**2))
        return dist

    def workers_of_trade(self, occupation):
        """Return all population in the city who practice to given occupation.

        @param occupation: The class pertaining to the occupation in question.
        """
        return [resident for resident in self.residents if isinstance(resident.occupation, occupation)]

    def businesses_of_type(self, business_type):
        """Return all business in this city of the given type.

        @param business_type: A string of the Class name representing the type of business in question.
        """
        businesses_of_this_type = [
            company for company in self.companies if company.__class__.__name__ == business_type
        ]
        return businesses_of_this_type

    def manipulate_population(self):
        """Attempt to manipulate the population of this city to reflect its true population this year."""
        if self.true_yearly_populations[self.cosmos.year] == -99:  # Minor city
            self._manipulate_population_as_a_minor_city()
        else:  # Major city (at least at one time TODO REVERT CITIES TO MINOR)
            self._manipulate_population_as_a_major_city()

    def _manipulate_population_as_a_minor_city(self):
        """Attempt to maintain a low population for this minor city."""
        if not self.residents:
            self._cause_population_growth()
        elif len(self.residents) > self.cosmos.config.desired_maximum_number_of_npcs_in_minor_cities:
            # Select a random adult in town
            if self.unemployed:
                resident_to_move = random.choice(list(self.unemployed))
            else:
                resident_to_move = random.choice([p for p in self.residents if p.adult])
            # Attempt to have them move to an underpopulated city
            underpopulated_city_to_move_to = resident_to_move.choose_new_city_to_move_to()
            if underpopulated_city_to_move_to:
                resident_to_move.move_to_new_city(
                    city=underpopulated_city_to_move_to, reason=Fate(cosmos=self.cosmos)
                )

    def _manipulate_population_as_a_major_city(self):
        """Attempt to manipulate the population of this major city to reflect its true population this year."""
        number_of_npcs_to_shoot_for = self._get_ideal_number_of_npcs_for_this_year()
        if number_of_npcs_to_shoot_for <= self.population:
            self.overpopulated = True
            self.underpopulated = False
        elif number_of_npcs_to_shoot_for > self.population:
            self.overpopulated = False
            self.underpopulated = True
        if self.underpopulated:
            self._cause_population_growth()
        elif self.overpopulated:
            self._cause_population_reduction()

    def _get_ideal_number_of_npcs_for_this_year(self):
        """Return the ideal number of NPCs that should be living in this city this year."""
        config = self.cosmos.config
        true_population_this_year = self.true_yearly_populations[self.cosmos.year]
        if true_population_this_year > 0:
            number_of_npcs_to_shoot_for = (
                config.function_to_get_desired_number_of_npcs_given_true_population_some_year(
                    true_pop=true_population_this_year
                )
            )
        else:  # elif true_population_this_year == -1:
            # This is a (one-time) major city, but we don't have data for the true population
            # this year, so just attempt to maintain the last population count on record
            years_that_have_passed_already = xrange(config.year_worldgen_begins, self.cosmos.year)
            last_population_on_record = next(
                y for y in years_that_have_passed_already if
                y in self.true_yearly_populations and self.true_yearly_populations[y] != 1
            )
            number_of_npcs_to_shoot_for = (
                config.function_to_get_desired_number_of_npcs_given_true_population_some_year(
                    true_pop=last_population_on_record
                )
            )
        return number_of_npcs_to_shoot_for

    def _cause_population_growth(self):
        """Do things that will cause the population of this city to grow."""
        if not self.vacant_lots:
            # This city is likely going to run too low on living quarters -- build an
            # apartment complex
            ApartmentComplex(city=self)
        else:
            self._have_a_new_business_start_up()

    def _cause_population_reduction(self):
        """Do things that will cause the population of this city to reduce."""
        self._have_a_business_shut_down()

    def _have_a_new_business_start_up(self):
        """Stimulate the population of this city by having a new business start up."""
        config = self.cosmos.config
        # If there's less than 30 vacant homes in this city and no apartment complex
        # yet, have one open up
        if len(self.vacant_lots) < 30 and not self.businesses_of_type('ApartmentComplex'):
            ApartmentComplex(city=self)
        else:
            all_business_types = Business.__subclasses__()
            random.shuffle(all_business_types)
            for business_type in all_business_types:
                advent, demise, min_pop = (
                    config.business_types_advent_demise_and_minimum_population[business_type]
                )
                # Check if the business type is era-appropriate
                if advent < self.cosmos.year < demise and self.population >= min_pop:
                    # Check if there aren't already too many businesses of this type in town
                    max_number_for_this_type = config.max_number_of_business_types_at_one_time[business_type]
                    if (len(self.businesses_of_type(business_type.__name__)) <
                            max_number_for_this_type):
                        # Lastly, if this is a business that only forms on a tract, make sure
                        # there is a vacant tract for it to be established upon
                        need_tract = business_type in config.companies_that_get_established_on_tracts
                        if (need_tract and self.vacant_tracts) or not need_tract:
                            # Instantiate the business and break the for loop
                            business_type(city=self)
                            break

    def _have_a_business_shut_down(self):
        """Reduce the population of this city by having a business shut down.

        This will cause its employees to be unemployed, which will likely lead to them and
        their families moving to underpopulated cities, which will at the same time be constructing
        new companies.
        """
        # Collect all private companies in this city that are not apartment complexes
        possible_shutdowns = [
            co for co in self.companies if co.private and co.__class__.__name__ not in (
                "ApartmentComplex", "HoldingCompany"
            )
        ]
        # Remove from this list companies that are the only business of their type in this city
        possible_shutdowns = [
            co for co in possible_shutdowns if len(self.businesses_of_type(co.__class__.__name__)) > 1
        ]
        if not possible_shutdowns:
            self.minimal_infrastructure = True
        else:
            # Sort by how redundant the company is, i.e., how many other companies in this city
            # are of the same type
            possible_shutdowns.sort(
                key=lambda company: len(self.businesses_of_type(company.__class__.__name__)), reverse=True
            )
            shutdown = utilities.pick_from_sorted_list(possible_shutdowns)
            shutdown.go_out_of_business(reason=Fate(cosmos=self.cosmos))

