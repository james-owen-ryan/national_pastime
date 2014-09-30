class PitchInterim(object):
    """A duration between pitches in which the ball is live."""

    def __init__(self):
        pass


class PlayingAction(object):

    def __init__(self, at_bat):
        # Dynamic attributes that specify game actions while the ball is in play
        self.fly_out_call_given = False  # So that multiple fly outs aren't awarded by umpire.officiate()
        self.resolved = False  # Whether the current playing action has ended
        self.result = None
        self.running_to_first = self.at_bat.batter
        self.running_to_second = self.at_bat.frame.on_first
        self.running_to_third = self.at_bat.frame.on_second
        self.running_to_home = self.at_bat.frame.on_third
        self.retreating_to_first = None
        self.retreating_to_second = None
        self.retreating_to_third = None
        self.covering_first = None
        self.covering_second = None
        self.covering_third = None
        self.covering_home = None
        self.backing_up_first = None
        self.backing_up_second = None
        self.backing_up_third = None
        self.backing_up_home = None
        self.cut_off_man = None  # Fielder positioned to act as relay on the throw