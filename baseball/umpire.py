import math
import random
from random import normalvariate as normal
from career import UmpireCareer
from call import PlayAtBaseCall, FlyOutCall
from outcome import FoulBall, FlyOut, HomeRun, GrandSlam, AutomaticDouble, GroundRuleDouble


class Umpire(object):
    """The baseball-umpire layer of a person's being."""

    def __init__(self, person):
        """Initialize an Umpire object."""

        # TODO FIGURE THESE OUT
        self.name = person.name

        self.person = person  # The person in whom this umpire layer embeds
        # Prepare career attribute
        self.career = UmpireCareer(umpire=self)
        # Prepare bias attributes
        self.pitch_call_inconsistency = None
        self.pitch_call_left_edge_bias = None
        self.pitch_call_right_edge_bias = None
        self.pitch_call_top_edge_bias = None
        self.pitch_call_bottom_edge_bias = None
        self.pitch_call_two_strikes_bias = None
        self.pitch_call_three_balls_bias = None
        self.pitch_call_just_called_strike_bias = None
        self.pitch_call_just_called_ball_bias = None
        self.pitch_call_lefty_bias = None
        self.pitch_call_home_team_bias = None
        self.play_at_base_tie_policy = None
        self.play_at_first_prior_entry_bias = None
        self.play_at_base_inconsistency = None
        # Initialize bias attributes
        self._init_umpire_biases()

    def _init_umpire_biases(self):
        """Initialize umpire biases for a person.

        These biases are triggered in tandem by Umpire.call_pitch().

        Primary source: http://www.sloansportsconference.com/wp-content/
        uploads/2014/02/2014_SSAC_What-Does-it-Take-to-Call-a-Strike.pdf
        """
        # Pitch-call inconsistency represents how consistent an
        # umpire will be in attributing a certain call to a specific
        # pitch location over multiple pitches; we represent this as
        # a standard deviation in number of ball widths (the same units
        # with which we represent the strike zone)
        self.pitch_call_inconsistency = abs(normal(0, 0.15))
        # Pitch-edge biases represent the umpire's mean deviation
        # from a true edge of the strike zone in how he
        # represents that edge inasmuch as the calls he makes
        # (studies show that umpires show huge bias for the top edge,
        # considerable bias for the left and bottom edges, and less bias
        # for the right edge)
        self.pitch_call_left_edge_bias = normal(-0.3, 0.15)
        self.pitch_call_right_edge_bias = normal(-0.15, 0.05)
        self.pitch_call_top_edge_bias = normal(-0.65, 0.35)
        self.pitch_call_bottom_edge_bias = normal(1.25, 0.5)
        # Count biases represent whether and how the umpire expands
        # the strike zone when there is three balls and/or constricts
        # the strike zone when there is two strikes -- this bias
        # will affect the ump's representation of all four edges of
        # the strike zone for this pitch, thus they have no sign
        # [Note: these biases are not enacted on a full count]
        self.pitch_call_two_strikes_bias = normal(1, 0.25)
        self.pitch_call_three_balls_bias = normal(0.3, 0.1)
        # Previous-call biases represent whether and how the umpire expands
        # the strike zone after calling a ball and/or constricts the
        # strike zone after calling a strike [Note: these biases ar not
        # enacted on a full-count]
        self.pitch_call_just_called_strike_bias = normal(1, 0.25)
        self.pitch_call_just_called_ball_bias = normal(0.3, 0.1)
        # Left-handedness bias represents how the umpire moves the
        # vertical edges of the strike zone further left for
        # left-handed hitters (Source: http://www.lookoutlanding.com/
        # 2012/10/29/3561060/the-strike-zone)
        self.pitch_call_lefty_bias = normal(-0.07, 0.03)
        # Home-team pitch-call bias represents how the umpire expands
        # the strike zone slightly for home-team pitchers -- this value
        # will be used to expand all four edges of the strike zone, so
        # it small
        self.pitch_call_home_team_bias = abs(normal(0.0, 0.1))
        # Tie-at-base policy represents whether the umpire's procedure
        # for calls at a base is to enforce that the tag must precede
        # the runner reaching the base ('tie goes to the runner', which
        # is not an actual rule) or that the runner must beat the tag --
        # the value represents the number of seconds that will be
        # subtracted from the true time at which the runner reached base
        if random.random() < 0.7:
            # Tie given to runner
            self.play_at_base_tie_policy = 0.01
        else:
            self.play_at_base_tie_policy = -0.01
        # Prior-entry bias makes an umpire call a batter-runner out at
        # first when he is truly safe, due to perceiving the auditory
        # stimulus of the ball embedding in the glove as occurring
        # slightly earlier than it actually does -- this represents
        # the number of seconds that will be subtracted from the true
        # time at which the runner reached base
        self.play_at_first_prior_entry_bias = abs(normal(0.0, 0.015))
        # Play-at-base inconsistency represents how consistent the
        # umpire will be in how he calls plays at a base. The value
        # represents a standard error in number of seconds, which
        # will be either added to or subtracted from the true time
        # at which the baserunner reached
        self.play_at_base_inconsistency = abs(normal(0.0, 0.005))
        # TODO race biases, reputation biases (e.g. all-star control
        # pitcher gets expanded strike zone, etc.)
        # TODO biases from gambling on the game

    def call_pitch(self, pitch):
        """Call a pitch that is not swung at either a strike or a ball."""
        # First, start with a perfect model of the true strike zone
        left_edge, right_edge = -2.83, 2.83
        bottom_edge, top_edge = pitch.batter.strike_zone
        # Pollute this model with edge biases
        left_edge += self.pitch_call_left_edge_bias
        right_edge += self.pitch_call_right_edge_bias
        top_edge += self.pitch_call_top_edge_bias
        bottom_edge += self.pitch_call_bottom_edge_bias
        # Further pollute the model with count biases and
        # previous-call biases, as appropriate; first, consider whether
        # a count bias should be enacted, given the pitch context; if it
        # is not applicable, consider applying a previous-call bias
        # (they'll never both be applied simultaneously)
        if pitch.count == 02 or pitch.count == 12 or pitch.count == 22:
            # Constrict the strike zone
            left_edge += self.pitch_call_two_strikes_bias
            right_edge -= self.pitch_call_two_strikes_bias
            top_edge -= self.pitch_call_two_strikes_bias
            bottom_edge += self.pitch_call_two_strikes_bias
        elif (pitch.count != 00 and pitch.count != 32 and
                pitch.at_bat.pitches[-1].call == "Strike"):
            # Constrict the strike zone
            left_edge += self.pitch_call_just_called_strike_bias
            right_edge -= self.pitch_call_just_called_strike_bias
            top_edge -= self.pitch_call_just_called_strike_bias
            bottom_edge += self.pitch_call_just_called_strike_bias
        if pitch.count == 30 or pitch.count == 31:
            # Expand the strike zone
            left_edge -= self.pitch_call_three_balls_bias
            right_edge += self.pitch_call_three_balls_bias
            top_edge += self.pitch_call_three_balls_bias
            bottom_edge -= self.pitch_call_three_balls_bias
        elif (pitch.count != 00 and pitch.count != 32 and
                pitch.at_bat.pitches[-1].call == "Ball"):
            # Expand the strike zone
            left_edge -= self.pitch_call_just_called_ball_bias
            right_edge += self.pitch_call_just_called_ball_bias
            top_edge += self.pitch_call_just_called_ball_bias
            bottom_edge -= self.pitch_call_just_called_ball_bias
        # Further pollute the model with left-handed hitter bias,
        # if appropriate
        if pitch.batter_left_handed:
            left_edge += self.pitch_call_lefty_bias
            right_edge += self.pitch_call_lefty_bias
        # Further pollute the model with home-team--pitcher bias, if
        # appropriate, which expands the strike zone at all edges
        if pitch.pitcher.team is pitch.at_bat.game.home_team:
            left_edge -= self.pitch_call_home_team_bias
            right_edge += self.pitch_call_home_team_bias
            top_edge += self.pitch_call_home_team_bias
            bottom_edge -= self.pitch_call_home_team_bias
        # Crucially, account for the effects of pitch framing by altering
        # a heretofore perfect representation pitch's location at the
        # point that it crossed the plane over the front of home plate
        # (good pitch framers bring the ball toward the center of the
        # strike zone, while bad pitch framers pull it away from it); this
        # is only enacted in borderline pitches
        if -4 < pitch.actual_x < -2:
            # Pull up toward [0, 0]
            framed_x = pitch.actual_x + pitch.catcher.pitch_framing
        elif 2 < pitch.actual_x < 4:
            # Pull down toward [0, 0]
            framed_x = pitch.actual_x - pitch.catcher.pitch_framing
        else:
            framed_x = pitch.actual_x
        if -5 < pitch.actual_y < -3:
            framed_y = pitch.actual_y + pitch.catcher.pitch_framing
        elif 3 < pitch.actual_x < 5:
            framed_y = pitch.actual_y - pitch.catcher.pitch_framing
        else:
            framed_y = pitch.actual_y
        # Finally, *to simulate umpire inconsistency*, pollute the
        # framed position of the pitch using the umpire's rating
        # for pitch call consistency as a standard deviation
        pitch_location = (
            normal(framed_x, self.pitch_call_inconsistency),
            normal(framed_y, self.pitch_call_inconsistency)
        )
        # Now, make the call if consideration of the polluted pitch
        # location (which is only offset as a trick to represent umpire
        # inconsistency) relative to the umpire's biased model of the
        # trick zone
        if (left_edge < pitch_location[0] < right_edge and
                bottom_edge < pitch_location[1] < top_edge):
            return "Strike"
        else:
            return "Ball"

    def call_play_at_base(self, playing_action, baserunner, base, throw=None, fielder_afoot=None):
        """Call a baserunner either safe or out."""
        # This is some housekeeping that can probably be deleted if the specified errors never pop up
        if base == "1B":
            assert baserunner is playing_action.running_to_first or baserunner is playing_action.retreating_to_first, "" \
                "Umpire was tasked with calling out {} at first, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif base == "2B":
            assert baserunner is playing_action.running_to_second or baserunner is playing_action.retreating_to_second, "" \
                "Umpire was tasked with calling out {} at second, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif base == "3B":
            assert baserunner is playing_action.running_to_third or baserunner is playing_action.retreating_to_third, "" \
                "Umpire was tasked with calling out {} at third, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif base == "H":
            assert baserunner is playing_action.running_to_home or baserunner.safely_on_base, "" \
                "Umpire was tasked with calling out {} at home, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        # If the baserunner hasn't reached base yet, we need to calculate at what timestep
        # they *will/would have* reached base
        if not baserunner.timestep_reached_base:
            dist_from_baserunner_to_base = 90 - (baserunner.percent_to_base*90)
            time_until_baserunner_reaches_base = dist_from_baserunner_to_base * baserunner.full_speed_seconds_per_foot
            baserunner.timestep_reached_base = (
                playing_action.batted_ball.time_since_contact + time_until_baserunner_reaches_base
            )
        # If the ball has reached the base via throw, we know the timestep it reached base;
        # if it reached base via a fielder's on-foot approach, we need to calculate it
        if throw:
            timestep_ball_reached_base = throw.timestep_reached_target
        else:  # elif fielder_afoot
            dist_from_fielder_to_base = math.hypot(
                fielder_afoot.immediate_goal[0]-fielder_afoot.location[0],
                fielder_afoot.immediate_goal[1]-fielder_afoot.location[1]
            )
            time_until_fielder_reaches_base = dist_from_fielder_to_base * fielder_afoot.full_speed_seconds_per_foot
            timestep_ball_reached_base = (
                playing_action.batted_ball.time_since_contact + time_until_fielder_reaches_base
            )
        # Get the difference in time between the baserunner reaching base
        # and the throw reached the first baseman's glove -- this will be
        # negative if the runner beat the throw
        baserunner_diff_from_throw = true_difference = (
            baserunner.timestep_reached_base - timestep_ball_reached_base
        )
        # Make note of the true call for this play -- we'll say that ties go to the runner,
        # though the chance of one is extremely unlikely
        if baserunner_diff_from_throw <= 0:
            true_call = "Safe"
        else:
            true_call = "Out"
        # Pollute this perfectly accurate difference for whether the
        # umpire believes the throw must beat the runner ('tie goes to
        # the runner') or vice versa
        baserunner_diff_from_throw -= self.play_at_base_tie_policy
        # If play is at first, further pollute the difference for how susceptible the umpire
        # is to a prior-entry bias, explained in _init_umpire_biases()
        if base == "1B":
            baserunner_diff_from_throw += self.play_at_first_prior_entry_bias
        # Finally, *to simulate umpire inconsistency*, further pollute the
        # difference by regenerating it from a normal distribution around
        # itself with the umpire's inconsistency standard error as the
        # standard deviation
        baserunner_diff_from_throw = (
            normal(baserunner_diff_from_throw, self.play_at_base_inconsistency)
        )
        if baserunner_diff_from_throw <= 0:
            PlayAtBaseCall(at_bat=playing_action.at_bat, umpire=self, call="Safe", true_call=true_call,
                           true_difference=true_difference, baserunner=baserunner, base=base, throw=throw,
                           fielder_afoot=fielder_afoot)
        else:
            PlayAtBaseCall(at_bat=playing_action.at_bat, umpire=self, call="Out", true_call=true_call,
                           true_difference=true_difference, baserunner=baserunner, base=base, throw=throw,
                           fielder_afoot=fielder_afoot)

    def call_fly_out_or_trap(self, batted_ball):
        """Call a fielding act either a fly out or a trap."""
        # First, determine the crucial timestep, which is the timestep in which the
        # ball truly landed such that no fly out should be scored -- this will depend on
        # the rules and whether they allow for bounding fly outs
        if batted_ball.in_foul_territory:
            if batted_ball.at_bat.game.rules.foul_ball_on_first_bounce_is_out:
                if batted_ball.second_landing_timestep:
                    crucial_timestep = batted_ball.second_landing_timestep
                else:
                    # Ball just plopped down on its first timestep, so there's no chance for
                    # a bounding catch -- as such, give arbitrary high number for crucial timestep,
                    # which will never allow for a FlyOut call
                    crucial_timestep = 999
            else:
                crucial_timestep = batted_ball.landing_timestep
        else:  # elif not batted_ball.in_foul_territory:
            if batted_ball.at_bat.game.rules.fair_ball_on_first_bounce_is_out:
                if batted_ball.second_landing_timestep:
                    crucial_timestep = batted_ball.second_landing_timestep
                else:
                    crucial_timestep = 999
            else:
                crucial_timestep = batted_ball.landing_timestep
        # Next, determine the true difference, in seconds, between the current timestep,
        # which is when the fielding act in question has occurred, and the crucial timestep
        # in which the ball bounced to preclude any true fly out -- negative values represent
        # the ball landing first, and thus cases where the true call is a trap
        true_difference_between_ball_landing_and_fielding_act = crucial_timestep - batted_ball.time_since_contact
        if true_difference_between_ball_landing_and_fielding_act < -0.1:
            # If the ball landed two or more timesteps ago, it's not even a trap, so
            # don't bother making a call
            pass
        else:
            if true_difference_between_ball_landing_and_fielding_act > 0:
                true_call = "Out"
            else:
                true_call = "Trap"
            # To simulate umpire imperfection and inconsistency, pollute the perfect (though
            # coarse-grained) representation of the difference in time
            umpire_perceived_difference = normal(true_difference_between_ball_landing_and_fielding_act, 0.04)
            if umpire_perceived_difference > 0:
                FlyOutCall(umpire=self, call="Out", true_call=true_call,
                           true_difference=true_difference_between_ball_landing_and_fielding_act,
                           batted_ball=batted_ball)
            else:
                FlyOutCall(umpire=self, call="Trap", true_call=true_call,
                           true_difference=true_difference_between_ball_landing_and_fielding_act,
                           batted_ball=batted_ball)

    def officiate(self, playing_action):
        """Officiate as necessary, including making (pseudo) dead-ball determination."""
        # TODO umpire biases
        batted_ball = playing_action.batted_ball
        if batted_ball.ground_rule_incurred:
            GroundRuleDouble(batted_ball=batted_ball)
            playing_action.resolved = True
        elif batted_ball.contacted_foul_pole:
            if batted_ball.at_bat.frame.bases_loaded:
                GrandSlam(batted_ball=batted_ball)
            else:
                HomeRun(batted_ball=batted_ball)
            playing_action.resolved = True
        elif batted_ball.contacted_foul_fence:
            FoulBall(batted_ball=batted_ball)
            playing_action.resolved = True
        elif batted_ball.fielded_by and not batted_ball.fly_out_call_given:
            # If a fly out was potentially made, make the call as to whether it was
            # indeed a fly out or else a trap; don't even bother if the ball has
            # clearly bounced one or more times too many or if it has bounced off the
            # outfield wall
            if not batted_ball.contacted_outfield_wall:
                if (batted_ball.at_bat.game.rules.foul_ball_on_first_bounce_is_out or
                        batted_ball.at_bat.game.rules.fair_ball_on_first_bounce_is_out):
                    if batted_ball.n_bounces < 3:
                        self.call_fly_out_or_trap(batted_ball=batted_ball)
                else:
                    if batted_ball.n_bounces < 2:
                        self.call_fly_out_or_trap(batted_ball=batted_ball)
        elif batted_ball.left_playing_field:
            if batted_ball.crossed_plane_foul:
                FoulBall(batted_ball=batted_ball)
                playing_action.resolved = True
            elif batted_ball.crossed_plane_fair:
                # Could potentially be a home run, ground-rule double, or foul
                # ball, depending on the rules agreed upon for the game
                if batted_ball.n_bounces:
                    # A ball that bounds over the outfield fence will be either
                    # a home run or automatic double, depending on the following
                    # rule
                    if batted_ball.at_bat.game.rules.bound_that_leaves_park_is_home_run:
                        if batted_ball.at_bat.frame.bases_loaded:
                            GrandSlam(batted_ball=batted_ball)
                        else:
                            HomeRun(batted_ball=batted_ball)
                        playing_action.resolved = True
                    else:
                        AutomaticDouble(batted_ball=batted_ball)
                        playing_action.resolved = True
                elif not batted_ball.n_bounces and batted_ball.at_bat.game.rules.home_run_must_land_fair:
                    # A ball that crosses the plane of the outfield fence in flight
                    # will be either a foul ball or home run, depending on whether
                    # this rule is in effect -- if it is, the ball must also land fair
                    # to be a home run
                    if batted_ball.landed:
                        if batted_ball.in_foul_territory:
                            FoulBall(batted_ball=batted_ball, anachronic_home_run=True)
                            playing_action.resolved = True
                        elif not batted_ball.in_foul_territory:
                            # Batted ball crosses plane of the outfield fence fair
                            # and lands fair -- a home run in any era
                            if batted_ball.at_bat.frame.bases_loaded:
                                GrandSlam(batted_ball=batted_ball)
                            else:
                                HomeRun(batted_ball=batted_ball)
                            playing_action.resolved = True
                else:
                    # Batted ball crossed the plane of the outfield fence, which is
                    # good enough for a home run if the above rule is not in effect
                    if batted_ball.at_bat.frame.bases_loaded:
                        GrandSlam(batted_ball=batted_ball)
                    else:
                        HomeRun(batted_ball=batted_ball)
                    playing_action.resolved = True
        elif batted_ball.landed_foul:
            # Generally, a batted ball that lands foul incur a foul ball -- the exception
            # is if the rule allowing a bounding foul to be caught for a FlyOut is in effect;
            # in that case, we don't score the foul ball until a timestep after the batted ball's
            # second bounce -- this allows a fielder to potentially make the catch (if the ball
            # doesn't have a second bounce in its trajectory, we just score the foul right away)
            if not batted_ball.at_bat.game.rules.foul_ball_on_first_bounce_is_out:
                FoulBall(batted_ball=batted_ball)
                playing_action.resolved = True
            else:
                if (not batted_ball.second_landing_timestep or
                        batted_ball.time_since_contact > batted_ball.second_landing_timestep+0.1):
                    FoulBall(batted_ball=batted_ball)
                    playing_action.resolved = True
        elif batted_ball.landed and batted_ball.in_foul_territory:
            if batted_ball.passed_first_or_third_base or batted_ball.stopped or batted_ball.touched_by_fielder:
                FoulBall(batted_ball=batted_ball)
                playing_action.resolved = True
        # Determine whether the current playing action has ended
        if batted_ball.at_bat.frame.outs == 3:
            if batted_ball.at_bat.game.trace:
                print "-- Since there are three outs, the playing action is over [{}]".format(
                    batted_ball.time_since_contact
                )
            playing_action.resolved = True
        # elif all(b.safely_on_base or b.out for b in batted_ball.at_bat.frame.baserunners + [batted_ball.at_bat.batter]):
        #     if batted_ball.landed and (not batted_ball.at_bat.throw or batted_ball.at_bat.throw.reached_target):
        #         print "-- Since all baserunners are either out or safe, the playing action is over [{}]".format(
        #             batted_ball.time_since_contact
        #         )
        #         playing_action.resolved = True
