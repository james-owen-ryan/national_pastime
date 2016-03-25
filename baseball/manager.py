import random
from career import ManagerCareer
from strategy import Strategy


class Manager(object):
    """The baseball-manager layer of a person's being."""

    def __init__(self, person, team):
        """Initialize a Manager object."""
        self.person = person  # The person in whom this manager layer embeds
        person.manager = self
        self.career = ManagerCareer(manager=self)
        self.team = team
        self.strategy = Strategy(owner=self)

    def decide_position_of_greatest_need(self):
        """Return the team's position of greatest need in the opinion of this manager, given their
        strategy and other concerns.
        """
        # TODO FLESH THIS OUT
        positions = ('P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF')
        positions_already_covered = {p.position for p in self.team.players}
        try:
            return next(p for p in positions if p not in positions_already_covered)
        except StopIteration:
            if self.strategy.hitting_is_more_important:
                return random.choice(positions[1:])
            else:
                return 'P'