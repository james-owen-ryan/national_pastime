from outcome import FlyOut, ForceOut, TagOut, Single, Double, Triple, HomeRun, GrandSlam


class PlayAtBaseCall(object):

    def __init__(self, umpire, call, true_call, true_difference, baserunner, throw):
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
        at_bat = throw.batted_ball.at_bat
        if (call == "Safe" and not at_bat.result and baserunner is at_bat.batter and
                not baserunner.advancing_due_to_error):
            # If baserunner *is* advancing due to error, AtBat.review() will score the hit and
            # no call will be attributed to it; if there is already an AtBat.result, it's because the
            # true result of the play was a FieldersChoice.
            if throw.base == "1B":
                Single(batted_ball=throw.batted_ball, call=self)
            elif throw.base == "2B":
                Double(batted_ball=throw.batted_ball, call=self)
            elif throw.base == "3B":
                Triple(batted_ball=throw.batted_ball, call=self)
            elif throw.base == "H":
                if throw.batted_ball.at_bat.frame.bases_loaded:
                    GrandSlam(batted_ball=throw.batted_ball, call=self, inside_the_park=True)
                else:
                    HomeRun(batted_ball=throw.batted_ball, call=self, inside_the_park=True)
        if call == "Out":
            if baserunner.forced_to_advance or baserunner.forced_to_retreat:
                ForceOut(batted_ball=throw.batted_ball, baserunner=baserunner,
                         base=throw.base, call=self, forced_by=throw.thrown_to)
            else:
                TagOut(batted_ball=throw.batted_ball, baserunner=throw.runner,
                       call=self, tagged_by=throw.thrown_to)
        # Record statistics
        umpire.play_at_base_calls.append(self)

        if abs(true_difference) < 0.15:
            if self.correct:
                print "-- Close call at {} is '{}', which umpire {} got right [{}] [{}]".format(
                    self.throw.base, self.call, self.umpire.name, round(self.true_difference, 2),
                    throw.batted_ball.time_since_contact
                )
            elif not self.correct:
                print "-- Close call at {} is '{}', which umpire {} got wrong [{}] [{}]".format(
                    self.throw.base, self.call, self.umpire.name, round(self.true_difference, 2),
                    throw.batted_ball.time_since_contact
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
            FlyOut(batted_ball=batted_ball)
        # Record statistics
        umpire.fly_out_calls.append(self)