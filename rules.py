class Rules(object):

    def __init__(self):

        self.n_strikes_for_strikeout = 3
        self.n_balls_for_walk = 4
        self.n_fouls_for_out = None
        self.foul_bunts_are_strikes = True
        self.fouls_are_strikes_except_on_third = True
        self.hit_batter_awarded_base = False