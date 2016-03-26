class Mood(object):
    """A person's mood.

    Mood attributes may have base values that they attract to (i.e., that they regress
    to naturally over time, if not inhibited), but they are dynamic and can shift both
    gradually and sharply.
    """

    def __init__(self, person):
        """Initialize a Mood object."""
        self.person = person  # The person to whom this mood belongs
        # Composure is a dynamic confidence measure that can change over the course
        # of a baseball game or more gradually over longer stretches of time; it works as a feedback
        # loop on player performance (i.e., better playing boosts composure and better composure yields
        # better playing, and vice versa with negative trending); affects fielding, swing timing; is
        # increased by impressive acts, good plate-appearance outcomes; is decreased by fielding bloopers,
        # bad plate-appearance outcomes
        self.base_composure = self.person.cosmos.config.set_base_composure(
            confidence=self.person.personality.confidence, focus=self.person.personality.focus
        )
        # To start, set the person's current composure to be their base composure
        self.composure = self.base_composure

    def __str__(self):
        """Return string representation."""
        return "Mood of {}".format(self.person.name)

    def clamp_composure(self):
        """Clamp composure into a specific range."""
        config = self.person.cosmos.config
        min_composure, max_composure = config.min_composure, config.max_composure
        self.composure = max(min_composure, min(self.composure, max_composure))

    def long_for_family(self):
        """Long for your family."""
