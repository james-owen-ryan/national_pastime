class Player(object):

    def __init__(self, city):

        self.country = city.country
        self.hometown = city
        self.location = city

        city.players.add(self)

        self.first_name = random.choice(FORENAMES)
        self.middle_name = random.choice(FORENAMES)

        if self.hometown.name == "Milwaukee":
            self.last_name = random.choice(GERMAN_SURNAMES)
        elif self.hometown.name in ["Minneapolis", "Duluth"]:
            self.last_name = random.choice(SCANDANAVIAN_SURNAMES)
        elif self.hometown.name == "Boston":
            self.last_name = random.choice(IRISH_SURNAMES)
        elif self.hometown.name == "Philadelphia":
            self.last_name = random.choice(IRISH_SURNAMES+ENGLISH_SURNAMES)
        elif self.hometown.name == "New Orleans":
            self.last_name = random.choice(FRENCH_SURNAMES)
        else:
            self.last_name = random.choice(ALL_SURNAMES)

        self.full_name = (self.first_name + ' ' + self.middle_name + ' ' +
                          self.last_name)
        self.name = self.first_name + ' ' + self.last_name

        self.alive = True
        self.dead = False

        self.retired = False
        self.team = None
        self.pos = None

        self.init_attributes()


    def init_attributes(self):

        self.prime = int(round(normal(29, 1)))

        self.hitting_abil = int(round(normal(50, 25)))
        self.power = int(round(normal(self.hitting_abil, 25)))
        self.contact = int(round(normal(self.hitting_abil, 25)))

        self.pitching_abil = int(round(normal(50, 25)))
        self.speed = int(round(normal(self.pitching_abil, 25)))
        self.control = int(round(normal(self.pitching_abil, 25)))
        # self.changeup = int(round(normal(self.pitching_abil, 25)))
        # self.curveball = int(round(normal(self.pitching_abil, 25)))

    def __str__(self):

        rep = self.name + ' (' + self.team.city.name + ')'
        return rep

    def age_v(self):

        self.age += 1

        d = self.prime - self.age

        self.power += int(round(normal(d, 1)))
        self.contact += int(round(normal(d, 1)))

        self.speed += int(round(normal(d, 1)))
        self.control += int(round(normal(d, 1)))
        # self.changeup += int(round(normal(d, 1)))
        # self.curveball += int(round(normal(d, 1)))


    def sign_with(self, team, pos):

        self.team = team
        self.pos = pos

        team.players.append(self)