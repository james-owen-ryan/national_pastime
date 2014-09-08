class Strike(object):

    def __init__(self, pitch):
        self.pitch = pitch
        self.pitch.result = self
        # Effect consequences
        at_bat = pitch.at_bat
        at_bat.strikes += 1
        if at_bat.strikes == at_bat.game.rules.n_strikes_for_strikeout:
            # Strikeout -- caught looking
            self.result = Strikeout(at_bat=at_bat)
        else:
            self.result = None
        # Record statistics
        pitch.pitcher.strikes.append(self)


class Ball(object):

    def __init__(self, pitch):
        self.pitch = pitch
        self.pitch.result = self
        # Effect consequences
        at_bat = pitch.at_bat
        at_bat.balls += 1
        if at_bat.balls == at_bat.game.rules.n_balls_for_walk:
            # Base on balls
            self.result = BaseOnBalls(at_bat=at_bat)
        else:
            self.result = None


class Bean(object):

    def __init__(self, pitch):
        self.pitch = pitch
        self.pitch.result = self
        self.intentional = False  # TODO
        # Effect consequences
        at_bat = pitch.at_bat
        if at_bat.game.rules.hit_batter_awarded_base:
            self.result = BaseOnBalls(at_bat=at_bat)
        else:
            at_bat.balls += 1  # TODO was this always the case?
            if at_bat.balls == at_bat.game.rules.n_balls_for_walk:
                # Base on balls
                self.result = BaseOnBalls(at_bat=at_bat)
            else:
                self.result = None


class Foul(object):

    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        # Effect consequences
        at_bat = batted_ball.at_bat
        if batted_ball.bunt and at_bat.game.rules.foul_bunts_are_strikes:
            # Enforce foul-bunt rule
            at_bat.strikes += 1
            if at_bat.strikes == at_bat.game.rules.n_strikes_for_strikeout:
                self.result = Strikeout(at_bat=at_bat, foul_bunt=True)
        elif (not batted_ball.bunt and at_bat.strikes < 2 and
                  at_bat.game.rules.fouls_are_strikes_except_on_third):
            # Enforce foul-strike rule
            at_bat.strikes += 1


class Strikeout(object):

    def __init__(self, at_bat, foul_bunt=True):
        self.at_bat = at_bat
        self.pitcher = at_bat.pitcher
        self.batter = at_bat.batter
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        self.foul_bunt = foul_bunt
        self.decisive_pitch = at_bat.pitches[-1]
        if self.decisive_pitch.call:
            self.looking = True
        else:
            self.looking = False
        # Effect consequences
        if self.decisive_pitch.caught or foul_bunt:
            at_bat.resolved = True
            at_bat.frame.outs += 1
        else:  # Dropped third strike!
            self.result = None
        # Record statistics
        self.pitcher.pitching_strikeouts.append(self)
        self.batter.batting_strikeouts.append(self)
        if self.decisive_pitch.caught or foul_bunt:
            self.catcher.putouts.append(self)


class FlyOut(object):

    def __init__(self, at_bat, caught_by):
        self.at_bat = at_bat
        self.batter = at_bat.batter
        self.caught_by = caught_by
        # Effect consequences
        at_bat.resolved = True
        at_bat.frame.outs += 1
        # Record statistics
        self.batter.outs.append(self)
        self.caught_by.putouts.append(self)


class ForceOut(object):

    def __init__(self, at_bat, baserunner, forced_by, assisted_by):
        self.at_bat = at_bat
        self.baserunner = baserunner
        self.forced_by = forced_by
        self.assisted_by = assisted_by
        # Effect consequences
        at_bat.resolved = True
        at_bat.frame.outs += 1
        # Record statistics
        self.baserunner.outs.append(self)
        self.forced_by.putouts.append(self)
        for fielder in assisted_by:
            fielder.assists.append(self)


class TagOut(object):

    def __init__(self, at_bat, baserunner, tagged_by, assisted_by):
        self.at_bat = at_bat
        self.baserunner = baserunner
        self.tagged_by = tagged_by
        self.assisted_by = assisted_by
        # Effect consequences
        at_bat.resolved = True
        at_bat.frame.outs += 1
        # Record statistics
        self.baserunner.outs.append(self)
        self.tagged_by.putouts.append(self)
        for fielder in assisted_by:
            fielder.assists.append(self)


class DroppedThirdStrike(object):

    def __init__(self, strikeout):
        self.strikeout = strikeout
        self.at_bat = strikeout.at_bat

        print 'HELP NEED DROPPED THIRD STRIKE!!!?!??!'



class BaseOnBalls(object):

    def __init__(self, at_bat):
        self.at_bat = at_bat
        self.pitcher = at_bat.pitcher
        self.batter = at_bat.batter
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        self.decisive_pitch = at_bat.pitches[-1]
        # Effect consequences
        at_bat.resolved = True
        at_bat.frame.advance_runners()
        # Record statistics
        self.pitcher.pitching_walks.append(self)
        self.batter.batting_walks.append(self)


