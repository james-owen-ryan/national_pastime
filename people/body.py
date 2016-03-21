import random
from random import normalvariate as normal


# TODO implement dynamics of aging


class Body(object):
    """A person's body."""

    def __init__(self, person):
        """Initialize a Body object.

        Objects of this class hold people's physical attributes, most of which will
        be baseball-centric. Even if a person never plays a game of baseball in the
        simulation, their body will still be generated, since they may have children
        that will inherit their physical attributes, and also to support the targeted
        narrative of potentially great baseball players who never had any interest in
        actually playing the game, and thus never were.
        """
        self.person = person  # The person to which this body belongs
        # Prepare all the attributes that we'll be setting momentarily; these will
        # be instantiated as Feature attributes (that extend Float)
        self.height = None
        self.weight = None
        self.bmi = None  # Body mass index
        self.coordination = None
        self.reflexes = None
        self.agility = None
        self.hustle = None
        self.vertical = None  # Maximum jumping height in inches
        self.vertical_reach = None  # Max height (in feet) a person can reach while standing with arm stretched upward
        self.full_speed_seconds_per_foot = None
        self.full_speed_feet_per_second = None
        self.speed_home_to_first = None
        self.lefty = False  # Left-handed
        self.righty = False  # Right-handed
        # If you have parents, inherit physical attributes
        if False:  # TODO delete after inheritance implemented
        # if self.person.mother:
            self._init_inherit_physical_attributes()
        # Otherwise, generate them from scratch
        else:
            self._init_generate_physical_attributes()

    def _init_inherit_physical_attributes(self):
        """Inherit physical attributes from this person's parents."""
        mother, father = self.person.biological_mother, self.person.biological_father

    def _init_generate_physical_attributes(self):
        """Generate physical attributes for this person."""

        # TODO put all these in config and also cast them as Features

        self.height = int(normal(71, 2))
        # Determine weight, which is correlated with height
        self.weight = int(normal(self.height*2.45, self.height*0.2))
        # Determine body mass index (BMI)
        self.bmi = float(self.weight)/self.height**2 * 703
        # Determine coordination, which is correlated to BMI
        if self.bmi > 24:
            primitive_coordination = (21-(self.bmi-21))/23.
        else:
            primitive_coordination = 1.0
        self.coordination = normal(primitive_coordination, 0.1)
        # Determine reflexes, which is correlated to coordination
        base_reflexes = normal(self.coordination, self.coordination/10)
        self.reflexes = base_reflexes**0.3
        # Determine agility, which is correlated to coordination and
        # height (with 5'6 somewhat arbitrarily being the ideal height
        # for agility)
        primitive_agility = (
            self.coordination - abs((self.height-66)/66.)
        )
        self.agility = normal(primitive_agility, 0.1)
        # Determine jumping ability, which is correlated to coordination and
        # height (with 6'6 somewhat arbitrarily being the ideal height
        # for jumping)
        primitive_jumping = (
            self.coordination - abs((self.height-78)/78.)
        )
        if primitive_jumping < 0.3:
            primitive_jumping = 0.3
        self.vertical = normal(primitive_jumping**1.5 * 22, 3)
        if self.vertical < 2:
            self.vertical = 2 + random.random()*2
        # Determine the maximum height of fieldable batted balls for the player,
        # which is determined by sum of the player's vertical and vertical reach
        # (the latter being how high they can reach while standing on the ground)
        self.vertical_reach = (self.height * 1.275) / 12.0
        self.fieldable_ball_max_height = (
            self.vertical_reach + (self.vertical / 12.0)
        )
        # Determine footspeed, which is correlated to coordination and
        # height (with 6'1 somewhat arbitrarily being the ideal height
        # for footspeed) -- we do this by generating a 60-yard dash time
        # and then dividing that by its 180 feet to get a full-speed
        # second-per-foot time
        primitive_footspeed = (
            (1.5 * self.coordination) - abs((self.height-73)/73.)
        )
        diff_from_avg = primitive_footspeed - 1.21
        if diff_from_avg >= 0:
            diff_from_avg /= 2.3
            self.full_speed_seconds_per_foot = (7.3 - abs(normal(0, diff_from_avg))) / 180
        else:
            diff_from_avg /= 1.8
            self.full_speed_seconds_per_foot = (7.3 + abs(normal(0, abs(diff_from_avg)))) / 180
        #   THIS IS THE NEW ONE -- FEET PER SECOND
        self.full_speed_feet_per_second = 20 + primitive_footspeed*4.05
        # Determine baserunning speed,
        # [TODO penalize long follow-through and lefties on speed to first]
        self.speed_home_to_first = (
            (self.full_speed_seconds_per_foot*180) / (1.62 + normal(0, 0.01))
        )
        7.2 - abs(normal(0, 0.17*2))  # WTF? JOR 03-17-2015
        self.lefty, self.righty = (True, False) if random.random() < 0.1 else (False, True)
        self.hustle = normal(1.0, 0.02)


class Feature(float):
    """A feature representing a person's physical attribute and metadata about that."""

    def __init__(self, value, inherited_from):
        """Initialize a Feature object.

        @param value: A float representing the value of the physical attribute.
        @param inherited_from: The parent from whom this memory capability was
                               inherited, if any.
        """
        super(Feature, self).__init__()
        self.inherited_from = inherited_from

    def __new__(cls, value, inherited_from):
        """Do float stuff."""
        return float.__new__(cls, value)