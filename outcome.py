# TODO: in the park home run


class Strike(object):

    def __init__(self, pitch, looking, foul_tip=None):
        self.pitch = pitch
        if looking:
            self.pitch.result = self
        elif not looking:
            swing = pitch.result
            swing.result = self
        elif foul_tip:
            foul_tip.result = self
        self.looking = looking
        self.foul_tip = foul_tip
        # Effect consequences
        at_bat = pitch.at_bat
        at_bat.strikes += 1
        self.strike_n = at_bat.strikes
        if at_bat.strikes == at_bat.game.rules.n_strikes_for_strikeout:
            self.result = Strikeout(at_bat=at_bat)
        else:
            self.result = None
        # Record statistics
        # pitch.pitcher.strikes.append(self)

    def __str__(self):
        if self.looking:
            return "Strike {}, looking".format(self.strike_n)
        else:
            return "Strike {}, swing and a miss".format(self.strike_n)


class Ball(object):

    def __init__(self, pitch):
        self.pitch = pitch
        self.pitch.result = self
        # Effect consequences
        at_bat = pitch.at_bat
        at_bat.balls += 1
        self.ball_n = at_bat.balls
        if at_bat.balls == at_bat.game.rules.n_balls_for_walk:
            # Base on balls
            self.result = BaseOnBalls(at_bat=at_bat)
        else:
            self.result = None
        # Record statistics
        # pitch.pitcher.balls.append(self)

    def __str__(self):
        return "Ball {}".format(self.ball_n)


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
                self.result = HitByPitch(at_bat=at_bat)
            else:
                self.result = None
        # Record statistics
        self.pitch.pitcher.beans.append(self)


class FoulBall(object):

    def __init__(self, batted_ball, anachronic_home_run=False):
        # NOTE: batted_ball may be a foul tip
        self.batted_ball = batted_ball
        batted_ball.result = self
        # Modified below, depending on context and rules
        self.strike = False
        self.result = None
        # A foul ball that is an anachronic home run is one that crosses
        # the plane of the outfield fence fair but lands in foul territory,
        # batted balls like such being deemed foul by MLB rules before 1930
        # and home runs thereafter
        self.anachronic_home_run = anachronic_home_run
        # Effect consequences
        at_bat = batted_ball.at_bat
        if batted_ball.bunt and at_bat.game.rules.foul_bunts_are_strikes:
            # Enforce foul-bunt rule
            self.strike = True
            at_bat.strikes += 1
            if at_bat.strikes == at_bat.game.rules.n_strikes_for_strikeout:
                self.result = Strikeout(at_bat=at_bat, foul_bunt=True)
        elif (not batted_ball.bunt and at_bat.strikes < 2 and
                at_bat.game.rules.fouls_are_strikes_except_on_third):
            # Enforce foul-strike rule
            self.strike = True
            at_bat.strikes += 1

    def __str__(self):
        if self.strike:
            return "Strike {}, foul ball".format(self.batted_ball.at_bat.strikes)
        else:
            return "Foul ball, no strike"


class Strikeout(object):

    def __init__(self, at_bat, foul_bunt=True):
        self.at_bat = at_bat
        at_bat.result = self  # TODO what about with dropped third strike?
        self.pitcher = at_bat.pitcher
        self.batter = at_bat.batter
        self.batter.out = True
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        self.foul_bunt = foul_bunt
        self.result = None
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
            pass
        # Record statistics
        self.batter.plate_appearances.append(at_bat)
        self.batter.at_bats.append(at_bat)
        self.pitcher.pitching_strikeouts.append(self)
        self.batter.batting_strikeouts.append(self)
        if self.decisive_pitch.caught or foul_bunt:
            self.catcher.putouts.append(self)

    def __str__(self):
        if self.looking:
            return "Strikeout, caught looking!".format(self.at_bat.strikes)
        else:
            return "Strikeout, swing and a miss!".format(self.at_bat.strikes)


class BaseOnBalls(object):

    def __init__(self, at_bat):
        self.at_bat = at_bat
        at_bat.result = self
        self.pitcher = at_bat.pitcher
        self.batter = at_bat.batter
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        self.result = None
        self.decisive_pitch = at_bat.pitches[-1]
        # Effect consequences
        at_bat.resolved = True
        if at_bat.frame.on_first and at_bat.frame.on_second and at_bat.frame.on_third:
            # Third advances and scores
            Run(frame=self.at_bat.frame, runner=at_bat.frame.on_third, batted_in_by=self.at_bat.batter)
            at_bat.frame.on_third = at_bat.frame.on_second
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        elif at_bat.frame.on_first and at_bat.frame.on_second:
            at_bat.frame.on_third = at_bat.frame.on_second
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        elif at_bat.frame.on_first:
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        else:
            at_bat.frame.on_first = self.at_bat.batter
        # Record statistics
        self.batter.plate_appearances.append(at_bat)
        self.pitcher.pitching_walks.append(self)
        self.batter.batting_walks.append(self)

    def __str__(self):
        return "Walk"


class HitByPitch(object):

    def __init__(self, at_bat):
        self.at_bat = at_bat
        at_bat.result = self
        self.pitcher = at_bat.pitcher
        self.batter = at_bat.batter
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        self.result = None
        self.pitch = at_bat.pitches[-1]
        # Effect consequences
        at_bat.resolved = True
        if at_bat.frame.on_first and at_bat.frame.on_second and at_bat.frame.on_third:
            # Third advances and scores
            Run(frame=self.at_bat.frame, runner=at_bat.frame.on_third, batted_in_by=self.at_bat.batter)
            at_bat.frame.on_third = at_bat.frame.on_second
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        elif at_bat.frame.on_first and at_bat.frame.on_second:
            at_bat.frame.on_third = at_bat.frame.on_second
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        elif at_bat.frame.on_first:
            at_bat.frame.on_second = at_bat.frame.on_first
            at_bat.frame.on_first = self.at_bat.batter
        else:
            at_bat.frame.on_first = self.at_bat.batter
        # Record statistics
        self.batter.plate_appearances.append(at_bat)
        self.pitcher.pitching_walks.append(self)
        self.batter.batting_walks.append(self)

    def __str__(self):
        return "Walk (HBP)"


class FlyOut(object):

    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        self.difficulty = batted_ball.fielding_difficulty
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.batter = self.at_bat.batter
        self.batter.out = True
        self.result = None
        self.caught_by = batted_ball.fielded_by
        if batted_ball.n_bounces:
            self.bounding = True
        else:
            self.bounding = False
        # Effect consequences
        self.at_bat.resolved = True
        self.at_bat.frame.outs += 1
        # TODO self.result = SacrificeFly()
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.outs.append(self)
        self.caught_by.putouts.append(self)

    def __str__(self):
        return "Fly out by {} ({}) at ~{} ft. distance [Difficulty: {}]".format(
            self.caught_by.last_name, self.caught_by.position, self.batted_ball.true_distance,
            round(self.difficulty, 3)
        )


class ForceOut(object):

    def __init__(self, at_bat, baserunner, base, true_call, forced_by, assisted_by):
        self.at_bat = at_bat
        self.baserunner = baserunner
        baserunner.out = True
        self.base = base
        self.true_call = true_call
        self.forced_by = forced_by
        self.assisted_by = assisted_by
        self.result = None
        if baserunner is at_bat.batter:
            at_bat.result = self  # TODO SAC-FLY choices nuances, also what about double-play??
        else:
            FieldersChoice(at_bat=at_bat, out=self)
        # Effect consequences
        baserunner.safely_on_base = False
        at_bat.resolved = True
        at_bat.frame.outs += 1
        # Record statistics
        if baserunner is at_bat.batter:
            at_bat.batter.at_bats.append(at_bat)
            at_bat.batter.plate_appearances.append(at_bat)
        self.baserunner.outs.append(self)
        self.forced_by.putouts.append(self)
        for fielder in assisted_by:
            fielder.assists.append(self)

        print "{} is forced out at {}".format(baserunner.last_name, self.base)

    def __str__(self):
        # TODO doesn't capture multiple assistants
        return "Force out at {} by {} ({}), assisted by {} ({})".format(
            self.base, self.forced_by.last_name, self.forced_by.position,
            self.assisted_by[-1].last_name, self.assisted_by[-1].position,
        )


class TagOut(object):

    def __init__(self, at_bat, baserunner, tagged_by, assisted_by):
        self.at_bat = at_bat
        self.baserunner = baserunner
        baserunner.out = True
        self.tagged_by = tagged_by
        self.assisted_by = assisted_by
        self.result = None
        if baserunner is at_bat.batter:
            at_bat.result = self  # TODO SAC-FLY choices nuances, also what about double-play??
        else:
            FieldersChoice(at_bat=at_bat, out=self)
        # Effect consequences
        baserunner.safely_on_base = False
        at_bat.resolved = True
        at_bat.frame.outs += 1
        # Record statistics
        if baserunner is at_bat.batter:  # TODO batter taking extra bases and failing nuances
            at_bat.batter.at_bats.append(at_bat)
            at_bat.batter.plate_appearances.append(at_bat)
        self.baserunner.outs.append(self)
        self.tagged_by.putouts.append(self)
        for fielder in assisted_by:
            fielder.assists.append(self)

    def __str__(self):
        # TODO doesn't capture multiple assistants
        return "Out! {} is tagged by {} ({}), assisted by {} ({})".format(
            self.baserunner, self.tagged_by.name, self.tagged_by.position,
            self.assisted_by[-1].name, self.assisted_by[-1].position
        )


class FieldersChoice(object):

    def __init__(self, at_bat, out):
        self.at_bat = at_bat
        self.out = out
        self.result = None
        at_bat.result = self
        # Record statistics
        at_bat.batter.at_bats.append(at_bat)
        at_bat.batter.plate_appearances.append(at_bat)

    def __str__(self):
        return "{} out on fielder's choice".format(self.out.baserunner.last_name)


class DroppedThirdStrike(object):

    def __init__(self, strikeout):
        self.strikeout = strikeout
        self.at_bat = strikeout.at_bat
        self.result = None  # OR??

        print 'HELP NEED DROPPED THIRD STRIKE!!!?!??!'


class Single(object):

    def __init__(self, batted_ball, true_call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.true_call = true_call
        self.beat_throw_by = None  # Modified by at_bat.enact(), if appropriate
        self.result = None
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.singles.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if self.beat_throw_by:
            if self.true_call == "Out":
                return "Single hit by {}, who was actually beat on the throw".format(
                    self.batter.name
                )
            else:
                return "Single hit by {}, who beat throw by {}".format(
                    self.batter.name, self.beat_throw_by
                )
        else:
            return "Single hit by {}".format(self.batter.name)


class Double(object):

    def __init__(self, batted_ball, true_call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.true_call = true_call
        self.beat_throw_by = None  # Modified by at_bat.enact(), if appropriate
        self.result = None
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.doubles.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if self.beat_throw_by:
            if self.true_call == "Out":
                return "Double hit by {}, who was actually beat on the throw!".format(
                    self.batter.name
                )
            else:
                return "Double hit by {}, who beat throw by {}!".format(
                    self.batter.name, self.beat_throw_by
                )
        else:
            return "Double hit by {}!".format(self.batter.name)


class Triple(object):

    def __init__(self, batted_ball, true_call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.true_call = true_call
        self.beat_throw_by = None  # Modified by at_bat.enact(), if appropriate
        self.result = None
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.triples.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if self.beat_throw_by:
            if self.true_call == "Out":
                return "Triple hit by {}, who was actually beat on the throw!".format(
                    self.batter.name
                )
            else:
                return "Triple hit by {}, who beat throw by {}!".format(
                    self.batter.name, self.beat_throw_by
                )
        else:
            return "Triple hit by {}!".format(self.batter.name)


class HomeRun(object):

    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.true_distance = batted_ball.true_distance
        self.result = None
        self.runs = 0
        # Effect consequences
        if self.at_bat.frame.on_third:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_second:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_first:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_first, batted_in_by=self.batter)
            self.runs += 1
        Run(frame=self.at_bat.frame, runner=self.batter, batted_in_by=self.batter)
        self.runs += 1
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.home_runs.append(self)
        self.pitcher.hits_allowed.append(self)
        self.pitcher.home_runs_allowed.append(self)

    def __str__(self):
        return "Home run hit by {}!".format(self.batter.name)


class AutomaticDouble(object):
    """A batted ball that bounds over the outfield fence, pending rules.

    Though this is colloquially called a 'ground-rule double', the latter
    pertains only to the peculiar ground rules of the ballpark being
    played in, while this denotes the league-wide rule that was enacted
    by MLB in 1930. Prior to that, a ball that bounded over the outfield
    fence counted as a home run. Whether such a batted ball will count as
    an automatic double or a home run in this game will depend on the
    agreed-upon rules.
    """
    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.result = None
        self.runs = 0
        # Effect consequences
        if self.at_bat.frame.on_third:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_second:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_first:
            self.at_bat.frame.on_third = self.at_bat.frame.on_first
        self.at_bat.frame.on_second = self.batter
        # Record statistics
        # TODO crazy stuff when winning run is batted in here, see
        # TODO http://baseballscoring.wordpress.com/2014/05/06/ground-rule-double-not/
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.doubles.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        return "Automatic double hit by {}!".format(self.batter.name)


class GroundRuleDouble(object):
    """A batted ball that incurs a ground rule.

    Though this term is colloquially used for what are actually
    automatic doubles, it in fact denotes only batted balls that incur
    a peculiar ground rule of the ballpark being played in. Aside from
    the semantic nuance, all effects and statistics are the same (i.e.,
    the code is the same).
    """
    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.result = None
        self.runs = 0
        # Effect consequences
        if self.at_bat.frame.on_third:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_second:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            self.runs += 1
        if self.at_bat.frame.on_first:
            self.at_bat.frame.on_third = self.at_bat.frame.on_first
        self.at_bat.frame.on_second = self.batter
        # Record statistics
        # TODO crazy stuff when winning run is batted in here, see
        # TODO http://baseballscoring.wordpress.com/2014/05/06/ground-rule-double-not/
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.doubles.append(self)
        self.pitcher.hits_allowed.append(self)


class Run(object):

    def __init__(self, frame, runner, batted_in_by):
        self.runner = runner
        self.batted_in_by = batted_in_by
        self.result = None
        # Effect consequences
        self.runner.safely_home = False
        runner.team.runs += 1
        frame.runs += 1
        # Record statistics
        runner.runs.append(self)
        batted_in_by.rbi.append(self)

        print "\n\t{} scores!\n".format(self.runner)
