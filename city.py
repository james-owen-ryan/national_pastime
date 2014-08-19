ENGLISH_SURNAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/english_surnames.txt','r')]

FRENCH_SURNAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/french_surnames.txt','r')]

GERMAN_SURNAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/german_surnames.txt','r')]

IRISH_SURNAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/irish_surnames.txt','r')]

SCANDANAVIAN_SURNAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/scandinavian_surnames.txt','r')]

ALL_SURNAMES = ENGLISH_SURNAMES+FRENCH_SURNAMES+GERMAN_SURNAMES+IRISH_SURNAMES+SCANDANAVIAN_SURNAMES

LATS = pickle.load(open(os.getcwd()+'/assets/city_lats.dat', 'rb'))
LONGS = pickle.load(open(os.getcwd()+'/assets/city_longs.dat', 'rb'))

pops = pickle.load(open(os.getcwd()+'/assets/city_pops.dat', 'rb'))
city_unique_names = pickle.load(
                    open(os.getcwd()+'/assets/city_unique_names.dat', 'rb'))

class City(object):

    def __init__(self, country, name):
        self.country = country
        country.cities.append(self)
        self.name = name
        self.pop = eval('pops')[self.country.year][name]
        self.lat = LATS[name]
        self.long = LONGS[name]

        self.teams = []
        self.former_teams = []
        self.champions = set()
        self.champions_timeline = []

        self.players = set()

        for i in range(self.pop * 10):
            Player(self)


    def __str__(self):

        rep = self.name + ', pop. ' + str(self.pop)
        return rep

    def get_dist(self, city):
        '''Return Pythagorean distance between city and self.'''
        lat_dist = self.lat-city.lat
        long_dist = self.long-city.long
        dist =  sqrt((lat_dist * lat_dist) + (long_dist * long_dist))
        return dist

    def progress(self):

        self.pop = eval('pops')[self.country.year][self.name]