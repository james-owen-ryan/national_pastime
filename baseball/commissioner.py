from career import CommissionerCareer


class Commissioner(object):
    """The baseball-commissioner layer of a person's being."""

    def __init__(self, person):
        """Initialize a Commissioner object."""
        self.person = person  # The person in whom this commissioner layer embeds
        person.commissioner = self
        self.career = CommissionerCareer(commissioner=self)