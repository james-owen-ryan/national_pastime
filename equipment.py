from random import normalvariate as normal


class Baseball(object):

    def __init__(self):
        self.weight = normal(5.125, 0.0625)
        self.yarn_synthetic_composition = 0.0


class Bat(object):

    def __init__(self):
        self.weight = 33


class Glove(object):

    def __init__(self):
        # Fielding or pitch receiving difficulty is divided
        # by the advantage derived from the glove, so values
        # above 1.0 reduce difficulty and values below 1.0
        # increase difficulty
        self.fielding_advantage = 1.0  # TODO
        self.pitch_receiving_advantage = 0.5


class Mitt(object):

    def __init__(self):
        self.fielding_advantage = 0.5  # TODO
        self.pitch_receiving_advantage = 1.0

