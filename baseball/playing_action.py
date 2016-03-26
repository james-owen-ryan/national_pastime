from outcome import Run


# IDEA: HAVE EVERY UNIT OF ACTION THAT OCCURS IN THIS SIMULATION BE ASSOCIATED WITH
# AN 'EXPRESSION' OBJECT, WHICH STANDS FOR AN EXPRESSION OF A PLAYER'S SKILL, STYLE,
# INTELLECT, ETC., THAT PROJECTS FROM THE PLAYER'S EXECUTION OF THAT UNIT OF ACTION.
# SO ANYTIME A PLAYER DOES SOMETHING, THEY'RE BLASTING OUT EXPRESSIONS OF THEIR
# UNDERLYING SKILL, ETC., AND PEOPLE IN THE STANDS AND MANAGERS AND SCOUTS ETC. CAN
# DISCERN THESE EXPRESSIONS (WITH VARYING SKILLS, E.G., SCOUTS WOULD BE BETTER AND
# BETTER SCOUTS WOULD BE BETTER YET). NOT SURE HOW TO REPRESENT THE EXPRESSIONS, BUT
# SOMETHING NICE AND MODULAR -- MAYBE TUPLES (ATTRIBUTE, MEAN, VARIANCE)? MIGHT WANT
# TO GO BELIEF FACET ROUTE, BUT I KIND OF WANT TO GUT THAT.


class PlayingAction(object):

    def __init__(self, batted_ball):
        self.batted_ball = batted_ball
        self.at_bat = batted_ball.at_bat
        self.batter = self.at_bat.batter
        self.baserunners = self.at_bat.frame.baserunners
        self.fielders = self.at_bat.fielders
        self.umpire = self.at_bat.game.umpire
        self.resolved = False  # Whether the current playing action has ended
        self.result = None
        # This is used so that so that fielder.decide_immediate_goal() is called for
        # each fielder in the correct order -- e.g., the center fielder must be called
        # after both the left fielder and right fielder, because what he decides to do
        # will depend on what they already decided to do
        self.fielder_control_sequence = (
            self.at_bat.fielders[2:7] + [self.at_bat.fielders[-1], self.at_bat.fielders[-2]] + self.at_bat.fielders[:2]
        )
        # Dynamic attributes that change during the simulation
        self.throws = []
        self.throw = None
        self.potential_assistants = set()
        self.fielder_afoot_for_putout = None
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
        # Simulate the playing action
        # self._transpire()

    def enact(self):
        batted_ball = self.batted_ball
        self.throw = None
        # Fielders read the batted ball and decide immediate goals
        batted_ball.get_read_by_fielders()
        if self.at_bat.game.trace:
            print "-- {}; Oblig: {} [0.0]".format(batted_ball, batted_ball.obligated_fielder.position)
        if self.at_bat.game.radio_announcer:
            self.at_bat.game.radio_announcer.call_batted_ball(batted_ball=batted_ball)
        for fielder in self.fielder_control_sequence:
            fielder.decide_immediate_goal(playing_action=self)
        if self.at_bat.game.trace:
            self.enumerate_defensive_responsibilities()
        for _ in xrange(4):
            batted_ball.time_since_contact += 0.1
            # While defensive players and baserunners are reading the ball,
            # it starts moving and the batter starts running to first
            # (since players have a flat-rate home-to-first speed,
            # the delay dut to their follow-through, etc., is already
            # factored in), and any baserunners that have already taken off
            # keep advancing
            batted_ball.move()
            self.batter.baserun(playing_action=self)
            for baserunner in self.baserunners:
                if baserunner.took_off_early:
                    baserunner.baserun(playing_action=self)
        while not self.resolved:
            assert batted_ball.time_since_contact < 100, "Playing action has fallen into infinite loop."
            if self.at_bat.game.debug:
                self.report_baserunner_progress()
            batted_ball.time_since_contact += 0.1
            if not batted_ball.fielded_by:
                batted_ball.move()
            self.progress_all_baserunners()
            for fielder in self.fielders:
                fielder.act(batted_ball=batted_ball)
            if not self.throw or self.fielder_afoot_for_putout:
                # If there's a fielder with a chance, and the ball hasn't been fielded
                # yet, and that player is not reorienting from a prior fielding miss,
                # simulate the fielding attempt
                if not batted_ball.fielded_by and batted_ball.fielder_with_chance:
                    if batted_ball.fielder_with_chance.reorienting_after_fielding_miss > 0:
                        batted_ball.fielder_with_chance.reorienting_after_fielding_miss -= 0.1
                    if batted_ball.fielder_with_chance.reorienting_after_fielding_miss <= 0:
                        # Attempt to field the ball
                        batted_ball.fielder_with_chance.field_ball(batted_ball=batted_ball)
                        if not batted_ball.fielded_by:
                            # ** Defensive player didn't field the ball cleanly **
                            # TODO may be scored as error, and then all the statistical nuances there
                            if batted_ball.bobbled:
                                pass  # Player will attempt to field ball again after reorienting
                            elif not batted_ball.bobbled:
                                # Batted ball will continue on its trajectory, so players need to
                                # reassess whether and how they may attempt to field it
                                batted_ball.get_reread_by_fielders()
                            for baserunner in self.at_bat.frame.baserunners + [self.batter]:
                                # if error:
                                #       baserunner.advancing_due_to_error = True
                                if (not baserunner.baserunning_full_speed and
                                        (batted_ball.bobbled or
                                         not any(f for f in self.fielders if f.attempting_fly_out))):
                                    # (Note on above if statement: It's possible a fielder backing up
                                    # the catch will somehow himself be making a fly out attempt now,
                                    # in which case the baserunners should keep tentatively advancing)
                                    baserunner.estimate_whether_you_can_beat_throw(playing_action=self)
                                    if (baserunner.believes_he_can_beat_throw or
                                            baserunner.forced_to_advance):
                                        # You weren't baserunning full-speed, but you will start now
                                        baserunner.safely_on_base = False
                                        baserunner._decided_finish = False
                                        baserunner.will_round_base = False
                                        baserunner.percent_to_base = 0.0
                                        baserunner.baserun(playing_action=self)
                                    else:
                                        # Don't retreat already or stay on base -- keep tentatively
                                        # advancing in case there is another fielding gaffe
                                        if self.at_bat.game.trace:
                                            print (
                                                "-- {} still doesn't believe he can beat the throw, but "
                                                "will tentatively advance to the next base in case of "
                                                "another fielding gaffe [{}]"
                                            ).format(
                                                baserunner.person.last_name, batted_ball.time_since_contact
                                            )
                                        baserunner.safely_on_base = False
                                        baserunner.tentatively_baserun(playing_action=self)
                            batted_ball.bobbled = False  # Reset to allow consideration of future bobbles
                        elif batted_ball.fielded_by:
                            for baserunner in self.at_bat.frame.baserunners + [self.batter]:
                                if baserunner.forced_to_advance:
                                    # The fielder *was* attempting a fly out, but they fielded it
                                    # it in a way that wasn't called a fly out, e.g., off the outfield
                                    # wall or with a trap -- in this case, you were tentatively baserunning
                                    # waiting for resolution of the fielding attempt, but now you need to
                                    # baserun full speed, because you're forced to advance
                                    baserunner.baserun(playing_action=self)
                                elif baserunner.tentatively_baserunning:
                                    # You are not forced to advance, but we're inching along to make sure
                                    # a major fielding gaffe wouldn't allow you to advance -- no such
                                    # gaffe occurred, so retreat back now before you get nabbed
                                    baserunner.retreat(playing_action=self)
                # If the ball has been fielded and the fielder hasn't decided his throw
                # yet, have him decide his throw and then instantiate the throw
                elif batted_ball.fielded_by:
                    # elif here so that the umpire gets a timestep to make a call
                    # as to whether it's a fly out or a trap, if necessary
                    batted_ball.fielded_by.decide_throw_or_on_foot_approach_to_target(playing_action=self)
                    if batted_ball.fielded_by.will_throw:
                        self.throw = batted_ball.fielded_by.throw(playing_action=self)
            if self.throw and not self.throw.reached_target:
                self.throw.move()
            if self.throw and self.throw.reached_target and self.throw.resolved:
                self.throw.thrown_to.decide_throw_or_on_foot_approach_to_target(playing_action=self)
                if self.throw.thrown_to.will_throw:
                    self.throw = self.throw.thrown_to.throw(playing_action=self)
            # If the throw was in anticipation of an advancing runner and it has
            # reached its target, resolve the play at the plate
            elif self.throw and self.throw.reached_target and not self.throw.resolved:
                if self.at_bat.game.trace:
                    print "-- Throw has reached {} ({}) [{}]".format(
                        self.throw.thrown_to.person.last_name, self.throw.thrown_to.position,
                        batted_ball.time_since_contact
                    )
                self.throw.resolved = True
                if self.throw.runner:
                    self.umpire.call_play_at_base(
                        playing_action=self, baserunner=self.throw.runner, base=self.throw.base, throw=self.throw
                    )
                elif not self.throw.runner:
                    if self.throw.thrown_to is not self.cut_off_man:
                        self.resolved = True
            elif self.fielder_afoot_for_putout and self.fielder_afoot_for_putout[0].at_goal:
                if self.at_bat.game.trace:
                    print "-- {} has reached {} [{}]".format(
                        self.fielder_afoot_for_putout[0].person.last_name, self.fielder_afoot_for_putout[-1],
                        batted_ball.time_since_contact
                    )
                self.umpire.call_play_at_base(
                    playing_action=self, baserunner=self.fielder_afoot_for_putout[1],
                    base=self.fielder_afoot_for_putout[2], fielder_afoot=self.fielder_afoot_for_putout[0]
                )
                self.fielder_afoot_for_putout[0].decide_throw_or_on_foot_approach_to_target(playing_action=self)
                if self.fielder_afoot_for_putout[0].will_throw:
                    self.throw = self.fielder_afoot_for_putout[0].throw(playing_action=self)
                self.fielder_afoot_for_putout = None
            self.umpire.officiate(playing_action=self)

    def enumerate_defensive_responsibilities(self):
        print "\n"
        print "- Playing the ball: {}".format(
            next(f for f in self.at_bat.fielders if f.playing_the_ball).position
        )
        print "- Backing up the catch: {}".format(
            ', '.join(f.position for f in self.at_bat.fielders if f.backing_up_the_catch))
        if self.cut_off_man:
            print "- Cut-off man: {}".format(self.cut_off_man.position)
        else:
            print "- Cut-off man: None"
        if self.covering_first:
            print "- Covering first: {}".format(self.covering_first.position)
        else:
            print "- Covering first: None (prob. 1B is going for clear foul ball)"
        if self.covering_second:
            print "- Covering second: {}".format(self.covering_second.position)
        else:
            print "- No one is currently covering second! Check to make sure SS ends up doing so."
        if self.covering_third:
            print "- Covering third: {}".format(self.covering_third.position)
        else:
            print "- Covering third: None (prob. 3B is going for clear foul ball)"
        print "- Covering home: {}".format(self.covering_home.position)
        if self.backing_up_first:
            print "- Backing up first: {}".format(self.backing_up_first.position)
        else:
            print "- Backing up first: None"
        if self.backing_up_second:
            print "- Backing up second: {}".format(self.backing_up_second.position)
        else:
            print "- Backing up second: None"
        if self.backing_up_third:
            print "- Backing up third: {}".format(self.backing_up_third.position)
        else:
            print "- Backing up third: None"
        if self.backing_up_home:
            print "- Backing up home: {}".format(self.backing_up_home.position)
        else:
            print "- Backing up home: None"
        print "\n"

    def report_baserunner_progress(self):
        running_to_first = self.running_to_first or self.retreating_to_first
        if running_to_first:
            print "{} is {}% to first".format(
                running_to_first.person.last_name, int(round(running_to_first.percent_to_base*100))
            )
        running_to_second = self.running_to_second or self.retreating_to_second
        if running_to_second:
            print "{} is {}% to second".format(
                running_to_second.person.last_name, int(round(running_to_second.percent_to_base*100))
            )
        running_to_third = self.running_to_third or self.retreating_to_third
        if running_to_third:
            print "{} is {}% to third".format(
                running_to_third.person.last_name, int(round(running_to_third.percent_to_base*100))
            )
        running_to_home = self.running_to_home
        if running_to_home:
            print "{} is {}% to home".format(
                running_to_home.person.last_name, int(round(running_to_home.percent_to_base*100))
            )

    def progress_all_baserunners(self):
        # If there are less than two outs and there is potential for a fly out,
        # baserunners will tentatively advance on the base paths, while the
        # batter-runner will run it out to first regardless
        if self.at_bat.frame.outs != 2 and any(f for f in self.fielders if f.attempting_fly_out):
            for baserunner in self.baserunners:
                if not baserunner.out:
                    baserunner.tentatively_baserun(playing_action=self)
            if not self.batter.out:
                if not self.batter.base_reached_on_hit:
                    self.batter.baserun(playing_action=self)
                elif not self.batter.safely_on_base:
                    if self.batter.baserunning_full_speed:
                        self.batter.baserun(playing_action=self)
                    elif self.batter.tentatively_baserunning:
                        self.batter.tentatively_baserun(playing_action=self)
                    elif self.batter.retreating:
                        self.batter.retreat(playing_action=self)
        else:
            for baserunner in self.baserunners + [self.batter]:
                if not baserunner.out and not baserunner.safely_on_base:
                    if baserunner.baserunning_full_speed:
                        baserunner.baserun(playing_action=self)
                    elif baserunner.tentatively_baserunning:
                        baserunner.tentatively_baserun(playing_action=self)
                    elif baserunner.forced_to_retreat or baserunner.retreating:
                        baserunner.retreat(playing_action=self)
                    elif baserunner.safely_home:
                        if self.at_bat.frame.outs == 2 or not self.batter.base_reached_on_hit:
                            Run(frame=self.at_bat.frame, runner=baserunner, batted_in_by=self.batter,
                                queued=True)
                        else:
                            Run(frame=self.at_bat.frame, runner=baserunner, batted_in_by=self.batter)


class AtBatInterim(object):
    """A duration between at bats in which the ball is live."""

    def __init__(self):
        pass


class PitchInterim(object):
    """A duration between pitches in which the ball is live."""

    def __init__(self, at_bat):
        self.at_bat = at_bat
        at_bat.pitch_interims.append(self)
        # Update the count
        counts = {(0, 0): 00, (1, 0): 10, (2, 0): 20, (3, 0): 30,
                  (0, 1): 10, (1, 1): 11, (2, 1): 21, (3, 1): 31,
                  (0, 2): 02, (1, 2): 12, (2, 2): 22, (3, 2): 32}
        at_bat.count = counts[(at_bat.balls, at_bat.strikes)]
        # Fielders and baserunners get in position
        for player in at_bat.fielders + at_bat.frame.baserunners + [at_bat.batter]:
            player.get_in_position(at_bat=at_bat)
        # Minds wander
        for person in at_bat.game.ballpark.people_here_now:
            person.mind.wander()
        # Pitcher prepares delivery
        at_bat.pitcher.decide_pitch(at_bat=at_bat)