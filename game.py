class Game(object):

    def __init__(league, host, visitor):

        self.t1 = host
        self.t2 = visitor
        self.h_runs = 0
        self.v_runs = 0
        self.i = 0

    def inning(self):

        self.i += 1


    def at_bat(self, pitcher, batter):
        x = (pitcher.speed + pitcher.control)-(batter.power + batter.contact)