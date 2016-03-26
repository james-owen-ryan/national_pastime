import random


class Event(object):
    """A superclass that all event subclasses inherit from."""

    def __init__(self, cosmos):
        """Initialize an Event object."""
        self.year = cosmos.year
        if self.year < cosmos.config.year_worldgen_begins:  # This event is being retconned; generate a random day
            self.month, self.day, self.ordinal_date = cosmos.get_random_day_of_year(year=self.year)
            self.time_of_day = random.choice(['day', 'night'])
            self.date = cosmos.get_date(ordinal_date=self.ordinal_date)
        else:
            self.month = cosmos.month
            self.day = cosmos.day
            self.ordinal_date = cosmos.ordinal_date
            self.time_of_day = cosmos.time_of_day
            self.date = cosmos.date
        # Also request and attribute an event number, so that we can later
        # determine the precise ordering of events that happen on the same timestep
        self.event_number = cosmos.assign_event_number(new_event=self)


class Fate(Event):
    """A catch-all event that can serve as the reason for anything in the cosmos that was forced to happen
    by top-down methods in the greater simulation (usually ones that are in service to population maintenance).
    """

    def __init__(self, cosmos):
        """Initialize a Retirement object."""
        super(Fate, self).__init__(cosmos=cosmos)

    def __str__(self):
        """Return string representation."""
        return "Fate"