import random
import datetime
from utils.config import Config
from data import CityData
from geography.city import City
from geography.country import Country
from people.business import *
from people.productionist import Productionist
from baseball.classification import Class, InformalPlay

CHANCE_OF_A_DAY_BEING_SIMULATED = 0.005


class Cosmos(object):
    """A baseball cosmos."""

    def __init__(self):
        """Initialize a Cosmos object."""
        # Determine and display an official Baseball Cosmos ID :)
        self.id = self._init_cosmos_id()
        print "Preparing {self}...".format(self=self)
        # Load the config parameters
        self.config = Config()
        # Load the city data (specifies data about all cities that will eventually
        # be established in this simulation)
        self.city_data = CityData()
        # Load the NLG module for this game instance, etc.
        self.productionist = Productionist(game=self)
        self.errors = []
        self.problems = []
        # This gets incremented each time a new person is born/generated,
        # which affords a persistent ID for each person
        self.current_person_id = 0
        self.current_place_id = 0
        # Determine whether baseball curses are real in this baseball cosmos
        self.curses_are_real = random.random() < self.config.chance_baseball_curses_are_real
        # Prepare attributes relating to time
        # self.year = self.config.year_worldgen_begins
        # self.true_year = self.config.year_worldgen_begins  # True year never gets changed during retconning
        self.ordinal_date = datetime.date(*self.config.date_worldgen_begins).toordinal()  # N days since 01-01-0001
        self.year = datetime.date(*self.config.date_worldgen_begins).year
        self.true_year = self.year  # True year never gets changed during retconning
        self.month = datetime.date(*self.config.date_worldgen_begins).month
        self.day = datetime.date(*self.config.date_worldgen_begins).day
        self.time_of_day = 'day'
        self.date = self.get_date()
        # Prepare a listing of all in-game events, which will facilitate debugging later
        self.events = []
        # A game's event number allows the precise ordering of events that
        # happened on the same timestep -- every time an event happens, it requests an
        # event number from Game.assign_event_number(), which also increments the running counter
        self.event_number = -1
        # Prepare a listing of all people born on each day -- this is used to
        # age people on their birthdays; we start with (2, 29) initialized because
        # we need to perform a check every March 1 to ensure that all leap-year babies
        # celebrate their birthday that day on non-leap years
        self.birthdays = {(2, 29): set()}
        # Prepare a number that will hold a single random number that is generated daily -- this
        # facilitates certain things that should be determined randomly but remain constant across
        # a timestep, e.g., whether a person locked their door before leaving home
        self.random_number_this_timestep = random.random()
        # self.establish_setting()
        # self._sim_and_save_a_week_of_timesteps()
        self.weather = None
        # Prepare geographic listings
        self.countries = []
        self.states = []
        self.cities = []
        # Instantiate a first country
        Country(name='United States of America', cosmos=self)
        # Prepare baseball-centric attributes
        self.baseball_classifications = [
            # TODO MAKE THIS BOTTOM-UP; HAVE AGENTS NEGOTIATE TO COMPOSE/MODIFY CLASSES
            Class(cosmos=self, level='AAA'),
            InformalPlay(cosmos=self)
        ]
        self.leagues = []  # Leagues based here

    @staticmethod
    def _init_cosmos_id():
        """Randomly determine an eight-digit cosmos ID."""
        return "".join(str(int(random.random()*10)) for _ in xrange(8))

    def __str__(self):
        """Return string representation."""
        return "Baseball Cosmos {cosmos_id}".format(cosmos_id=self.id)

    @property
    def people(self):
        """Return a list of all people living in the game world."""
        return list(self.residents)

    @property
    def residents(self):
        """Return a list of all people living in the game world."""
        residents = []
        for country in self.countries:
            residents += list(country.residents)
        return residents

    @property
    def random_person(self):
        """Return a random person living in this game world."""
        random_country = random.choice(self.countries)
        return random.choice(list(random_country.residents))

    @property
    def major_league_team_nicknames(self):
        major_nicknames = set()
        for league in self.leagues:
            for team in league.teams:
                major_nicknames.add(team.nickname)
        return major_nicknames

    def assign_event_number(self, new_event):
        """Assign an event number to some event, to allow for precise ordering of events that happened same timestep.

        Also add the event to a listing of all in-game events; this facilitates debugging.
        """
        self.events.append(new_event)
        self.event_number += 1
        return self.event_number

    @staticmethod
    def get_random_day_of_year(year):
        """Return a randomly chosen day in the given year."""
        ordinal_date_on_jan_1_of_this_year = datetime.date(year, 1, 1).toordinal()
        ordinal_date = (
            ordinal_date_on_jan_1_of_this_year + random.randint(0, 365)
        )
        datetime_object = datetime.date.fromordinal(ordinal_date)
        month, day = datetime_object.month, datetime_object.day
        return month, day, ordinal_date

    def get_date(self, ordinal_date=None):
        """Return a pretty-printed date for ordinal date."""
        if not ordinal_date:
            ordinal_date = self.ordinal_date
        year = datetime.date.fromordinal(ordinal_date).year
        month = datetime.date.fromordinal(ordinal_date).month
        day = datetime.date.fromordinal(ordinal_date).day
        month_ordinals_to_names = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July",
            8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
        }
        date = "{} of {} {}, {}".format(
            # Note: for retconning, the time of day will always be whatever the actual time of day
            # is at the beginning of the true simulation ("day", I assume), but this shouldn't matter
            self.time_of_day.title(), month_ordinals_to_names[month], day, year
        )
        return date

    def progress(self, until=None):
        """Progress the cosmos until the specified date."""
        if not until:  # Progress one week
            until = self.ordinal_date + 7
        else:
            if len(until) == 1:  # Just a year was passed
                until = (until, 1, 1)
            until = self.ordinal_date + 7 if not until else datetime.date(*until).toordinal()
        while self.ordinal_date < until:
            for l in self.leagues:
                l.operate()
            self._advance_timechunk(3)

    def _advance_timechunk(self, n_timesteps=51122):
        """Simulate the passing of a chunk of time at a lower fidelity than normal."""
        for i in xrange(n_timesteps):
            self._advance_time()
            for city in self.cities:
                if random.random() < 0.03:
                    city.manipulate_population()
                if random.random() < CHANCE_OF_A_DAY_BEING_SIMULATED:
                    self._simulate_a_timestep_in_a_city(city)

    def _advance_time(self):
        """Advance time of day and date, if it's a new day."""
        self.time_of_day = "night" if self.time_of_day == "day" else "day"
        self.weather = random.choice(['good', 'bad'])
        if self.time_of_day == "day":
            self.ordinal_date += 1
            new_date_tuple = datetime.date.fromordinal(self.ordinal_date)
            if new_date_tuple.year != self.year:
                # Happy New Year
                self.true_year = new_date_tuple.year
                self.year = new_date_tuple.year
                print "Updating each city's nearest cities..."
                for city in self.cities:
                    city.set_nearest_cities()
            self.month = new_date_tuple.month
            self.day = new_date_tuple.day
            self.date = self.get_date()
            print self.date
            self._handle_any_birthdays_today()
            self._handle_any_city_establishments_today()
        else:  # Nighttime
            self.date = self.get_date()
        # Lastly, set a new random number for this timestep
        self.random_number_this_timestep = random.random()

    def _handle_any_birthdays_today(self):
        """Age any living character whose birthday is today."""
        if (self.month, self.day) not in self.birthdays:
            self.birthdays[(self.month, self.day)] = set()
        else:
            for person in self.birthdays[(self.month, self.day)]:
                if person.alive:
                    person.grow_older()
            # Don't forget leap-year babies
            if (self.month, self.day) == (3, 1):
                for person in self.birthdays[(2, 29)]:
                    if person.present:
                        person.grow_older()

    def _handle_any_city_establishments_today(self):
        """Establish any cities that have been prescribed to be established today."""
        if self.ordinal_date in self.city_data.ordinal_dates_of_city_establishment:
            for city_specification in self.city_data.ordinal_dates_of_city_establishment.get(self.ordinal_date, set()):
                City(cosmos=self, specification=city_specification)

    def _simulate_a_timestep_in_a_city(self, city):
        """Simulate a timestep in the given city."""
        print "Simulating a {} in {}...".format(self.time_of_day, city.full_name)
        # Simulate birth, death, retirement, college, and moving out of parents
        for person in list(city.residents):
            if person.pregnant and self.ordinal_date >= person.due_date:
                person.give_birth()
            if person.age > max(65, random.random() * 100):
                person.die(cause_of_death="Natural causes")
            elif person.occupation and person.age > max(65, random.random() * 100):
                person.retire()
            elif person.adult and not person.occupation:
                if person.age > 22:
                    person.college_graduate = True
            elif person.age > 18 and person not in person.home.owners:
                person.move_out_of_parents_home()
        days_since_last_simulated_day = self.ordinal_date-city.last_simulated_day
        # Reset all Relationship interacted_this_timestep attributes
        for person in list(city.residents):
            for other_person in person.relationships:
                person.relationships[other_person].interacted_this_timestep = False
        # Have people go to the location they will be at this timestep
        for person in list(city.residents):
            person.routine.enact()
        # Simulate sex  TODO sex outside out marriage
        for person in list(city.residents):
            if person.marriage and person.spouse.home is person.home:
                chance_they_are_trying_to_conceive_this_year = (
                    self.config.function_to_determine_chance_married_couple_are_trying_to_conceive(
                        n_kids=len(person.marriage.children_produced)
                    )
                )
                chance_they_are_trying_to_conceive_this_year /= CHANCE_OF_A_DAY_BEING_SIMULATED*365
                if random.random() < chance_they_are_trying_to_conceive_this_year:
                    person.have_sex(partner=person.spouse, protection=False)
        # Have people observe their surroundings, which will cause knowledge to
        # build up, and have them socialize with other people also at that location --
        # this will cause relationships to form/conduct_offseason_activity and knowledge to propagate
        for person in list(city.residents):
            if person.age > 3:
                # person.observe()
                person.socialize(missing_timesteps_to_account_for=days_since_last_simulated_day*2)
        city.last_simulated_day = self.ordinal_date

    def find_by_hex(self, hex_value):
        """Return person whose ID in memory has the given hex value."""
        int_of_hex = int(hex_value, 16)
        try:
            person = next(
                # p for p in self.city.residents | self.city.deceased | self.city.departed if
                p for p in self.people if
                id(p) == int_of_hex
            )
            return person
        except StopIteration:
            raise Exception('There is no one with that hex ID')