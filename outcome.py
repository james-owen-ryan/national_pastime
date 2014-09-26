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
        # Effect consequences
        pitch.pitcher.composure += 0.01
        # print "-- {}'s composure increased from {} to {}".format(
        #     pitch.pitcher.last_name, round(pitch.pitcher.composure-0.01, 2), round(pitch.pitcher.composure, 2)
        # )
        pitch.batter.composure -= 0.01
        # print "-- {}'s composure decreased from {} to {}".format(
        #     pitch.batter.last_name, round(pitch.batter.composure+0.01, 2), round(pitch.batter.composure, 2)
        # )
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
        pitch.pitcher.composure -= 0.008
        # print "-- {}'s composure increased from {} to {}".format(
        #     self.pitcher.last_name, round(pitch.pitcher.composure-0.01, 2), round(pitch.pitcher.composure, 2)
        # )
        pitch.batter.composure += 0.008
        # print "-- {}'s composure decreased from {} to {}".format(
        #     pitch.batter.last_name, round(pitch.batter.composure+0.01, 2), round(pitch.batter.composure, 2)
        # )
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

        print "-- Foul ball [{}]".format(batted_ball.time_since_contact)

    def __str__(self):
        if self.strike:
            return "Strike {}, foul ball".format(self.batted_ball.at_bat.strikes)
        else:
            return "Foul ball, no strike"


class Strikeout(object):

    def __init__(self, at_bat, foul_bunt=True):
        self.at_bat = at_bat
        self.at_bat.outs.append(self)
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
        if self.batter.position != "P":
            self.batter.composure -= 0.15
            print "-- {}'s composure decreased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure+0.15, 2), round(self.batter.composure, 2)
            )
        else:
            self.batter.composure -= 0.05
            print "-- {}'s composure decreased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure+0.05, 2), round(self.batter.composure, 2)
            )
        self.pitcher.composure += 0.1
        print "-- {}'s composure increased from {} to {}".format(
            self.pitcher.last_name, round(self.pitcher.composure-0.1, 2), round(self.pitcher.composure, 2)
        )
        # Record statistics
        self.batter.plate_appearances.append(at_bat)
        self.batter.at_bats.append(at_bat)
        self.pitcher.pitching_strikeouts.append(self)
        self.batter.batting_strikeouts.append(self)
        if self.decisive_pitch.caught or foul_bunt:
            self.catcher.putouts.append(self)

    def __str__(self):
        if self.looking:
            return "Strikeout, caught looking".format(self.at_bat.strikes)
        else:
            return "Strikeout, swing and a miss".format(self.at_bat.strikes)


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
        self.intentional = False  # TODO
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
        # Effect consequences
        self.batter.composure += 0.1
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.1, 2), round(self.batter.composure, 2)
        )
        if not self.intentional:
            self.pitcher.composure -= 0.1
            print "-- {}'s composure decreased from {} to {}".format(
                self.pitcher.last_name, round(self.pitcher.composure+0.1, 2), round(self.pitcher.composure, 2)
            )
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
        self.intentional = False  # TODO
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
        # Effect consequences
        self.batter.composure += 0.05
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.05, 2), round(self.batter.composure, 2)
        )
        if not self.intentional:
            self.pitcher.composure -= 0.25
            print "-- {}'s composure decreased from {} to {}".format(
                self.pitcher.last_name, round(self.pitcher.composure+0.25, 2), round(self.pitcher.composure, 2)
            )
        # Record statistics
        self.batter.plate_appearances.append(at_bat)
        self.pitcher.pitching_walks.append(self)
        self.batter.batting_walks.append(self)

    def __str__(self):
        return "Walk (HBP)"


class FlyOut(object):

    # TODO attribute calls to these

    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        self.difficulty = batted_ball.fielding_difficulty
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.outs.append(self)
        self.at_bat.result = self
        self.batter = self.at_bat.batter
        self.batter.out = True
        self.result = None
        self.fielder = batted_ball.fielded_by
        self.fielder_position = self.fielder.position
        if batted_ball.n_bounces:
            self.bounding = True
        else:
            self.bounding = False
        # Effect consequences
        batted_ball.fly_out_awarded = True
        self.at_bat.resolved = True
        self.at_bat.frame.outs += 1
        if self.at_bat.frame.outs < 3:
            for fielder in self.at_bat.fielders:
                fielder.attempting_fly_out = False
            for baserunner in self.at_bat.frame.baserunners:
                baserunner.forced_to_advance = False
                baserunner.forced_to_retreat = True
            if self.batter is batted_ball.running_to_first:
                batted_ball.running_to_first = None
            elif self.batter is batted_ball.retreating_to_first:
                batted_ball.retreating_to_first = None
            elif self.batter is batted_ball.running_to_second:
                batted_ball.running_to_second = None
            elif self.batter is batted_ball.retreating_to_second:
                batted_ball.retreating_to_second = None
            elif self.batter is batted_ball.running_to_third:
                batted_ball.running_to_third = None
            elif self.batter is batted_ball.retreating_to_third:
                batted_ball.retreating_to_third = None
            elif self.batter is batted_ball.running_to_home:
                batted_ball.running_to_home = None
        if self.at_bat.batter.position != "P":
            self.at_bat.batter.composure -= 0.05
            print "-- {}'s composure decreased from {} to {}".format(
                self.at_bat.batter.last_name, round(self.at_bat.batter.composure+0.05, 2),
                round(self.at_bat.batter.composure, 2)
            )
        else:
            self.at_bat.batter.composure -= 0.025
            print "-- {}'s composure decreased from {} to {}".format(
                self.at_bat.batter.last_name, round(self.at_bat.batter.composure+0.025, 2),
                round(self.at_bat.batter.composure, 2)
            )
        # TODO self.result = SacrificeFly()
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.outs.append(self)
        self.fielder.putouts.append(self)

        print "-- Ball caught in flight by {} ({}) at {} ft. distance [Difficulty: {}] [{}]".format(
            self.fielder.last_name, self.fielder.position, self.batted_ball.true_distance,
            round(self.difficulty, 3), batted_ball.time_since_contact
        )

    def __str__(self):
        return "Fly out by {} ({}) at {} ft. distance [Difficulty: {}]".format(
            self.fielder.last_name, self.fielder.position, self.batted_ball.true_distance,
            round(self.difficulty, 3)
        )


class ForceOut(object):

    def __init__(self, batted_ball, baserunner, base, call, forced_by):
        self.at_bat = batted_ball.at_bat
        self.at_bat.outs.append(self)
        self.baserunner = baserunner
        self.base = base
        self.call = call
        self.forced_by = forced_by
        self.assisted_by = self.at_bat.potential_assistants
        self.result = None
        if baserunner is self.at_bat.batter:
            self.at_bat.result = self  # TODO SAC-FLY choices nuances
        elif not self.at_bat.result and baserunner is not self.at_bat.batter and not baserunner.base_reached_on_hit:
            FieldersChoice(at_bat=self.at_bat, out=self)
        # Effect consequences
        baserunner.safely_on_base = False
        baserunner.out = True
        if baserunner is batted_ball.running_to_first:
            batted_ball.running_to_first = None
            if batted_ball.running_to_second:
                batted_ball.running_to_second.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_first:
            batted_ball.retreating_to_first = None
        elif baserunner is batted_ball.running_to_second:
            batted_ball.running_to_second = None
            if batted_ball.running_to_third:
                batted_ball.running_to_third.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_second:
            batted_ball.retreating_to_second = None
        elif baserunner is batted_ball.running_to_third:
            batted_ball.running_to_third = None
            if batted_ball.running_to_home:
                batted_ball.running_to_home.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_third:
            batted_ball.retreating_to_third = None
        elif baserunner is batted_ball.running_to_home:
            batted_ball.running_to_home = None
        self.at_bat.resolved = True
        self.at_bat.frame.outs += 1
        if baserunner is self.at_bat.batter:
            if self.at_bat.batter.position != "P":
                self.at_bat.batter.composure -= 0.05
                print "-- {}'s composure decreased from {} to {}".format(
                    self.at_bat.batter.last_name, round(self.at_bat.batter.composure+0.05, 2),
                    round(self.at_bat.batter.composure, 2)
                )
            else:
                self.at_bat.batter.composure -= 0.025
                print "-- {}'s composure decreased from {} to {}".format(
                    self.at_bat.batter.last_name, round(self.at_bat.batter.composure+0.025, 2),
                    round(self.at_bat.batter.composure, 2)
                )
        # Record statistics
        if baserunner is self.at_bat.batter:
            self.at_bat.batter.at_bats.append(self.at_bat)
            self.at_bat.batter.plate_appearances.append(self.at_bat)
        self.baserunner.outs.append(self)
        self.forced_by.putouts.append(self)
        for fielder in self.assisted_by:
            fielder.assists.append(self)

        print "-- {} is forced out by {} ({}); assisted by {} [{}]".format(
            baserunner.last_name, self.forced_by.last_name, self.forced_by.position,
            ', '.join("{} ({})".format(assistant.last_name, assistant.position) for assistant in self.assisted_by),
            batted_ball.time_since_contact)

    def __str__(self):
        return "Force out by {} ({}), assisted by {}".format(
            self.forced_by.last_name, self.forced_by.position,
            ', '.join("{} ({})".format(assistant.last_name, assistant.position) for assistant in self.assisted_by)
        )


class TagOut(object):

    def __init__(self, batted_ball, baserunner, call, tagged_by):
        self.at_bat = batted_ball.at_bat
        self.at_bat.outs.append(self)
        self.baserunner = baserunner
        baserunner.out = True
        self.call = call
        self.tagged_by = tagged_by
        self.assisted_by = self.at_bat.potential_assistants
        self.result = None
        if baserunner is self.at_bat.batter and not baserunner.base_reached_on_hit:
            self.at_bat.result = self  # TODO SAC-FLY choices nuances
        elif baserunner is self.at_bat.batter and baserunner.base_reached_on_hit:
            baserunner.out_on_the_throw = self
        elif not self.at_bat.result and baserunner is not self.at_bat.batter and not baserunner.base_reached_on_hit:
            FieldersChoice(at_bat=self.at_bat, out=self)
        # Effect consequences
        baserunner.safely_on_base = False
        baserunner.out = True
        if baserunner is batted_ball.running_to_first:
            batted_ball.running_to_first = None
            if batted_ball.running_to_second:
                batted_ball.running_to_second.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_first:
            batted_ball.retreating_to_first = None
        elif baserunner is batted_ball.running_to_second:
            batted_ball.running_to_second = None
            if batted_ball.running_to_third:
                batted_ball.running_to_third.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_second:
            batted_ball.retreating_to_second = None
        elif baserunner is batted_ball.running_to_third:
            batted_ball.running_to_third = None
            if batted_ball.running_to_home:
                batted_ball.running_to_home.forced_to_advance = False
        elif baserunner is batted_ball.retreating_to_third:
            batted_ball.retreating_to_third = None
        elif baserunner is batted_ball.running_to_home:
            batted_ball.running_to_home = None
        self.at_bat.resolved = True
        self.at_bat.frame.outs += 1
        # Record statistics
        if baserunner is self.at_bat.batter:  # TODO batter taking extra bases and failing nuances
            self.at_bat.batter.at_bats.append(self.at_bat)
            self.at_bat.batter.plate_appearances.append(self.at_bat)
        self.baserunner.outs.append(self)
        self.tagged_by.putouts.append(self)
        for fielder in self.assisted_by:
            fielder.assists.append(self)

        print "-- {} is tagged out by {} ({}); assisted by {} [{}]".format(
            baserunner.last_name, self.tagged_by.last_name, self.tagged_by.position,
            ', '.join("{} ({})".format(assistant.last_name, assistant.position) for assistant in self.assisted_by),
            batted_ball.time_since_contact)

    def __str__(self):
        return "Tag out by {} ({}), assisted by {}".format(
            self.tagged_by.last_name, self.tagged_by.position,
            ', '.join("{} ({})".format(assistant.last_name, assistant.position) for assistant in self.assisted_by)
        )


class DoublePlay(object):

    def __init__(self, at_bat, outs):
        self.at_bat = at_bat
        if not any(out for out in outs if type(out) is FlyOut):
            at_bat.result = self  # This will overwrite FlyOut, TagOut that put the runner out
        self.outs = outs
        self.participants = set()
        for out in outs:
            if type(out) is FlyOut:
                self.participants.add(out.fielder)
            elif type(out) is ForceOut:
                self.participants.add(out.forced_by)
                self.participants |= out.assisted_by
            elif type(out) is TagOut:
                self.participants.add(out.tagged_by)
                self.participants |= out.assisted_by
        if len(self.participants) == 1:
            self.unassisted = True
        else:
            self.unassisted = False
        # Effect consequences
        if at_bat.batter.position != "P":
            at_bat.batter.composure -= 0.15
            print "-- {}'s composure decreased from {} to {}".format(
                at_bat.batter.last_name, round(at_bat.batter.composure+0.15, 2), round(at_bat.batter.composure, 2)
            )
        else:
            at_bat.batter.composure -= 0.07
            print "-- {}'s composure decreased from {} to {}".format(
                at_bat.batter.last_name, round(at_bat.batter.composure+0.07, 2), round(at_bat.batter.composure, 2)
            )
        if self.unassisted:
            fielder = list(self.participants)[0]
            fielder.composure += 0.25
            print "-- {}'s composure increased from {} to {}".format(
                fielder.last_name, round(fielder.composure-0.25, 2), round(fielder.composure, 2)
            )
        else:
            for participant in self.participants:
                participant.composure += 0.15
            print "-- {}".format(
                '; '.join("{}'s composure increased from {} to {}".format(
                    participant.last_name, round(participant.composure-0.15, 2), round(participant.composure, 2)
                ) for participant in self.participants)
            )
        # Record statistics
        if not any(out for out in outs if type(out) is FlyOut):
            at_bat.batter.double_plays_grounded_into.append(self)
        for participant in self.participants:
            participant.double_plays_participated_in.append(self)

    def __str__(self):
        # TODO be more specific, indicating 6-4-3 or whatever
        return "Double play turned by {}".format(
            ', '.join("{} ({})".format(p.last_name, p.position) for p in self.participants)
        )


class TriplePlay(object):

    def __init__(self, at_bat, outs):
        self.at_bat = at_bat
        if not any(out for out in outs if type(out) is FlyOut):
            at_bat.result = self  # This will overwrite FlyOut, TagOut that put the runner out
        self.outs = outs
        self.participants = set()
        for out in outs:
            if type(out) is FlyOut:
                self.participants.add(out.fielder)
            elif type(out) is ForceOut:
                self.participants.add(out.forced_by)
                self.participants |= out.assisted_by
            elif type(out) is TagOut:
                self.participants.add(out.tagged_by)
                self.participants |= out.assisted_by
        if len(self.participants) == 1:
            self.unassisted = True  # TODO add this to league statistics or something special
        else:
            self.unassisted = False
        # Effect consequences
        at_bat.batter.composure -= 0.2
        print "-- {}'s composure decreased from {} to {}".format(
            at_bat.batter.last_name, round(at_bat.batter.composure+0.2, 2), round(at_bat.batter.composure, 2)
        )
        if self.unassisted:
            fielder = list(self.participants)[0]
            fielder.composure += 0.5
            print "-- {}'s composure increased from {} to {}".format(
                fielder.last_name, round(fielder.composure-0.5, 2), round(fielder.composure, 2)
            )
        else:
            for participant in self.participants:
                participant.composure += 0.3
            print "-- {}".format(
                '; '.join("{}'s composure increased from {} to {}".format(
                    participant.last_name, round(participant.composure-0.3, 2), round(participant.composure, 2)
                ) for participant in self.participants)
            )
        # Record statistics
        if not any(out for out in outs if type(out) is FlyOut):
            at_bat.batter.double_plays_grounded_into.append(self)  # This is what baseball-reference does
        for participant in self.participants:
            participant.double_plays_participated_in.append(self)
            participant.triple_plays_participated_in.append(self)

    def __str__(self):
        # TODO be more specific, indicating 6-4-3 or whatever
        return "Triple play turned by {}".format(
            ', '.join("{} ({})".format(p.last_name, p.position) for p in self.participants)
        )


class FieldersChoice(object):

    def __init__(self, at_bat, out):
        self.at_bat = at_bat
        self.out = out
        self.result = None
        at_bat.result = self
        at_bat.resolved = True
        # Effect consequences
        at_bat.batter.composure -= 0.05
        print "-- {}'s composure decreased from {} to {}".format(
            at_bat.batter.last_name, round(at_bat.batter.composure+0.05, 2), round(at_bat.batter.composure, 2)
        )
        # Record statistics
        at_bat.batter.at_bats.append(at_bat)
        at_bat.batter.plate_appearances.append(at_bat)

    def __str__(self):
        return "{} out on fielder's choice".format(self.out.baserunner.last_name)


class HitOnError(object):

    # When the batter reaches base solely because of a fielder's mistake, this is scored.
    # It doesn't count as a hit.

    def __init__(self, at_bat, error):
        self.at_bat = at_bat
        self.error = error
        self.result = None
        at_bat.result = self
        at_bat.resolved = True
        # Record statistics
        at_bat.batter.at_bats.append(at_bat)
        at_bat.batter.plate_appearances.append(at_bat)

    def __str__(self):
        return "{} reaches base on error".format(self.at_bat.baserunner.last_name)


class DroppedThirdStrike(object):

    def __init__(self, strikeout):
        self.strikeout = strikeout
        self.at_bat = strikeout.at_bat
        self.result = None  # OR??

        print 'HELP NEED DROPPED THIRD STRIKE!!!?!??!'


class Single(object):

    def __init__(self, batted_ball, call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.call = call
        self.result = None
        self.out_on_the_throw = self.batter.out_on_the_throw  # Points to TagOut object if runner is out on the throw
        # Effect consequences
        self.at_bat.pitcher.composure -= 0.05
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.05, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if not self.out_on_the_throw:
            self.batter.composure += 0.15
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure-0.15, 2), round(self.batter.composure, 2)
            )
        else:
            self.batter.composure -= 0.05
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure+0.05, 2), round(self.batter.composure, 2)
            )
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.singles.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if not self.out_on_the_throw:
            return "Single hit by {}".format(self.batter.name)
        else:
            return "Single hit by {} (out at second on the throw)".format(self.batter.name)


class Double(object):

    def __init__(self, batted_ball, call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.call = call
        self.result = None
        self.out_on_the_throw = self.batter.out_on_the_throw
        # Effect consequences
        self.at_bat.pitcher.composure -= 0.1
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.1, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if not self.out_on_the_throw:
            self.batter.composure += 0.22
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure-0.22, 2), round(self.batter.composure, 2)
            )
        else:
            self.batter.composure -= 0.05
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure+0.05, 2), round(self.batter.composure, 2)
            )
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.doubles.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if not self.out_on_the_throw:
            return "Double hit by {}".format(self.batter.name)
        else:
            return "Double hit by {} (out at third on the throw)".format(self.batter.name)


class Triple(object):

    def __init__(self, batted_ball, call):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.call = call
        self.result = None
        self.out_on_the_throw = self.batter.out_on_the_throw
        # Effect consequences
        self.at_bat.pitcher.composure -= 0.15
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.15, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if not self.out_on_the_throw:
            self.batter.composure += 0.28
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure-0.28, 2), round(self.batter.composure, 2)
            )
        else:
            self.batter.composure -= 0.05
            print "-- {}'s composure increased from {} to {}".format(
                self.batter.last_name, round(self.batter.composure+0.05, 2), round(self.batter.composure, 2)
            )
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.triples.append(self)
        self.pitcher.hits_allowed.append(self)

    def __str__(self):
        if not self.out_on_the_throw:
            return "Triple hit by {}".format(self.batter.name)
        else:
            return "Triple hit by {} (out at third on the throw)".format(self.batter.name)


class HomeRun(object):

    def __init__(self, batted_ball, call=None, inside_the_park=False):
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
        self.call = call  # For calls at the plate on in-the-park home runs
        self.inside_the_park = inside_the_park
        self.grand_slam = False
        # Effect consequences
        self.at_bat.pitcher.composure -= 0.25
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.25, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if not inside_the_park:
            if self.at_bat.frame.on_third:
                Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
                self.at_bat.frame.on_third.safely_on_base = False
                self.runs += 1
            if self.at_bat.frame.on_second:
                Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
                self.at_bat.frame.on_second.safely_on_base = False
                self.runs += 1
            if self.at_bat.frame.on_first:
                Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_first, batted_in_by=self.batter)
                self.at_bat.frame.on_first.safely_on_base = False
                self.runs += 1
            Run(frame=self.at_bat.frame, runner=self.batter, batted_in_by=self.batter)
            self.batter.safely_on_base = False
            self.runs += 1
        self.batter.composure += 0.33
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.33, 2), round(self.batter.composure, 2)
        )
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.home_runs.append(self)
        self.pitcher.hits_allowed.append(self)
        self.pitcher.home_runs_allowed.append(self)

    def __str__(self):
        if self.inside_the_park:
            if self.runs == 1:
                return "Inside-the-park home run hit by {} [{} ft]".format(self.batter.name, int(self.true_distance))
            else:
                return "{}-run inside-the-park home run hit by {} [{} ft]".format(self.runs, self.batter.name,
                                                                                  int(self.true_distance))
        else:
            if self.runs == 1:
                return "Home run hit by {} [{} ft]".format(self.batter.name, int(self.true_distance))
            else:
                return "{}-run home run hit by {} [{} ft]".format(self.runs, self.batter.name, int(self.true_distance))


class GrandSlam(object):

    def __init__(self, batted_ball, call=None, inside_the_park=False):
        self.batted_ball = batted_ball
        batted_ball.result = self
        self.at_bat = batted_ball.at_bat
        self.at_bat.result = self
        self.at_bat.resolved = True
        self.batter = batted_ball.batter
        self.pitcher = batted_ball.pitcher
        self.true_distance = batted_ball.true_distance
        self.result = None
        self.runs = 4
        self.call = call
        self.inside_the_park = inside_the_park
        self.grand_slam = True
        # Effect consequences
        self.at_bat.pitcher.composure -= 0.5
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.5, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if not inside_the_park:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_first, batted_in_by=self.batter)
            Run(frame=self.at_bat.frame, runner=self.batter, batted_in_by=self.batter)
        self.batter.composure += 0.4
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.4, 2), round(self.batter.composure, 2)
        )
        # Record statistics
        self.batter.plate_appearances.append(self.at_bat)
        self.batter.at_bats.append(self.at_bat)
        self.batter.hits.append(self)
        self.batter.home_runs.append(self)
        self.batter.grand_slams.append(self)
        self.pitcher.hits_allowed.append(self)
        self.pitcher.home_runs_allowed.append(self)
        self.pitcher.grand_slams_allowed.append(self)

    def __str__(self):
        if self.inside_the_park:
            return "Inside-the-park grand slam hit by {} [{} ft]".format(self.batter.name, int(self.true_distance))
        else:
            return "Grand slam hit by {} [{} ft]".format(self.batter.name, int(self.true_distance))


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
        self.at_bat.pitcher.composure -= 0.1
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.1, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if self.at_bat.frame.on_third:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            self.at_bat.frame.on_third.safely_on_base = False
            self.runs += 1
        if self.at_bat.frame.on_second:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            self.at_bat.frame.on_second.safely_on_base = False
            self.runs += 1
        if self.at_bat.frame.on_first:
            batted_ball.running_to_third = self.at_bat.frame.on_first
            self.at_bat.frame.on_first.safely_on_base = True
        batted_ball.running_to_second = self.batter
        self.batter.safely_on_base = True
        self.batter.composure += 0.22
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.22, 2), round(self.batter.composure, 2)
        )
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
        self.at_bat.pitcher.composure -= 0.1
        print "-- {}'s composure decreased from {} to {}".format(
            self.at_bat.pitcher.last_name, round(self.at_bat.pitcher.composure+0.1, 2),
            round(self.at_bat.pitcher.composure, 2)
        )
        if self.at_bat.frame.on_third:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_third, batted_in_by=self.batter)
            self.at_bat.frame.on_third.safely_on_base = False
            self.runs += 1
        if self.at_bat.frame.on_second:
            Run(frame=self.at_bat.frame, runner=self.at_bat.frame.on_second, batted_in_by=self.batter)
            self.at_bat.frame.on_second.safely_on_base = False
            self.runs += 1
        if self.at_bat.frame.on_first:
            batted_ball.running_to_third = self.at_bat.frame.on_first
            self.at_bat.frame.on_first.safely_on_base = True
        batted_ball.running_to_second = self.batter
        self.batter.safely_on_base = True
        self.batter.composure += 0.22
        print "-- {}'s composure increased from {} to {}".format(
            self.batter.last_name, round(self.batter.composure-0.22, 2), round(self.batter.composure, 2)
        )
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

        if batted_in_by.at_bats[-1].batted_ball:
            print "-- {} scores [{}]".format(self.runner.last_name,
                                             batted_in_by.at_bats[-1].batted_ball.time_since_contact)
        else:
            print "-- {} scores".format(self.runner.last_name)
