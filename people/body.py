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
        self.age_of_physical_peak = None
        self.lefty = False  # Left-handed
        self.righty = False  # Right-handed
        self.left_handed = None  # 1.0 if lefty, else 0.0 (represented as a float so that we can cast to Feature)
        self.right_handed = None
        self.hustle = None
        self.height = None
        self.weight = None
        self.adult_height = None
        self.bmi = None  # Body mass index
        self.coordination = None
        self.coordination_propensity = None
        self.reflexes_propensity = None
        self.agility_propensity = None
        self.jumping_propensity = None
        self.footspeed_propensity = None
        self.reflexes = None
        self.agility = None
        self.vertical = None  # Maximum jumping height in inches
        self.vertical_reach = None  # Max height (in feet) a person can reach while standing with arm stretched upward
        self.full_speed_seconds_per_foot = None
        self.full_speed_feet_per_second = None
        self.speed_home_to_first = None
        # If you have parents, inherit physical attributes
        if False:  # TODO delete after inheritance implemented
        # if self.person.mother:
            self._init_inherit_physical_attributes()
        # Otherwise, generate them from scratch
        else:
            self._init_generate_physical_attributes()

    def _init_inherit_physical_attributes(self):
        """Inherit physical attributes from this person's parents."""
        config = self.person.cosmos.config
        mother, father = self.person.biological_mother, self.person.biological_father
        parents = (mother.body, father.body)
        # Handedness
        if random.random() < config.heritability_of_handedness:
            takes_after = random.choice(parents)
            self.left_handed = Feature(value=takes_after.left_handed, inherited_from=takes_after)
            self.right_handed = Feature(value=takes_after.right_handed, inherited_from=takes_after)
        # Hustle
        if random.random() < config.heritability_of_hustle:
            takes_after = random.choice(parents)
            inherited_hustle = takes_after.hustle
            mutated_hustle = normal(inherited_hustle, config.hustle_mutation_sd)
            self.hustle = Feature(value=mutated_hustle, inherited_from=takes_after)
        else:
            pass  # TODO SET UP GENERATING FROM NOTHING


    def _init_generate_physical_attributes(self):
        """Generate physical attributes for this person."""
        # Prepare these now, for speedier access
        config = self.person.cosmos.config
        year = self.person.cosmos.year
        male = self.person.male
        # Determine age of physical peak, i.e., baseball prime
        self.age_of_physical_peak = config.determine_age_of_physical_peak()
        # Determine handedness
        self.lefty = True if random.random() < config.chance_of_being_left_handed else False
        self.righty = not self.lefty
        self.left_handed = 1.0 if self.lefty else 0.0
        self.right_handed = 1.0 if self.righty else 0.0
        # Determine hustle
        self.hustle = config.determine_hustle()
        # Determine adult height this person will attain, in inches
        if male:
            self.adult_height = normal(
                config.adult_male_height_mean(year=year), config.adult_male_height_sd(year=year)
            )
        else:
            self.adult_height = normal(
                config.adult_female_height_mean(year=year), config.adult_female_height_sd(year=year)
            )
        # Determine this person's BMI  TODO BMI INCREASES AS ADULTHOOD PROGRESSES
        if male:
            self.bmi = normal(
                config.young_adult_male_bmi_mean(year=year), config.young_adult_male_bmi_sd(year=year)
            )
        else:
            self.bmi = normal(
                config.young_adult_female_bmi_mean(year=year), config.young_adult_female_bmi_sd(year=year)
            )
        # Determine propensities for coordination, reflexes, agility, jumping...
        self.coordination_propensity = config.determine_coordination_propensity()
        self.reflexes_propensity = config.determine_reflexes_propensity(
            coordination_propensity=self.coordination_propensity
        )
        self.agility_propensity = config.determine_agility_propensity()
        self.jumping_propensity = config.determine_jumping_propensity()  # Number of inches added/subtracted to base
        # ...and finally footspeed propensity, which is a bit more convoluted to compute
        primitive_coordination = config.determine_primitive_coordination(bmi=self.bmi) if self.bmi > 24 else 1.0
        adult_coordination = primitive_coordination * self.coordination_propensity
        primitive_footspeed = config.determine_primitive_footspeed(
            coordination=adult_coordination, height=self.adult_height
        )
        self.footspeed_propensity = config.determine_footspeed_propensity(primitive_footspeed=primitive_footspeed)
        # Finally, fit these potentials to the person's current age
        self.develop()

    def develop(self):
        """Develop due to aging."""
        config = self.person.cosmos.config
        # Update height
        if self.person.male:
            percentage_of_adult_height_attained = (
                config.male_percentage_of_eventual_height_at_age(age=self.person.age)
            )
        else:  # Female
            percentage_of_adult_height_attained = (
                config.female_percentage_of_eventual_height_at_age(age=self.person.age)
            )
        self.height = percentage_of_adult_height_attained * self.adult_height
        # Calculate weight (by using BMI and new height)
        self.weight = (self.bmi/703.) * self.height**2
        # Evolve propensities according to their curves
        offset_from_typical_prime = config.typical_age_of_physical_peak - self.age_of_physical_peak
        age_to_fit_to_curve = self.person.age + offset_from_typical_prime
        self.coordination_propensity *= config.coordination_propensity_curve(age=age_to_fit_to_curve)
        self.reflexes_propensity = config.reflexes_propensity_curve(age=age_to_fit_to_curve)
        self.agility_propensity = config.agility_propensity_curve(age=age_to_fit_to_curve)
        self.jumping_propensity = config.jumping_propensity_curve(age=age_to_fit_to_curve)
        self.footspeed_propensity = config.footspeed_propensity_curve(age=age_to_fit_to_curve)
        # Determine coordination, which is correlated to BMI
        primitive_coordination = config.determine_primitive_coordination(bmi=self.bmi) if self.bmi > 24 else 1.0
        self.coordination = primitive_coordination * self.coordination_propensity
        # Determine reflexes, which is correlated to coordination
        primitive_reflexes = config.determine_primitive_reflexes(
            coordination=self.coordination, reflexes_propensity=self.reflexes_propensity
        )
        self.reflexes = config.determine_reflexes(primitive_reflexes=primitive_reflexes)
        # Determine agility, which is correlated to coordination and height (with 5'6 somewhat arbitrarily
        # being the ideal height for agility)
        primitive_agility = config.determine_primitive_agility(
            coordination=self.coordination, height=self.adult_height
        )
        self.agility = primitive_agility * self.agility_propensity
        # Determine jumping ability, which is correlated to coordination and height (with 6'6 somewhat
        # arbitrarily being the ideal height for jumping)
        primitive_jumping = config.determine_primitive_jumping(coordination=self.coordination, height=self.height)
        base_vertical = config.determine_base_vertical(primitive_jumping=primitive_jumping)
        self.vertical = base_vertical + self.jumping_propensity  # Notice the plus sign
        self.vertical = config.clamp_vertical(vertical=self.vertical)
        # Determined vertical (max. height of jump) and vertical reach (how high they can reach while
        # standing flat on the ground)
        self.vertical_reach = config.determine_vertical_reach(height=self.height)
        # Determine footspeed, which is correlated to coordination and height (with 6'1 somewhat arbitrarily
        # being the ideal height for footspeed) -- we do this by generating a 60-yard dash time and then
        # dividing that by its 180 feet to get a full-speed second-per-foot time, which is used frequently
        # in the on-field simulation
        primitive_footspeed = config.determine_primitive_footspeed(coordination=self.coordination, height=self.height)
        self.full_speed_seconds_per_foot = config.determine_full_speed_seconds_per_foot(
            primitive_footspeed=primitive_footspeed, footspeed_propensity=self.footspeed_propensity
        )
        # Finally, full-speed feet per second isn't derived from self.full_speed_seconds_per_foot, because
        # it's a measure of full speed on the base paths, and so it assumes 20 feet of acceleration have
        # already occurred (JOR 03-28-16: I think)
        self.full_speed_feet_per_second = config.determine_full_speed_feet_per_second(
            primitive_footspeed=primitive_footspeed
        )


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