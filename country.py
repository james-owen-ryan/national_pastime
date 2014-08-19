class Country(object):
    """A country in a baseball-centric game world."""

    def __init__(self):
        """Instantiate a country object."""
        self.name = 'United States of America'
        self.year = year
        self.cities = []
        self.leagues = []
        self.league_names = []
        # Nicknames for major league teams, used to prevent duplicates
        self.major_nicknames = []

        self.champions = []
        self.champions_timeline = []

        for name in [n for n in set([c for c in eval('pops')[year]])]:
            City(country=self, name=name)

        y = [year for year in city_unique_names]
        y.append(self.year)
        y.sort()
        most_recent = y[y.index(self.year)-1]
        self.city_uniques = city_unique_names[most_recent]

        # for i in range(int(round(normal(1, 0.35)))):
        for i in xrange(1):
            League(country=self)

    def __str__(self):

        rep = self.name
        return rep

    def progress(self, following=None):

        if len(self.leagues) == 0:
            x = random.randint(0,2)
            if x == 0:
                League(self)
        if len(self.leagues) == 1:
            x = random.randint(0,19)
            if x == 0:
                League(self)

        for l in self.leagues:
            l.conduct_season(following=following)

        if len(self.leagues) == 2:
            l1 = self.leagues[0]
            l2 = self.leagues[1]

            # Print marquee
            matchup = l1.champion.name + ' vs. ' + l2.champion.name
            print '\n\t' + '#' * (len(matchup) + 4)
            print ('\t' + ' '*((((len(matchup)+4)-17)/2)+1) + str(self.year)
                   + ' World Series' + ' '*((((len(matchup)+4)-17)/2)+1))
            print '\t  ' + matchup
            print '\t' + '#' * (len(matchup) + 4) + '\n'

            # Alternate World Series home field advantage each year
            if self.year % 2 == 0:
                l1.seasons[-1].sim_world_series(adv=l1.champion,
                                                dis=l2.champion)
            if self.year % 2 == 1:
                l2.seasons[-1].sim_world_series(adv=l2.champion,
                                                dis=l1.champion)

        if len(self.leagues) == 1:
            self.champion = self.leagues[0].champion
            self.champions.append(self.leagues[0].champion)
            self.champions_timeline.append(str(self.year) + ': ' +
                                           self.leagues[0].champion.name)
            self.leagues[0].champion.records_timeline[-1] += '*'

        if self.champion:
            self.champion.city.champions.add(self.champion)
            self.champion.city.champions_timeline.append(str(self.year) +
                                                  ': ' + self.champion.name)

        self.year += 1

        for l in self.leagues:
            l.conduct_offseason()

        y = [year for year in city_unique_names]
        y.append(self.year)
        y.sort()
        most_recent = y[y.index(self.year)-1]
        self.city_uniques = city_unique_names[most_recent]

        for city in self.cities:
            try:
                city.progress()
            except KeyError:
                pass