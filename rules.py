class Rules(object):

    def __init__(self):

        self.n_strikes_for_strikeout = 3
        self.n_balls_for_walk = 4
        self.n_fouls_for_out = None
        self.foul_bunts_are_strikes = True
        self.fouls_are_strikes_except_on_third = True
        self.hit_batter_awarded_base = True
        self.fair_ball_on_first_bounce_is_out = False
        self.foul_ball_on_first_bounce_is_out = False
        self.bound_that_leaves_park_is_home_run = False
        self.home_run_must_land_fair = False