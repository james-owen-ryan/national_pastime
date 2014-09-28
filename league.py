import random
import math
from random import normalvariate as normal

from team import Team
from season import Season


class League(object):
    
    def __init__(self, country):

        self.country = country
        self.name = self.init_name()
        while self.name in country.league_names:
            self.name = self.init_name()
        country.leagues.append(self)
        self.founded = country.year
        self.cities = []
        self.teams = []
        self.defunct = []
        self.seasons = []
            
        self.champion = None
        self.champions = []
        self.champions_timeline = []
        
        self.central = self.init_headquarters()
        
        self.init_teams()

        print ("\n\nA new baseball major league has been formed in {hq}! It's been christened the "
               "{league}, and features the following charter teams: {all_but_last}, and {last}.".format(
                    hq=self.central.name, league=self.name,
                    all_but_last=', '.join(team.name for team in self.teams[:-1]), last=self.teams[-1].name)
        )
        raw_input("")
        
        self.charter_teams = [t for t in self.teams]


    def init_name(self):
        
        prefix = random.choice(['American', 'American', 'American', 
                                'American', 'American', 'National',
                                'National', 'National', 'National',
                                'Federal', 'Federal', 'Union', 'Union', 
                                'Continental', 'Continental', 
                                'Conglomerated', 'Civil', 'United'])
        
       # if self.country.year > int(round(normal(1918,8))):
       #     sport_name = 'Baseball'
       # else:
       #     sport_name = 'Base Baseball'
            
        stem = random.choice(['League', 'Association'])
        
       # if self.country.year < int(round(normal(1880,2))):
       #     self.name = prefix + ' ' + sport_name + ' ' + suffix
        
        name = "{prefix} {stem}".format(prefix=prefix, stem=stem)
            
        return name
        

    def init_headquarters(self):
        
        n = int(round(normal(0,4)))
        while n < 1:
            n = int(round(normal(0,1)))
        
        pops = sorted([city.pop for city in self.country.cities], reverse=True)
        chosen = pops[n]
        
        headquarters = [city for city in self.country.cities if city.pop == 
                        chosen][0]
        
        return headquarters
    
    def init_teams(self):
        
        # Determine potential value of candidate cities to league, given
        # central location
        
        vals = self.evaluate_cities()
        cands = []
            
        # Enfranchise qualifying candidate cities
        
        thresh = int(math.exp(math.log(self.central.pop)*0.71))
        for city in vals:
            x = random.randint(0, thresh)
            if x < vals[city]:
                for i in range(vals[city]):
                    cands.append(city)
        number = int(round(normal(9,2)))
        for i in range(number):
            if cands:
                chosen_city = random.choice(cands)
                Team(city=chosen_city, league=self)
                while chosen_city in cands:
                    cands.remove(chosen_city)


    def __str__(self):
        
        rep = self.name
        return rep
    
    def evaluate_cities(self):
        
        vals = {}
        
        if self.country.year < 1945:
            central = self.central
            for c in [c for c in self.country.cities if c not in self.cities]:
                if (c.latitude == central.latitude and
                            c.longitude == central.longitude):
                    v = c.pop
                elif central.get_dist(c) < 1:
                    v = c.pop
                else:
                    v = int(c.pop/central.get_dist(c))
                vals[c] = v
        
        if self.country.year >= 1945:
            mean_pop = sum([c.pop for c in self.country.cities])/len(self.country.cities)
            for c in [c for c in self.country.cities if c not in self.cities]:
                v = c.pop
                if v >= mean_pop:
                    vals[c] = v
        
        return vals
    
    
    def conduct_season(self, updates=True, following=None):
        
        s = Season(league=self)
        
        if updates:
            print ('\t\n' + str(self.country.year) + ' ' + self.name + 
                   ' Champions: ' + s.champion.name + ' (' + 
                   s.champion.record + ')\n')
            raw_input ('')
            if following:
                print ('\t' + following.name + ' record: ' + following.record 
                       + '\n')
                raw_input ('')
        
        self.champion = s.champion
        self.champions.append(s.champion)
        self.champions_timeline.append(str(self.country.year) + ': ' +
                                       s.champion.name)
        
        for team in self.teams:
            team.records_timeline.append(str(self.country.year) + ': ' +
                                         team.record)
        s.champion.records_timeline[-1] += '^'
        
    def conduct_offseason(self):
        
        for team in self.teams:
            if team.cumulative_wins+team.cumulative_losses:
                team.progress()
        
        self.consider_expansion()

            
    def consider_expansion(self, to_replace=False):
        
        central = self.central
        
        vals = self.evaluate_cities()

        if not to_replace:
            ceiling = int(round(normal(13,3)))
            room = ceiling - len(self.teams)
            if room < 0:
                room = 0
        if to_replace:
            room = 45
        x = random.randint(0, 45)
        if x <= room:
            cands = []
            thresh = int(math.exp(math.log(central.pop)*0.71))
            for city in vals:
                x = random.randint(0, thresh)
                if x < vals[city]:
                    # Weight by city value
                    for i in range(vals[city]):
                        cands.append(city)
            x = random.randint(0, int(round(normal(2,0.5))))
            for i in range(x):
                if cands:
                    chosen_city = random.choice(cands)
                    Team(city=chosen_city, league=self, expansion=True)
                    while chosen_city in cands:
                        cands.remove(chosen_city)