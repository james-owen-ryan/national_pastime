import random


class Country(object):
    """A country in a baseball cosmos."""

    def __init__(self, name, cosmos):
        """Instantiate a country object."""
        self.name = name
        self.cosmos = cosmos
        self.states, self.federal_district = self._init_states_and_federal_district()
        self.capital = self.federal_district
        self.cities = []
        cosmos.countries.append(self)
        # Prepare baseball-centric attributes
        self.leagues = []  # Leagues based here

    def _init_states_and_federal_district(self):
        """Instantiate objects for all 50 states."""
        states = []
        state_names = [
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
            'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Iowa', 'Kansas', 'Kentucky',
            'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
            'Missouri', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
            'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'South Carolina',
            'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
            'West Virginia', 'Wisconsin', 'Wyoming', 'Montana', 'Nebraska', 'Rhode Island',
            'Pennsylvania', 'Illinois', 'Indiana'
        ]
        for state_name in state_names:
            states.append(State(name=state_name, country=self))
        federal_district = FederalDistrict(name="District of Columbia", country=self)
        return states, federal_district

    def __str__(self):
        return self.name

    def find(self, city_name):
        """Return city with the given name."""
        if any(c for c in self.cities if c.name == city_name):
            city = next(c for c in self.cities if c.name == city_name)
        else:
            city = None
        return city

    @property
    def companies(self):
        """Return all companies in this country."""
        companies = []
        for state in self.states + [self.federal_district]:
            companies += state.companies
        return companies

    @property
    def residents(self):
        """Return all residents of this country."""
        residents = []
        for state in self.states+[self.federal_district]:
            residents += state.residents
        return residents

    @property
    def deceased(self):
        """Return all deceased residents of this country."""
        deceased = []
        for state in self.states+[self.federal_district]:
            deceased += state.deceased
        return deceased

    @property
    def population(self):
        """Return the number of NPCs living in this country."""
        pop = sum(state.pop for state in self.states+[self.federal_district])
        return pop

    @property
    def pop(self):
        """Return the number of NPCs living in this country."""
        return self.population

    @property
    def random_person(self):
        """Return a random person living in this country."""
        return random.choice(list(self.residents))

    @property
    def free_agents(self):
        """Return all the baseball players in this country that are not under contract."""
        free_agents = {
            resident.player for resident in self.residents if resident.player and
            not resident.player.career.retired and
            not resident.player.career.team
        }
        for player in free_agents:
            if player.career.retired:
                free_agents.remove(player)
            elif player.career.team and player in player.career.team.players:
                free_agents.remove(player)
        return free_agents


class State(object):
    """A state in a country in a baseball cosmos."""

    def __init__(self, name, country):
        self.name = name
        self.cosmos = country.cosmos
        self.country = country
        self.cities = []  # Gets appended to by establish_cities, which gets called each year by Country
        # Prepare baseball-centric attributes
        self.leagues = []  # Leagues based here

    def __str__(self):
        return self.name

    @property
    def companies(self):
        """Return all residents of this state."""
        companies = []
        for city in self.cities:
            companies += list(city.companies)
        return companies

    @property
    def residents(self):
        """Return all residents of this state."""
        residents = []
        for city in self.cities:
            residents += city.residents
        return residents

    @property
    def deceased(self):
        """Return all deceased residents of this country."""
        deceased = []
        for city in self.cities:
            deceased += city.deceased
        return deceased

    @property
    def population(self):
        """Return all the NPCs living in this state."""
        pop = sum(city.pop for city in self.cities)
        return pop

    @property
    def pop(self):
        """Return all the NPCs living in this state."""
        return self.population

    @property
    def random_person(self):
        """Return a random person living in this state."""
        return random.choice(list(self.residents))

    @property
    def free_agents(self):
        """Return all the baseball players in this state that are not under contract."""
        free_agents = {
            resident.player for resident in self.residents if resident.player and
            not resident.player.career.retired and
            not resident.player.career.team
        }
        for player in free_agents:
            if player.career.retired:
                free_agents.remove(player)
            elif player.career.team and player in player.career.team.players:
                free_agents.remove(player)
        return free_agents


class FederalDistrict(State):
    """A district in a country in a baseball cosmos.

    Currently, this is a just a special class for Washington, D.C., but maybe it'll be
    useful for municipalities in other countries, too.
    """

    def __init__(self, name, country):
        super(FederalDistrict, self).__init__(name, country)