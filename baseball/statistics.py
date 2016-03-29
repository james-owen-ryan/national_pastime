class PlayerStatistics(object):
    """A person's playing statistics over the course of a life."""

    def __init__(self, player):
        """Initialize a PlayingStatistics object."""
        self.player = player  # The player to whom these statistics pertain
        # Service
        self.games_played = []
        # Pitching
        self.innings_pitched = []
        self.pitches = []
        self.strikes = []
        self.balls = []
        self.beans = []
        self.pitching_strikeouts = []
        self.pitching_walks = []
        self.hits_allowed = []
        self.home_runs_allowed = []
        self.grand_slams_allowed = []
        self.pitching_wins = []
        self.pitching_losses = []
        # Batting
        self.batting_strikeouts = []
        self.batting_walks = []
        self.plate_appearances = []
        self.at_bats = []
        self.hits = []
        self.singles = []
        self.doubles = []
        self.triples = []
        self.home_runs = []
        self.grand_slams = []
        self.rbi = []
        self.runs = []
        self.outs = []  # Instances where a player was called out
        self.double_plays_grounded_into = []
        self.left_on_base = 0
        self.stolen_bases = []
        # Fielding
        self.putouts = []
        self.assists = []
        self.double_plays_participated_in = []
        self.triple_plays_participated_in = []
        # Career
        self.career_hits = []
        self.career_at_bats = []
        self.career_home_runs = []
        self.yearly_batting_averages = {}
        self.yearly_home_runs = {}
        self.home_run_titles = []
        self.batting_titles = []
        # Non-statistical minutiae
        self.throws = []
        self.fielding_acts = []


class UmpireStatistics(object):
    """A person's umpiring statistics over the course of a life."""

    def __init__(self, umpire):
        """Initialize an UmpireStatistics object."""
        self.umpire = umpire  # The umpire to whom these statistics pertain
        self.games_umpired = []
        self.play_at_base_calls = []
        self.fly_out_calls = []