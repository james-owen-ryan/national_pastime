COLORS = ['Blue', 'Blue', 'Blue', 'Gray', 'Gray', 'Gray', 'Red', 'Red',
          'Red', 'Brown', 'Brown', 'Brown',  'Green', 'Green', 'Orange',
          'Silver', 'Maroon', 'Black', 'Gold', 'Yellow', 'White', 'White',
          'White']

ANIMAL_NAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/animal_names_reg.txt','r')]
ANIMAL_NAMES_IRREG = [name[:-1] for name in open(
    os.getcwd()+'/corpora/animal_names_irreg.txt','r')]
GEN_TEAM_NAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/gen_team_names.txt','r')]

class Team(object):

    def __init__(self, city, league, expansion=False):

        self.city = city
        self.country = city.country
        self.league = league
        self.ortg = int(round(normal(7, 2)))
        self.ortgs = []

        self.founded = self.country.year
        self.folded = False
        self.tradition = 0
        if not expansion:
            self.charter_team = True
            self.expansion = False
        if expansion:
            self.charter_team = False
            self.expansion = True

        self.players = []

        self.wins = 0
        self.losses = 0
        self.record = '0-0'
        self.win_diffs = []

        self.pitcher = None
        self.fielders = []

        self.records_timeline = []
        self.pennants = []
        self.championships = []


        self.cumulative_wins = 0
        self.cumulative_losses = 0

        self.in_city_since = self.league.country.year

        city.teams.append(self)
        league.teams.append(self)
        league.cities.append(city)

        self.init_name()
        while self.nickname in self.country.major_nicknames:
            self.init_name()
        self.country.major_nicknames.append(self.nickname)

        # self.init_players()

        self.names_timeline = [self.name + ' ' + str(self.country.year) + '-']

        if expansion:
            print '\n {team} ({league}) have been enfranchised.'.format(team=self.name, league=self.league.name)
        # if not expansion:
        #     print '\n {team} have been enfranchised.'.format(team=self.name)

    def init_name(self):

        if self.country.year < normal(1905, 2):
            if self.city.name in self.country.city_uniques:
                x = random.randint(0, 23)
            if self.city.name not in self.country.city_uniques:
                x = random.randint(0, 14)
        else:
            if self.city.name in self.country.city_uniques:
                x = random.randint(4, 23)
            if self.city.name not in self.country.city_uniques:
                x = random.randint(4, 14)

        if x in (0, 1):
            self.nickname = random.choice(COLORS) + ' Stockings'
        if x == 2:
            self.nickname = random.choice(COLORS) + ' Legs'
        if x == 3:
            self.nickname = random.choice(COLORS) + ' Caps'
        if x == 4:
            self.nickname = random.choice(COLORS[:-6]) + 's'
        if 4 < x < 13:
            self.nickname = random.choice(ANIMAL_NAMES) + 's'
        if x == 13:
            self.nickname = random.choice(ANIMAL_NAMES_IRREG)
        if x == 14:
            self.nickname = random.choice(GEN_TEAM_NAMES) + 's'
        if x > 14:
            self.nickname = random.choice(
                                self.country.city_uniques[self.city.name]
                                         )

        if self.city.name == 'Portland (OR)':
            self.city.name = 'Portland'

        self.name = self.city.name + ' ' + self.nickname


    def init_players(self):

        # find hitters

        for p in self.city.players:
            if len(self.players) < 8:
                if p.power + p.contact > 200:
                    if p.power + p.contact in nlargest(30, set([q.power + q.contact for q in self.city.players])):
                        if not p.team:
                            p.sign_with(self, pos='F')
                            self.fielders.append(p)

        # find pitcher

        for p in self.city.players:
            if len(self.players) < 9:
                if p.speed + p.control > 200:
                    if p.speed + p.control in nlargest(30, set([q.speed + q.control for q in self.city.players])):
                        if not p.team:
                            p.sign_with(self, pos='P')
                            self.pitcher = p

        self.batting_order = sorted(
                self.players, key=lambda x: x.contact+x.power, reverse=True)


    def progress(self):

        self.ortgs.append(self.ortg)
        self.win_diffs.append(self.wins-self.losses)
        self.ortg = int(round(normal(self.ortg, 1)))
        x = random.randint(0, 2)
        if x == 1:
            # Regress team offensive rating to mean
            d = 7-self.ortg
            y = random.randint(0, fabs(d))
            if d < 0:
                n = int(round(normal(-y, 1)))
            if d > 0:
                n = int(round(normal(y, 1)))
            if d == 0:
                x = random.randint(0, 1)
                if x == 0:
                    n = int(round(normal(-y, 1)))
                if x == 1:
                    n = int(round(normal(y, 1)))
            self.ortg += n

        self.tradition = (
            (1 + len([c for c in self.championships if c > self.in_city_since])) *
            (self.country.year-self.in_city_since))

        if self.cumulative_wins + self.cumulative_losses:
            # Make sure expansions don't already consider folding, relocation
            self.consider_folding()
            if not self.folded:
                self.consider_relocation()


    def consider_folding(self):

        if (float(self.cumulative_wins)/(
                  self.cumulative_wins+self.cumulative_losses)
            < .45):
            if (self.country.year-self.league.founded <
                int(round(normal(25,2)))):
                y = random.randint(0, self.country.year-self.league.founded)
                if y == 0:
                    n_teams = len(self.league.teams)
                    self.fold()
                    # League will consider expansion more than usual to
                    # replace folded team
                    self.league.consider_expansion(to_replace=True)


    def consider_relocation(self):

        fanbase_memory = int(round(normal(27, 5)))
        # Newer teams will not relocate, but only will possibly fold, since
        # they would have no more value to another city than an expansion
        if self.country.year-self.in_city_since > fanbase_memory:
            if (not self.championships or
                self.country.year-self.championships[-1] > fanbase_memory):
                # Check if averaging losing season for duration of
                # fanbase memory and prior season losing season
                if (sum([d for d in self.win_diffs[-fanbase_memory:]]) /
                    fanbase_memory < 0 and self.win_diffs[-1] < 0):
                    # Some teams will never move
                    if self.tradition >= int(round(normal(200, 15))):
                        x = random.randint(0, self.tradition/4)
                    else:
                        x = random.randint(0,3)
                    if x == 0:
                        cands = []
                        vals = self.league.evaluate_cities()
                        for city in vals:
                            for i in range(vals[city]):
                                cands.append(city)
                        if cands:
                            self.relocate(city=random.choice(cands))


    def relocate(self, city):

        print (self.name + ' (' + self.league.name +
               ') have relocated to become the...')
        self.city.teams.remove(self)
        self.city.former_teams.append(self)
        self.league.cities.remove(self.city)
        self.league.cities.append(city)
        self.city = city
        city.teams.append(self)

        self.in_city_since = self.league.country.year

        x = random.randint(0,10)
        if x < 8:
            self.country.major_nicknames.remove(self.nickname)
            self.init_name()
            while self.nickname in self.country.major_nicknames:
                self.init_name()
            self.country.major_nicknames.append(self.nickname)
        else:
            self.name = self.city.name + ' ' + self.nickname

        self.names_timeline[-1] = self.names_timeline[-1] + str(self.country.year)
        self.names_timeline.append(self.name + ' ' + str(self.country.year) + '-')

        raw_input('\t' + self.name + ' ')


    def fold(self):

        raw_input('\n' + self.name + ' (' + self.league.name +
                  ') have folded. ')
        self.city.teams.remove(self)
        self.city.former_teams.append(self)
        self.league.teams.remove(self)
        self.league.cities.remove(self.city)
        if self.country.year == self.founded:
             self.names_timeline[-1][:-1] += ' (folded)'
        else:
            self.names_timeline[-1] += str(self.country.year) + ' (folded)'
        self.league.defunct.append(self)
        self.country.major_nicknames.remove(self.nickname)

        self.folded = True


    def __str__(self):

        rep = self.name
        return rep