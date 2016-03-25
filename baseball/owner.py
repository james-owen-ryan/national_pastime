from career import OwnerCareer


class Owner(object):
    """The baseball team-owner layer of a person's being."""

    def __init__(self, person):
        """Initialize an Owner object."""
        self.person = person  # The person in whom this commissioner layer embeds
        person.team_owner = self
        self.career = OwnerCareer(owner=self)