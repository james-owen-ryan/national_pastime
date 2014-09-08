from random import normalvariate as normal


class Baseball(object):

    def __init__(self):

        self.weight = normal(5.125, 0.0625)
        self.yarn_synthetic_composition = 0.0


class Bat(object):

    def __init__(self):

        self.weight = 33