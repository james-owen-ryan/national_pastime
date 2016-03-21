from outcome import FlyOut, ForceOut, TagOut, Single, Double, Triple, HomeRun, GrandSlam


class PlayAtBaseCall(object):

    def __init__(self, at_bat, umpire, call, true_call, true_difference, baserunner, base, throw=None,
                 fielder_afoot=None):
        self.umpire = umpire
        self.call = call
        self.true_call = true_call
        if call == true_call:
            self.correct = True
        else:
            self.correct = False
        self.true_difference = true_difference  # If negative, seconds baserunner beat throw by; else vice versa
        if abs(self.true_difference) > 0.1:
            self.difficulty = "Easy"
        elif abs(self.true_difference) < 0.025:
            self.difficulty = "Tough"
        else:
            self.difficulty = "Medium"
        self.baserunner = baserunner
        self.throw = throw
        # Effect consequences
        if (call == "Safe" and not at_bat.result and baserunner is at_bat.batter and
                not baserunner.advancing_due_to_error):
            # If baserunner *is* advancing due to error, AtBat.review() will score the hit and
            # no call will be attributed to it; if there is already an AtBat.result, it's because the
            # true result of the play was a FieldersChoice.
            if base == "1B":
                Single(playing_action=at_bat.playing_action, call=self)
            elif base == "2B":
                Double(playing_action=at_bat.playing_action, call=self)
            elif base == "3B":
                Triple(playing_action=at_bat.playing_action, call=self)
            elif base == "H":
                if at_bat.playing_action.at_bat.frame.bases_loaded:
                    GrandSlam(batted_ball=at_bat.playing_action.batted_ball, call=self, inside_the_park=True)
                else:
                    HomeRun(batted_ball=at_bat.playing_action.batted_ball, call=self, inside_the_park=True)
        if call == "Out":
            if throw:
                putout_by = throw.thrown_to
            else:  # elif fielder_afoot
                putout_by = fielder_afoot
            if baserunner.forced_to_advance or baserunner.forced_to_retreat:
                ForceOut(playing_action=at_bat.playing_action, baserunner=baserunner, base=base, call=self,
                         forced_by=putout_by)
            else:
                TagOut(playing_action=at_bat.playing_action, baserunner=baserunner, call=self, tagged_by=putout_by)
        # Record statistics
        umpire.career.statistics.play_at_base_calls.append(self)

        if at_bat.game.trace:
            if abs(true_difference) < 0.15:
                if self.correct:
                    print "-- Close call at {} is '{}', which umpire {} got right [{}] [{}]".format(
                        base, self.call, self.umpire.name, round(self.true_difference, 2),
                        at_bat.playing_action.batted_ball.time_since_contact
                    )
                elif not self.correct:
                    print "-- Close call at {} is '{}', which umpire {} got wrong [{}] [{}]".format(
                        base, self.call, self.umpire.name, round(self.true_difference, 2),
                        at_bat.playing_action.batted_ball.time_since_contact
                    )


class FlyOutCall(object):
    """A determination of whether a fielded ball represents a fly out or a trap."""
    # TODO fielder who thinks he made catch may not make a throw, so the runner gets a double
    def __init__(self, umpire, call, true_call, true_difference, batted_ball):
        batted_ball.fly_out_call_given = True
        self.umpire = umpire
        self.call = call
        self.true_call = true_call
        if call == true_call:
            self.correct = True
        else:
            self.correct = False
        self.true_difference = true_difference  # If negative, seconds ball landed before fielding act; else vice versa
        if abs(self.true_difference) > 0.09:
            self.difficulty = "Easy"
        elif not self.true_difference:
            self.difficulty = "Tough"
        else:
            self.difficulty = "Medium"
        self.batted_ball = batted_ball
        if batted_ball.at_bat.game.trace:
            if abs(true_difference) < 0.15:
                if self.correct:
                    print "-- Close call on the fielding act is '{}', which umpire {} got right [{}]".format(
                        self.call, self.umpire.name, batted_ball.time_since_contact
                    )
                elif not self.correct:
                    print "-- Close call on the fielding act is '{}', which umpire {} got wrong [{}]".format(
                        self.call, self.umpire.name, batted_ball.time_since_contact
                    )
        # Effect consequences
        if self.call == "Out":
            FlyOut(batted_ball=batted_ball, call=self)
        # Record statistics
        umpire.career.statistics.fly_out_calls.append(self)