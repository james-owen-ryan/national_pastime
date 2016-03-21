import random
from random import normalvariate as normal


# TODO move cleverness, focus, ego, intuition to mind.py?


class Personality(object):
    """A person's personality."""

    def __init__(self, person):
        """Initialize a Personality object."""
        self.person = person
        # Determine five-factor personality components
        self.openness_to_experience = self._determine_base_personality_feature(feature_type="openness")
        self.conscientiousness = self._determine_base_personality_feature(feature_type="conscientiousness")
        self.extroversion = self._determine_base_personality_feature(feature_type="extroversion")
        self.agreeableness = self._determine_base_personality_feature(feature_type="agreeableness")
        self.neuroticism = self._determine_base_personality_feature(feature_type="neuroticism")
        # Determine higher-order personality components (that are important for baseball); confidence
        # values have the Big Five signal E+, N-; confidence follows a normal distribution
        # around 0.8, where 1.0 represents ideal confidence (in the sense of accurately judging
        # one's own abilities), while lower and higher values represent under- and overconfidence,
        # respectively. This trait affects estimating whether you can beat a throw on the base paths.
        # It's also a plastic trait, meaning it may change very gradually; this currently happens in
        # baseball.game.Game.effect_consequences()
        self.confidence = self._determine_higher_order_personality_trait(trait="confidence")
        # Audacity (high values have the signal E+, O+) also follows a normal distribution
        # around 0.8, where there is no ideal audacity, just that lower values will make the
        # player less likely to take risks (which may or may have paid off) and higher values will
        # make the player more likely to take risks; affects deciding whether to challenge a close
        # throw on the base paths
        self.audacity = self._determine_higher_order_personality_trait(trait="audacity")
        # Cleverness (high values have the signal O+, N-) also follows a normal distribution
        # around 1.0 -- average people have average cleverness, and the higher cleverness the better;
        # affects typical composure
        self.cleverness = self._determine_higher_order_personality_trait(trait="cleverness")
        # Focus (high values have the signal N-, C+) also follows a normal distribution
        # around 1.0 -- average people have average focus, and the higher focus the better;
        # affects ball-tracking ability, fly-ball fielding ability, ground-ball fielding
        # ability, throwing accuracy
        self.focus = self._determine_higher_order_personality_trait(trait="focus")
        # Ego (high values have the signal E+, N-, A-) also follows a normal distribution around
        # 1.0 -- average people have an average ego
        self.ego = self._determine_higher_order_personality_trait(trait="ego")
        # Intuition (high values have the signal O+, N-, N-, C+) also follows a normal
        # distribution around 1.0; this one is third-order (its components are the second-order
        # traits 'cleverness' and 'focus') -- as such, it must be derived after these have been;
        # affects the player's ability to accurately estimate things like how long a throw will take
        self.intuition = self._determine_higher_order_personality_trait(trait="intuition")
        # Interest in history currently affects how salient deceased ancestors are to a person
        self.interest_in_history = self._determine_higher_order_personality_trait(trait="interest in history")
        # Binned scores used as convenient personality hooks during Expressionist authoring
        config = person.cosmos.config
        if self.openness_to_experience > config.threshold_for_high_binned_personality_score:
            self.high_o, self.low_o = True, False
        elif self.openness_to_experience < config.threshold_for_low_binned_personality_score:
            self.high_o, self.low_o = False, True
        else:
            self.high_o, self.low_o = False, False
        if self.conscientiousness > config.threshold_for_high_binned_personality_score:
            self.high_c, self.low_c = True, False
        elif self.conscientiousness < config.threshold_for_low_binned_personality_score:
            self.high_c, self.low_c = False, True
        else:
            self.high_c, self.low_c = False, False
        if self.extroversion > config.threshold_for_high_binned_personality_score:
            self.high_e, self.low_e = True, False
        elif self.extroversion < config.threshold_for_low_binned_personality_score:
            self.high_e, self.low_e = False, True
        else:
            self.high_e, self.low_e = False, False
        if self.agreeableness > config.threshold_for_high_binned_personality_score:
            self.high_a, self.low_a = True, False
        elif self.agreeableness < config.threshold_for_low_binned_personality_score:
            self.high_a, self.low_a = False, True
        else:
            self.high_a, self.low_a = False, False
        if self.neuroticism > config.threshold_for_high_binned_personality_score:
            self.high_n, self.low_n = True, False
        elif self.neuroticism < config.threshold_for_low_binned_personality_score:
            self.high_n, self.low_n = False, True
        else:
            self.high_n, self.low_n = False, False

    def __str__(self):
        """Return string representation."""
        return "Personality of {}".format(self.person.name)

    @property
    def o(self):
        """Return this person's openness to experience."""
        return self.openness_to_experience

    @property
    def c(self):
        """Return this person's conscientiousness."""
        return self.conscientiousness

    @property
    def e(self):
        """Return this person's extroversion."""
        return self.extroversion

    @property
    def a(self):
        """Return this person's agreeableness."""
        return self.agreeableness

    @property
    def n(self):
        """Return this person's neuroticism."""
        return self.neuroticism

    @property
    def gregarious(self):
        """Return whether this person has a gregarious personality, which is a E+A+N- signal."""
        return True if self.high_e and self.high_a and self.low_n else False

    @property
    def cold(self):
        """Return whether this person has a cold personality, which is a E-A+C+ signal."""
        return True if self.low_e and self.high_a and self.high_c else False

    def _determine_base_personality_feature(self, feature_type):
        """Determine a value for a Big Five personality trait."""
        config = self.person.cosmos.config
        # Determine whether feature will be inherited
        feature_will_get_inherited = (
            self.person.biological_mother and
            random.random() < config.big_five_heritability_chance[feature_type]
        )
        # Inherit a feature value
        if feature_will_get_inherited:
            # Inherit this trait (with slight variance)
            takes_after = random.choice([self.person.biological_father, self.person.biological_mother])
            feature_value = normal(
                self._get_a_persons_feature_of_type(person=takes_after, feature_type=feature_type),
                config.big_five_inheritance_sd[feature_type]
            )
        # Generate a feature value
        else:
            takes_after = None
            # Generate from the population mean
            feature_value = normal(
                config.big_five_mean[feature_type], config.big_five_sd[feature_type]
            )
        # Clamp the value
        if feature_value < config.big_five_floor:
            feature_value = config.big_five_floor
        elif feature_value > config.big_five_cap:
            feature_value = config.big_five_cap
        # Cast the feature value as a Feature object
        feature_object = Feature(value=feature_value, inherited_from=takes_after)
        return feature_object

    def _determine_higher_order_personality_trait(self, trait):
        """Determine a higher-order personality trait by a function on this person's base personality components."""
        config = self.person.cosmos.config
        # Determine a value for the trait (this will be a float)
        function_to_determine_trait_value = config.functions_to_determine_higher_order_personality_traits[trait]
        trait_value = function_to_determine_trait_value(
            o=self.openness_to_experience, c=self.conscientiousness, e=self.extroversion,
            a=self.agreeableness, n=self.neuroticism
        )
        return trait_value

    @staticmethod
    def _get_a_persons_feature_of_type(person, feature_type):
        """Return this person's value for the given personality feature."""
        features = {
            "openness": person.personality.openness_to_experience,
            "conscientiousness": person.personality.conscientiousness,
            "extroversion": person.personality.extroversion,
            "agreeableness": person.personality.agreeableness,
            "neuroticism": person.personality.neuroticism,
        }
        return features[feature_type]

    @staticmethod
    def component_str(component_letter):
        """Return a short string indicating the value for a personality component."""
        component_value = eval('self.{}'.format(component_letter))
        if component_value > 0.7:
            return 'very high'
        elif component_value > 0.4:
            return 'high'
        elif component_value > 0.1:
            return 'somewhat high'
        elif component_value > -0.1:
            return 'neutral'
        elif component_value > -0.4:
            return 'somewhat low'
        elif component_value > -0.7:
            return 'low'
        else:
            return 'very low'


class Feature(float):
    """A particular personality feature, i.e., a value for a particular personality attribute."""

    def __init__(self, value, inherited_from):
        """Initialize a Feature object.

        @param value: A float representing the value, on a scale from -1 to 1, for this
                      particular personality feature.
        @param inherited_from: The parent from whom this personality feature was
                               inherited, if any.
        """
        super(Feature, self).__init__()
        self.inherited_from = inherited_from

    def __new__(cls, value, inherited_from):
        """Do float stuff."""
        return float.__new__(cls, value)