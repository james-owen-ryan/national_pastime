import random
from thought import Thoughts


class Mind(object):
    """A person's mind."""

    def __init__(self, person):
        """Initialize a Mind object."""
        self.person = person  # The person to which this mind belongs
        if self.person.mother:  # Player object
            self.memory = self._init_memory()
        else:  # PersonExNihilo object
            self.memory = self._init_ex_nihilo_memory()
        self.mental_models = {}
        self.thoughts = []

    def __str__(self):
        """Return string representation."""
        return "Mind of {}".format(self.person.name)

    def _init_memory(self):
        """Determine a person's base memory capability, given their parents'."""
        config = self.person.cosmos.config
        if random.random() < config.memory_heritability:
            takes_after = random.choice([self.person.mother, self.person.father])
            memory = random.normalvariate(takes_after.mind.memory, config.memory_heritability_sd)
        else:
            takes_after = None
            memory = random.normalvariate(config.memory_mean, config.memory_sd)
        if self.person.male:  # Men have slightly worse memory (studies show)
            memory -= config.memory_sex_diff
        if memory > config.memory_cap:
            memory = config.memory_cap
        elif memory < config.memory_floor_at_birth:
            memory = config.memory_floor_at_birth
        feature_object = Feature(value=memory, inherited_from=takes_after)
        return feature_object

    def _init_ex_nihilo_memory(self):
        """Determine this person's base memory capability."""
        config = self.person.cosmos.config
        memory = random.normalvariate(config.memory_mean, config.memory_sd)
        if self.person.male:  # Men have slightly worse memory (studies show)
            memory -= config.memory_sex_diff
        if memory > config.memory_cap:
            memory = config.memory_cap
        elif memory < config.memory_floor:
            memory = config.memory_floor
        feature_object = Feature(value=memory, inherited_from=None)
        return feature_object

    def wander(self):
        """Let this mind wander."""
        a_thought = Thoughts.a_thought(mind=self)
        if a_thought:
            self.think(a_thought)

    def entertain(self, thought_prototype, evoked_by=None, provoked_by=None):
        """Entertain a thought evoked or provoked by something or someone else.

        @param thought_prototype: The pattern for this thought.
        @param evoked_by: The thing or person that/who evoked this thought, if any.
        @param provoked_by: The person who explicitly provoked this thought, if any.
        """
        rendered_thought = Thoughts.an_elicited_thought(
            mind=self, thought_prototype=thought_prototype,
            evoked_by=evoked_by, provoked_by=provoked_by
        )
        if rendered_thought:
            self.think(rendered_thought)

    def think(self, thought):
        """Think a thought."""
        self.thoughts.append(thought)
        thought.execute()


class Feature(float):
    """A feature representing a person's memory capability and metadata about that."""

    def __init__(self, value, inherited_from):
        """Initialize a Feature object.

        @param value: A float representing the value, on a scale from -1 to 1, of a
                      person's memory capability.
        @param inherited_from: The parent from whom this memory capability was
                               inherited, if any.
        """
        super(Feature, self).__init__()
        self.inherited_from = inherited_from

    def __new__(cls, value, inherited_from):
        """Do float stuff."""
        return float.__new__(cls, value)