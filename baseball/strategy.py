import random


class Strategy(object):
    """A baseball strategy developed and practiced by a baseball manager.

    I plan for this class to represent dynamically constructed baseball strategies whose
    components may be propagated between agents. For inspiration, look up 'small ball' and
    'inside baseball'.
    """

    def __init__(self, owner):
        """Initialize a Strategy object."""
        self.owner = owner
        self.pitching_is_more_important = True if random.random() < 0.5 else False
        self.hitting_is_more_important = not self.pitching_is_more_important