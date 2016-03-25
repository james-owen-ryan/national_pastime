import random
import math
import os
import time
import re
from random import normalvariate as normal

from corpora import Names
from equipment import Bat, Baseball, Glove, Mitt
from play import Pitch, Swing, Bunt, FieldingAct, Throw
from career import PlayerCareer


# TODO PAIRWISE SYNERGY BETWEEN PLAYERS -- MAYBE A BASEBALL-CENTRIC CLASS RESEMBLING RELATIONSHIP()


# TODO  conduct_offseason_activity skills according to age, practice, and also according to era somehow (maybe
# TODO  have the averages, used often in diff_from_avg snippets, change over time?)


class Player(object):
    """The baseball-player layer of a person's being."""

    def __init__(self, person):
        """Initialize a Player object."""

        # TEMP TODO FIGURE OUT WHAT TO DO ABOUT THESE
        self.speed_home_to_first = person.body.speed_home_to_first
        self.height = person.body.height
        self.vertical_reach = person.body.vertical_reach
        self.full_speed_seconds_per_foot = person.body.full_speed_seconds_per_foot
        self.audacity = person.personality.audacity
        self.reflexes = person.body.reflexes

        self.person = person  # The person in whom this player layer embeds
        # Prepare career attribute
        self.career = PlayerCareer(player=self)
        self._init_baseball_attributes()
        self.strike_zone = self._determine_strike_zone()
        self.bat = None
        self.glove = Glove()
        # Inherent attributes that only change gradually over the course of a
        # life; these are set by _init_baseball_attributes(), and more info
        # on these can be found in the comments there
        self.fieldable_ball_max_height = None
        self.fly_ball_fielding = None
        self.ground_ball_fielding = None
        self.throwing_velocity_mph = None
        self.throwing_velocity = None  # This one is in ft/s, which is more convenient
        self.throwing_release_time = None
        self.throwing_error_per_foot = None
        self.sidearm_throwing_error_per_foot = None
        self.pitch_control = None
        self.pitch_speed = None
        self.pitch_speed_sd = None  # Standard deviation of pitch speed
        self.pitch_recognition = None
        self.swing_timing_error = None
        self.swing_contact_error = None
        self.batting_power_coefficient = None  # This one is actually used in determining bat speed on a swing
        self.batting_power = None  # This one is for human readability; average is 1.0, greater is stronger
        self.swing_pull_ability = None
        self.pitch_receiving = None
        self.pitch_blocking = None
        self.pitch_framing = None
        self.ball_tracking_ability = None
        # Dynamic attributes that change during a game and are reset after the game ends
        self.position = None  # Position player is currently playing
        self.infielder = False
        self.outfielder = False
        self.location = None  # Exact x, y coordinates on the field
        self.percent_to_base = None  # Percentage of way to base you're running to
        self.safely_on_base = False  # Physically reached the next base, not necessarily safely
        self.safely_home = False
        self.retreating = False
        self.time_needed_to_field_ball = None
        self.playing_the_ball = False
        self.attempting_fly_out = False
        self.immediate_goal = None
        self.making_goal_revision = False
        self.dist_per_timestep = None  # Feet per timestep in approach to immediate goal
        self.relative_rate_of_speed = None
        self._slope = None
        self.at_goal = None
        self._straight_ahead_x = None
        self._straight_ahead_y = None
        self._moving_left = False
        self._moving_right = False
        # Set inherent baseball attributes
        self._init_baseball_attributes()

    @property  # TODO STOPGAP
    def team(self):
        return self.career.team if self.career else None

    def _init_baseball_attributes(self):
        """Set this player's inherent baseball attributes."""
        self._init_baseball_intangibles()
        self._init_baseball_fielding_attributes()
        self._init_baseball_throwing_attributes()

        #           -- Pitching attributes --

        # Pitch control is modeled as the player's standard deviation,
        # in number of baseball widths, that both horizontally and
        # vertically a pitched ball will deviate in where it crosses
        # the vertical plane of home plate with regard to where the
        # pitcher intended for it to cross the plane
        self.pitch_control = abs(normal(5, 1.2))
        # Pitch speed is modeled similarly to batting power, in that
        # actual pitch speeds will be generated from a normal
        # distribution around a player's mean maximum pitch speed
        # using their standard deviation for maximum pitch speed
        self.pitch_speed = self.throwing_velocity_mph - random.random()*10
        self.pitch_speed_sd = normal(self.pitch_speed/20,
                                     self.pitch_speed/30)

        # Pitch recognition is modeled similarly to pitch control,
        # with it being the player's standard deviation, in number of
        # baseball widths, that both horizontally and vertically a
        # pitched ball will deviate in where it crosses the vertical
        # plane of home plate with regard to where the batter believes
        # it will cross the plane
        self.pitch_recognition = abs(normal(2, 0.8))

        #           -- Batting attributes --

        # Swing-timing error is a measure of a batter's standard
        # deviation from perfect swing timing (represented as 0);
        # swing timing is correlated to a player's coordination
        base_swing_timing = (
            0.75*self.person.body.coordination + 1.5*self.person.personality.focus + self.person.body.reflexes
        )
        self.swing_timing_error = base_swing_timing/40.0
        # Swing-contact error is a measure of a batter's standard
        # deviation, both on the x- and y-axis, from perfect swing
        # contact, i.e., bat-ball contact at the bat's sweet spot;
        # it is generated as a correlate to swing timing error
        self.swing_contact_error = base_swing_timing/120.0
        # Batting power affects the speed with which a player swings his
        # bat at the point of contact with a pitched ball -- the coefficient
        # is represented in an abstract unit that is used, along with bat
        # weight, by @property self.bat_speed to compute bat speed; the
        # batting_power attribute is for human readability and scouting and
        # is normalized so that 1.0 is average batting power and values above
        # it represent greater power
        base_batting_power = self.person.body.weight * self.person.body.coordination
        self.batting_power_coefficient = -1.65 + base_batting_power/215.
        self.batting_power = 2.0 + self.batting_power_coefficient
        # Swing pull ability represents the percentage of the time
        # that a batter can pull a batted ball to the opposite field
        # when they intend to
        self.swing_pull_ability = normal(0.15, 0.08)
        if self.swing_pull_ability < 0.01:
            self.swing_pull_ability = 0.01

        #           -- Catching attributes --

        # Pitch receiving is purely a rating of the player's ability to catch
        # pitches (cf. fielding, which is more general and represents a
        # player's ability to field batted balls); a player's pitch-receiving
        # rating specifies how increased their likelihood of successfully
        # catching a pitch is above the average player (ratings near 1.2
        # represent once-a-generation talents)
        primitive_pitch_receiving_ability = (
            (self.person.body.coordination * 0.5) + self.person.body.reflexes + (self.ball_tracking_ability * 1.5)
        )
        diff_from_avg = primitive_pitch_receiving_ability - 2.63
        diff_from_avg /= 7.4
        if diff_from_avg >= 0:
            percentage_above_avg = abs(normal(0, diff_from_avg))
            self.pitch_receiving = 1 + percentage_above_avg
        else:
            percentage_below_avg = abs(normal(0, abs(diff_from_avg)))
            self.pitch_receiving = 1 - percentage_below_avg
        # Pitch blocking ability represents the catcher's ability to
        # block pitches that are thrown in the dirt so that they don't
        # get past him, which would allow baserunners to advance
        primitive_pitch_blocking_ability = (
            (self.person.body.coordination * 1.25) + self.person.body.reflexes + (self.ball_tracking_ability * 1.5)
        )
        diff_from_avg = primitive_pitch_blocking_ability - 3.24
        diff_from_avg /= 15.2
        if diff_from_avg >= 0:
            percentage_above_avg = abs(normal(0, diff_from_avg))
            self.pitch_blocking = 1 + percentage_above_avg
        else:
            percentage_below_avg = abs(normal(0, abs(diff_from_avg)))
            self.pitch_blocking = 1 - percentage_below_avg
        # Pitch framing ability represents a catcher's ability to
        # receive pitches just outside the strike zone in a way that
        # makes them appear to be strikes -- or, in the case of a
        # negative rating, the detrimental tendency to receive
        # borderline strikes in such a way as to make them appear
        # to be balls
        primitive_pitch_framing_ability = (
            self.person.body.coordination + (self.person.personality.cleverness * 0.75)
        )
        diff_from_avg = primitive_pitch_framing_ability - 1.18
        diff_from_avg /= 1.5
        if diff_from_avg < -0.2:
            diff_from_avg = normal(-0.2, 0.03)
        if diff_from_avg >= 0:
            self.pitch_framing = abs(normal(0, diff_from_avg))
        else:
            self.pitch_framing = -abs(normal(0, diff_from_avg))

    def _init_baseball_intangibles(self):
        """Set this player's inherent baseball intangibles."""
        # Ball tracking ability is correlated to a player's focus rating and affects a
        # player's ability to anticipate the trajectories of balls in movement -- most
        # saliently, it affects the speed with which a fielder can move in getting in
        # position to field a fly ball while still properly tracking that ball; values
        # approaching 1.5 represent once-a-generation talents that would be capable of
        # something like Willie Mays' famous catch
        self.ball_tracking_ability = self.person.cosmos.config.set_ball_tracking_ability(
            focus=self.person.personality.focus
        )

    def _init_baseball_fielding_attributes(self):
        """Set this player's inherent baseball fielding attributes.

        Every fielding chance has a specified difficulty, which (approximately) represents
        the percentage likelihood that an average player would successfully field the ball
        given the circumstances at hand. A player's fielding ratings then specify how increased
        their likelihood of successfully fielding a batted ball is above the average player
        (ratings near 1.3-1.5 represent once-a-generation talents).
        """
        # For speed, bring in the physical and mental components that we will
        # reference multiple times
        config = self.person.cosmos.config
        body = self.person.body
        coordination = body.coordination
        agility = body.agility
        focus = self.person.personality.focus
        ball_tracking_ability = self.ball_tracking_ability
        # Fly-ball fielding ability (subsumes line drives and pop-ups) is a function of
        # coordination, agility, ball-tracking ability, and focus
        primitive_fly_ball_fielding_ability = config.set_primitive_fly_ball_fielding_ability(
            coordination=coordination, agility=agility,
            ball_tracking_ability=ball_tracking_ability, focus=focus
        )
        diff_from_avg = primitive_fly_ball_fielding_ability - config.fly_ball_fielding_ability_avg
        diff_from_avg /= config.fly_ball_fielding_ability_variance
        if diff_from_avg >= 0:
            percentage_above_avg = config.set_percentage_above_or_below_average(diff_from_avg=diff_from_avg)
            self.fly_ball_fielding = 1 + percentage_above_avg
        else:
            percentage_below_avg = config.set_percentage_above_or_below_average(diff_from_avg=diff_from_avg)
            self.fly_ball_fielding = 1 - percentage_below_avg
        # Ground-ball fielding ability is also a function of coordination, agility,
        # ball-tracking ability, and focus
        primitive_ground_ball_fielding_ability = config.set_primitive_ground_ball_fielding_ability(
            coordination=coordination, agility=agility,
            ball_tracking_ability=ball_tracking_ability, focus=focus
        )
        diff_from_avg = primitive_ground_ball_fielding_ability - config.ground_ball_fielding_ability_avg
        diff_from_avg /= config.ground_ball_fielding_ability_variance
        if diff_from_avg >= 0:
            percentage_above_avg = config.set_percentage_above_or_below_average(diff_from_avg=diff_from_avg)
            self.ground_ball_fielding = 1 + percentage_above_avg
        else:
            percentage_below_avg = config.set_percentage_above_or_below_average(diff_from_avg=diff_from_avg)
            self.ground_ball_fielding = 1 - percentage_below_avg
        # Max height, in feet, at which a ball in flight may be caught by a player; this
        # is calculated as his vertical reach plus his vertical
        vertical_in_feet = body.vertical / 12.0
        self.fieldable_ball_max_height = body.vertical_reach + vertical_in_feet

    def _init_baseball_throwing_attributes(self):
        """Set this player's inherent baseball throwing attributes."""
        # For speed, bring in the physical and mental components that we will
        # reference multiple times
        config = self.person.cosmos.config
        body = self.person.body
        coordination = body.coordination
        focus = self.person.personality.focus
        # Throwing velocity is a function of coordination and height
        primitive_throwing_velocity = config.set_primitive_throwing_velocity(
            coordination=coordination, height=body.height
        )
        primitive_throwing_velocity = config.clamp_primitive_throwing_velocity(
            primitive_throwing_velocity=primitive_throwing_velocity
        )
        self.throwing_velocity_mph = config.set_throwing_velocity_mph(  # MPH is for human readability
            primitive_throwing_velocity=primitive_throwing_velocity
        )
        self.throwing_velocity = self.throwing_velocity_mph * 1.46667  # Ft/s is for simulational convenience
        # Throwing release time is a function of coordination and hustle; I believe it
        # is measured in seconds
        primitive_throwing_release_time = config.set_primitive_throwing_release_time(
            coordination=coordination, hustle=body.hustle
        )
        diff_from_avg = primitive_throwing_release_time - config.throwing_release_time_avg
        if diff_from_avg >= 0:
            diff_from_avg /= config.throwing_release_time_variance_above_avg
            self.throwing_release_time = config.set_throwing_release_time_above_avg(diff_from_avg=diff_from_avg)
        elif diff_from_avg < 0:
            diff_from_avg /= config.throwing_release_time_variance_below_avg
            self.throwing_release_time = config.set_throwing_release_time_below_avg(diff_from_avg=diff_from_avg)
        # Regular throwing accuracy (accuracy on normal release) is a function of coordination
        # and focus; it's modeled as the typical error, in feet on both the x- and y-axes, per foot
        # of throwing distance
        primitive_throwing_accuracy = config.set_primitive_throwing_accuracy(coordination=coordination, focus=focus)
        diff_from_avg = primitive_throwing_accuracy - config.throwing_accuracy_avg
        throwing_error_per_foot = config.set_throwing_error_per_foot(diff_from_avg=diff_from_avg)
        # Enforce that the best throwing accuracy can be about one foot of error for every 130 feet
        self.throwing_error_per_foot = config.cap_throwing_error_per_foot(
            throwing_error_per_foot=throwing_error_per_foot
        )
        # Sidearm throwing accuracy is by default is quite worse, since this requires a lot of practice
        self.sidearm_throwing_error_per_foot = config.set_sidearm_throwing_error_per_foot(
            throwing_error_per_foot=self.throwing_error_per_foot
        )

    def _determine_strike_zone(self):
        """Determine this player's strike zone, given their height.

        A player's strike zone is represented by its lower and upper bound, which
        are both measured in number of baseballs.
        """
        height_in_baseballs = self.person.body.height/3.
        height_at_hollow_of_knee = height_in_baseballs * 0.25
        height_at_torso_midpoint = height_in_baseballs * 0.6
        height_of_strike_zone = height_at_torso_midpoint-height_at_hollow_of_knee
        return -height_of_strike_zone/2, height_of_strike_zone/2

    def __str__(self):
        """Return string representation."""
        if self.career.team:
            return "{name}, {position}, {team_name}".format(
                name=self.person.name,
                position=self.position,
                team_name=self.career.team.name
            )
        else:
            return "{name}, free agent, {city_name}, {state_name}".format(
                name=self.person.name,
                city_name=self.person.city.name,
                state_name=self.person.city.state.name
            )

    # @property
    # def composure(self):
    #     """Return this player's current composure level."""
    #     return self.person.mood.composure

    @property
    def righty(self):
        """Return whether this player plays right-handed."""
        return self.person.body.righty

    @property
    def lefty(self):
        """Return whether this player plays left-handed."""
        return self.person.body.lefty

    def get_in_position(self, at_bat):
        """Get into position prior to a pitch."""
        # Clamp composure
        self.person.mood.clamp_composure()
        # Offensive players
        if self is at_bat.batter:
            self.location = [0, 0]
            self.forced_to_advance = True
            self.percent_to_base = 0.0
        elif self is at_bat.frame.on_first:
            self.location = [63.5, 63.5]
            self.forced_to_advance = True
            # Lead off about 10 feet
            self.percent_to_base = normal(0.08, 0.01)
        elif self is at_bat.frame.on_second:
            self.location = [0, 127]
            if at_bat.frame.on_first:
                self.forced_to_advance = True
            # Lead off about 15 feet
            self.percent_to_base = normal(0.11, 0.01)
        elif self is at_bat.frame.on_third:
            self.location = [-63.5, 63.5]
            if at_bat.frame.on_first and at_bat.frame.on_second:
                self.forced_to_advance = True
            # Lead off about 10 feet
            self.percent_to_base = normal(0.08, 0.01)
        # Defensive players
        elif self.position == "P":
            self.location = [0, 60.5]
        elif self.position == "C":
            self.location = [0, -2]
        elif self.position == "1B":
            self.location = [69, 79]
        elif self.position == "2B":
            self.location = [32, 135]
        elif self.position == "SS":
            self.location = [-32, 132]
        elif self.position == "3B":
            self.location = [-60, 80]
        elif self.position == "RF":
            self.location = [125, 230]
        elif self.position == "CF":
            self.location = [-3, 290]
        elif self.position == "LF":
            self.location = [-133, 235]
        # Reset dynamic in-play attributes
        self.time_needed_to_field_ball = None
        self.timestep_of_planned_fielding_attempt = None
        self.attempting_fly_out = False
        self.immediate_goal = None
        self.dist_per_timestep = None
        self.playing_the_ball = False
        self.backing_up_the_catch = False
        self.called_off_by = None
        self.relative_rate_of_speed = None
        self._slope = None
        self.at_goal = False
        self._straight_ahead_x = False
        self._straight_ahead_y = False
        self._moving_left = False
        self._moving_right = False
        self.reorienting_after_fielding_miss = 0.0
        self.out = False
        self.out_on_the_throw = None  # Will point to a TagOut object if player is out on the throw
        self.took_off_early = False
        self.baserunning_full_speed = False
        self.tentatively_baserunning = False
        self._done_tentatively_advancing = False
        self._decided_finish = False
        self.will_round_base = False
        self.believes_he_can_beat_throw = False
        self.taking_next_base = False
        self.retreating = False
        self.safely_on_base = False
        self.safely_home = False
        self.base_reached_on_hit = None
        self.timestep_reached_base = None
        self.forced_to_retreat = False
        self.advancing_due_to_error = False
        self.will_throw = False
        self.throwing_to_first = False
        self.throwing_to_second = False
        self.throwing_to_third = False
        self.throwing_to_home = False
        self.throwing_back_to_pitcher = False
        self.throwing_to_relay = False
        self.making_goal_revision = False

    def decide_pitch(self, at_bat):

        # TODO this is decided collaboratively with catcher using signals

        batter = at_bat.batter
        count = at_bat.count

        # Here, I'll want to add in sidespin and downspin, which
        # will determine how a ball curves and breaks, respectively

        if count == 00 or count == 10:
            # Count is 0-0 or 1-0
            if random.random() < 0.35:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 01:
            if random.random() < 0.15:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 20:
            if random.random() < 0.4:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 11:
            if random.random() < 0.2:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 02:
            if random.random() < 0.1:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 30:
            if random.random() < 0.6:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 21:
            if random.random() < 0.28:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 12:
            if random.random() < 0.11:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 31:
            if random.random() < 0.67:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 22:
            if random.random() < 0.75:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 32:
            if random.random() < 0.67:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 3.0, 4.5
                self.kind, self.intended_x, self.intended_y = "fastball", x, y

    def pitch(self, at_bat, drop=None, curve=None):

        # TODO remove kind, add speed, break, curve -- then reason
        # over that to determine the kind; with increased speed comes
        # increased x and y error

        batter = at_bat.batter
        catcher = at_bat.catcher
        count = at_bat.count
        # Determine pitch speed and behavior
        kind = "fastball"
        speed = normal(self.pitch_speed, self.pitch_speed_sd)
        # Determine where it will intersect the vertical plane at home plate
        actual_x = normal(self.intended_x, self.pitch_control)
        actual_y = normal(self.intended_y, self.pitch_control)
        if self.righty:
            handedness = "R"
        else:
            handedness = "L"
        if batter.righty:
            batter_handedness = "R"
        else:
            batter_handedness = "L"
        pitch = Pitch(ball=Baseball(), at_bat=at_bat, handedness=handedness,
                      batter_handedness=batter_handedness, count=count, kind=kind,
                      speed=speed, intended_x=self.intended_x, intended_y=self.intended_y,
                      actual_x=actual_x, actual_y=actual_y)
        return pitch

    def decide_whether_to_swing(self, pitch):
        # Determine the batter's expected speed for the pitch, given
        # context such as the last pitch, his knowledge of the pitcher,
        # etc. TODO
        pitch.batter_expected_speed = pitch.speed
        # Determine the batter's hypothesis about the pitch's speed,
        # given his initial perception of it in movement TODO
        pitch.batter_hypothesized_speed = pitch.speed
        # Determine the batter's hypothesis of where the ball will cross
        # the vertical plane of home plate
        pitch.batter_hypothesized_x = (
            normal(pitch.actual_x, self.pitch_recognition)
        )
        pitch.batter_hypothesized_y = (
            normal(pitch.actual_y, self.pitch_recognition)
        )
        # (CURRENTLY, the batter forms his hypothesis of whether the pitch
        # is a ball or a strike with perfect knowledge of the strike zone.
        # Obviously, this is inaccurate -- but I think the noise around
        # his hypotheses for x and y are enough to account for the variation
        # this would give. Of course, we then give up the interesting
        # story nuance of a batter believing a pitch to be a ball when in fact
        # it was a strike, and then the umpire calling it a strike or ball or
        # whichever, etc. ADDITIONALLY, this more accurately would be
        # represented as a real-valued confidence score, rather than a binary.)
        if (-2.83 < pitch.batter_hypothesized_x < 2.83 and
                self.strike_zone[0] < pitch.batter_hypothesized_y <
                self.strike_zone[1]):
            pitch.batter_hypothesis = "Strike"
        else:
            pitch.batter_hypothesis = "Ball"
        # Decide whether to hit -- TODO: MAKE THIS ALSO CONSIDER PITCH SPEED
        if pitch.batter_hypothesis == "Strike":
            if pitch.count == 00:
                # Count before this pitch is 0-0
                if random.random() < 0.3:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 10:
                if random.random() < 0.41:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 01:
                if random.random() < 0.78:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 20:
                if random.random() < 0.4:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 11:
                if random.random() < 0.63:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 02:
                if random.random() < 0.995:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 30:
                if random.random() < 0.03:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 21:
                if random.random() < 0.65:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 12:
                if random.random() < 0.995:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 31:
                if random.random() < 0.3:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 22:
                if random.random() < 0.995:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 32:
                if random.random() < 0.995:
                    self.will_swing = True
                else:
                    self.will_swing = False
        elif pitch.batter_hypothesis == "Ball":
            if pitch.count == 00:
                # Count before this pitch is 0-0
                if random.random() < 0.01:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 10:
                if random.random() < 0.03:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 01:
                if random.random() < 0.15:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 20:
                if random.random() < 0.02:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 11:
                if random.random() < 0.15:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 02:
                if random.random() < 0.46:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 30:
                if random.random() < 0.01:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 21:
                if random.random() < 0.1:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 12:
                if random.random() < 0.4:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 31:
                if random.random() < 0.05:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 22:
                if random.random() < 0.65:
                    self.will_swing = True
                else:
                    self.will_swing = False
            elif pitch.count == 32:
                if random.random() < 0.7:
                    self.will_swing = True
                else:
                    self.will_swing = False

    def decide_swing(self, pitch):
        # Decide whether to bunt
        bunt = False
        if bunt:
            return "bunt"
        # Decide swing power -- this will be the main determinant of
        # how far the ball, if batted, will travel in the air; with
        # increasing swing power comes increasing chances to swing
        # and miss [Naively asserting medium-high power for now]
        # if random.random() > 0.6:
        #     self._swing_power = normal(0.75, 0.05)
        # else:
        #     self._swing_power = 1.0
        self._swing_power = 1.0
        # if self._swing_power > 1.0:
        #     self._swing_power = 1.0
        # if self._swing_power < 0.65:
        #     self._swing_power = 0.65
        # Decide upward force of the swing -- this will be a major
        # factor in determining a ball's trajectory upon being hit
        # The values correspond to hit types in the following way:
        # --------------------------------------------------------
        # 0	    downward            --  horrible ground ball
        # 0.2	horizontal 		    --  low line drive/ground ball
        # 0.4	slightly upward     --  line drive
        # 0.6	upward			    --  fly ball
        # 0.8+	increasingly upward --  pop-up
        # --------------------------------------------------------
        # if random.random() > 0.6:
        #     self._swing_incline = normal(7.5, 2)   # TODO [this is naive]
        # else:
        #     self._swing_incline = normal(25, 6)
        self._swing_incline = normal(25, 6)
        # Decide whether to attempt to pull the ball to the opposite
        # field
        if random.random() < 0.3:
            self.intended_pull = True
        else:
            self.intended_pull = False

    def bunt(self, pitch):
        pass

    def swing(self, pitch):
        """Swing at a pitch.

        Keyword arguments:
        power -- a real number between 0 and 1 indicating how much power
                 the batter will put into the swing
        incline -- the angle the ball will launch off the bat, if
                        it's struck right at the sweet spot
        pull -- a boolean indicating whether the batter will attempt to
                pull the ball, if batted, toward the opposite field
        """
        # Determine swing timing -- timing generally becomes worse with
        # more powerful swings, as well as utterly powerless swings (a
        # swing with 0.2 power produces ideal timing)
        base_timing = normal(0, self.swing_timing_error+(abs(0.65-self._swing_power)/30))
        # Affect timing according to the pitch speed -- timing improves as pitch speeds
        # drop below 70 and gets worse with pitches faster than 70
        proportion_relative_to_ideal_pitch_speed = pitch.speed/70.
        timing = base_timing / proportion_relative_to_ideal_pitch_speed
        # Affect timing according to composure (raised to the 1/3 power to mitigate
        # the effect)
        timing /= self.person.mood.composure**0.3
        # Determine swing contact point -- this is represented
        # as an (x, y) coordinate, where (0, 0) represents contact
        # at the bat's sweet spot; contact x-coordinate is determined
        # by the batter's swing contact error and then offset by their
        # timing (these could interact such that bad timing incidentally
        # corrects bad contact); contact y-coordinate is determined by the
        # batter's swing contact error and is negatively affected as more
        # power is put into the swing; both are also negatively affected by
        # high pitch speeds
        contact_x_coord = normal(0, self.swing_contact_error) + timing*5  # x-coord is on different scale
        contact_y_coord = normal(0, self.swing_contact_error) + timing/2.
        if self.righty:
            handedness = "R"
        else:
            handedness = "L"
        swing = Swing(pitch=pitch, handedness=handedness,
                      power=self._swing_power, incline=self._swing_incline,
                      intended_pull=self.intended_pull, timing=timing,
                      contact_x_coord=contact_x_coord,
                      contact_y_coord=contact_y_coord)
        return swing

    def receive_pitch(self, pitch):
        """Receive a pitch that is not swung at."""
        distance_from_strike_zone_center = (
            abs(0-pitch.actual_x) + abs(0-pitch.actual_y)
        )
        difficulty = (distance_from_strike_zone_center**2 / 20.0) * 0.015
        difficulty /= self.pitch_receiving
        # It's slightly harder to cleanly receive a pitch when framing,
        # so we increase the difficulty, just barely, for this
        difficulty += self.pitch_framing/1000.0
        if random.random() < difficulty:
            return False
        else:
            return True

    def receive_foul_tip(self):
        """Receive a foul tip.

        TODO: Considerable possibility of injury here.
        """
        difficulty = 0.6
        difficulty /= self.pitch_receiving
        if random.random() < difficulty:
            return False
        else:
            return True

    def block_pitch_in_the_dirt(self, pitch):
        """Block a pitch that has hit the dirt in front of home plate.

        Pitches in the dirt are identifiable by having actual_y
        coordinates of less than -12.
        """
        distance_from_strike_zone_center = (
            abs(0-pitch.actual_x) + abs(0-pitch.actual_y)
        )
        difficulty = (distance_from_strike_zone_center**2 / 20) * 0.03
        difficulty /= self.pitch_blocking
        if random.random() < difficulty:
            return False
        else:
            return True

    def decide_immediate_goal(self, playing_action):
        """Decide immediate goal other than playing the ball.

        This method is called by batted_ball.get_obligated_fielder()
        """
        batted_ball = playing_action.batted_ball
        if self.making_goal_revision:
            self._moving_left = self._moving_right = self._straight_ahead_x = self._straight_ahead_y = False
            self.at_goal = False
            self._slope = None
            self.making_goal_revision = False
            # If you are now playing the ball by virtue of batted_ball.get_reread_by_fielders()'s
            # computation, make sure you are not still playing_action.cut_off_man and not still
            # attributed as backing up the catch
            if self is playing_action.cut_off_man:
                playing_action.cut_off_man = None
            self.backing_up_the_catch = False
        if not self.playing_the_ball:
            if self.position == "1B":
                # Cover first base
                self.immediate_goal = [63.5, 63.5]
                # Get there ASAP, i.e., act at full speed
                self.dist_per_timestep = (
                    0.1/self.person.body.full_speed_seconds_per_foot
                )
                playing_action.covering_first = self
            elif self.position == "2B":
                # If ball is hit to the left of second base or shortstop is playing the ball,
                # cover second; else, if the ball is hit to the right of second, cover first
                shortstop = batted_ball.at_bat.fielders[5]
                if batted_ball.horizontal_launch_angle <= 0 or shortstop.playing_the_ball:
                    # Cover second base
                    self.immediate_goal = [0, 127]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.covering_second = self
                elif not playing_action.covering_first:
                    # Cover first base
                    self.immediate_goal = [63.5, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.covering_first = self
                elif batted_ball.hit_to_outfield and batted_ball.horizontal_launch_angle >= 0.0:
                    # Cut off the coming throw as a potential relay man -- go to about 60% of the
                    # distance from home plate to where the ball will be fielded
                    player_fielding_the_ball = next(f for f in self.team.players if f.playing_the_ball)
                    self.immediate_goal = [player_fielding_the_ball.immediate_goal[0]*0.6,
                                           player_fielding_the_ball.immediate_goal[1]*0.6]
                    playing_action.cut_off_man = self
                else:
                    # Back up first base
                    self.immediate_goal = [72, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_first = self
            elif self.position == "3B":
                # Cover third base
                self.immediate_goal = [-63.5, 63.5]
                # Get there ASAP, i.e., act at full speed
                self.dist_per_timestep = (
                    0.1/self.person.body.full_speed_seconds_per_foot
                )
                playing_action.covering_third = self
            elif self.position == "SS":
                # Put here in the control sequence because he covers second if 2B isn't and
                # covers third if 3B isn't, and thus needs to wait and see what they decide first
                if not playing_action.covering_third:
                    # Cover third base
                    self.immediate_goal = [-63.5, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.covering_third = self
                elif not playing_action.covering_second:
                    # Cover second base
                    self.immediate_goal = [0, 127]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.covering_second = self
                elif batted_ball.hit_to_outfield and batted_ball.horizontal_launch_angle < 0.0:
                    # Cut off the coming throw as a potential relay man -- go to about 60% of the
                    # distance from home plate to where the ball will be fielded
                    player_fielding_the_ball = next(f for f in self.team.players if f.playing_the_ball)
                    self.immediate_goal = [player_fielding_the_ball.immediate_goal[0]*0.6,
                                           player_fielding_the_ball.immediate_goal[1]*0.6]
                    playing_action.cut_off_man = self
                else:
                    if playing_action.running_to_second or not playing_action.running_to_third:
                        # Back-up second base
                        self.immediate_goal = [0, 135]
                        # Get there ASAP, i.e., act at full speed
                        self.dist_per_timestep = (
                            0.1/self.person.body.full_speed_seconds_per_foot
                        )
                        playing_action.backing_up_second = self
                    else:
                        # Back-up third base
                        self.immediate_goal = [-72, 63.5]
                        # Get there ASAP, i.e., act at full speed
                        self.dist_per_timestep = (
                            0.1/self.person.body.full_speed_seconds_per_foot
                        )
                        playing_action.backing_up_third = self
            elif self.position == "LF":
                if batted_ball.horizontal_launch_angle < 0.0:
                    if batted_ball.destination == "left" or batted_ball.destination == "deep left":
                        if not self.called_off_by:
                            # Play the ball and call any infielders off who want to chase the deep ball
                            self.playing_the_ball = True
                    elif batted_ball.destination == "shallow left" or batted_ball.destination == "shallow left-center":
                        if not self.called_off_by:
                            thresh = 0.5 * self.audacity
                            if random.random() < thresh:
                                # Call off infielder on next timestep
                                self.playing_the_ball = True
                    if not self.playing_the_ball:
                        # Back up the catch -- do this by making a goal to go to where the batted ball
                        # will be four-six timesteps later on its trajectory if it were to continue
                        # on it uninterrupted by the fielder playing the ball's fielding attempt
                        fielder_playing_the_ball = next(f for f in self.team.players if f.playing_the_ball)
                        timestep_i_will_shoot_for = fielder_playing_the_ball.timestep_of_planned_fielding_attempt
                        for i in xrange(5):
                            timestep_i_will_shoot_for += 0.1
                        if timestep_i_will_shoot_for in batted_ball.position_at_timestep:
                            self.immediate_goal = batted_ball.position_at_timestep[timestep_i_will_shoot_for][:2]
                        else:
                            if playing_action.at_bat.game.trace:
                                print "timestep {} not in batted_ball.position_at_timestep".format(
                                    timestep_i_will_shoot_for
                                )
                            self.immediate_goal = batted_ball.final_location
                        if playing_action.at_bat.game.trace:
                            print "-- {} ({}) will back up the catch by moving to [{}, {}] [{}]".format(
                                self.person.last_name, self.position, int(self.immediate_goal[0]), int(self.immediate_goal[1]),
                                batted_ball.time_since_contact
                            )
                        self.backing_up_the_catch = True
                elif batted_ball.horizontal_launch_angle >= 0.0:
                    # Back-up third base
                    self.immediate_goal = [-72, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_third = self
            elif self.position == "RF":
                if batted_ball.horizontal_launch_angle >= 0.0:
                    if batted_ball.destination == "right" or batted_ball.destination == "deep right":
                        if not self.called_off_by:
                            # Play the ball and call any infielders off who want to chase the deep ball
                            self.playing_the_ball = True
                    elif batted_ball.destination == "shallow right" or batted_ball.destination == "shallow right-center":
                        if not self.called_off_by:
                            thresh = 0.5 * self.audacity
                            if random.random() < thresh:
                                # Call off infielder on next timestep
                                self.playing_the_ball = True
                    if not self.playing_the_ball:
                        # Back up the catch -- do this by making a goal to go to where the batted ball
                        # will be four-six timesteps later on its trajectory if it were to continue
                        # on it uninterrupted by the fielder playing the ball's fielding attempt
                        fielder_playing_the_ball = next(f for f in self.team.players if f.playing_the_ball)
                        timestep_i_will_shoot_for = fielder_playing_the_ball.timestep_of_planned_fielding_attempt
                        for i in xrange(5):
                            timestep_i_will_shoot_for += 0.1
                        if timestep_i_will_shoot_for in batted_ball.position_at_timestep:
                            self.immediate_goal = batted_ball.position_at_timestep[timestep_i_will_shoot_for][:2]
                        else:
                            if playing_action.at_bat.game.trace:
                                print "timestep {} not in batted_ball.position_at_timestep".format(
                                    timestep_i_will_shoot_for
                                )
                            self.immediate_goal = batted_ball.final_location
                        if playing_action.at_bat.game.trace:
                            print "-- {} ({}) will back up the catch by moving to [{}, {}] [{}]".format(
                                self.person.last_name, self.position, int(self.immediate_goal[0]), int(self.immediate_goal[1]),
                                batted_ball.time_since_contact
                            )
                        self.backing_up_the_catch = True
                elif batted_ball.horizontal_launch_angle < 0.0:
                    # Back up first base
                    self.immediate_goal = [72, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_first = self
            elif self.position == "CF":
                # Put here in control sequence because if LF or RF is already backing up the catch,
                # CF should back-up at a different position
                if batted_ball.destination == "center" or batted_ball.destination == "deep center":
                    if not self.called_off_by:
                        self.playing_the_ball = True
                elif batted_ball.destination == "shallow center":
                    if not self.called_off_by:
                        thresh = 0.5 * self.audacity
                        if random.random() < thresh:
                            # Call off infielder on next timestep
                            self.playing_the_ball = True
                if not self.playing_the_ball:
                    if batted_ball.hit_to_outfield:
                        # Back up the catch -- do this by making a goal to go to where the batted ball
                        # will be four-six timesteps later on its trajectory if it were to continue
                        # on it uninterrupted by the fielder playing the ball's fielding attempt
                        fielder_playing_the_ball = next(f for f in self.team.players if f.playing_the_ball)
                        timestep_i_will_shoot_for = fielder_playing_the_ball.timestep_of_planned_fielding_attempt
                        for i in xrange(5):
                            timestep_i_will_shoot_for += 0.1
                        if timestep_i_will_shoot_for in batted_ball.position_at_timestep:
                            someone_else_already_backing_up_catch = (
                                any(f for f in batted_ball.at_bat.fielders if f.backing_up_the_catch)
                            )
                            if not someone_else_already_backing_up_catch:
                                self.immediate_goal = batted_ball.position_at_timestep[timestep_i_will_shoot_for][:2]
                            else:
                                # If someone is already backing up the catch, go about six feet behind where
                                # they will be standing to back it up
                                self.immediate_goal = (
                                    batted_ball.position_at_timestep[timestep_i_will_shoot_for][0],
                                    batted_ball.position_at_timestep[timestep_i_will_shoot_for][1] + 6
                                )
                        else:
                            if playing_action.at_bat.game.trace:
                                print "timestep {} not in batted_ball.position_at_timestep".format(timestep_i_will_shoot_for)
                            self.immediate_goal = batted_ball.final_location
                        if playing_action.at_bat.game.trace:
                            print "-- {} ({}) will back up the catch by moving toward [{}, {}] [{}]".format(
                                self.person.last_name, self.position, int(self.immediate_goal[0]), int(self.immediate_goal[1]),
                                batted_ball.time_since_contact
                            )
                        self.backing_up_the_catch = True
                    else:
                        # Back-up second base
                        self.immediate_goal = [0, 135]
                        # Get there ASAP, i.e., act at full speed
                        self.dist_per_timestep = (
                            0.1/self.person.body.full_speed_seconds_per_foot
                        )
                        playing_action.backing_up_second = self
            elif self.position == "C":
                # Stay put and cover home
                self.immediate_goal = self.location
                playing_action.covering_home = self
            elif self.position == "P":
                if self.team.roster.catcher.playing_the_ball:
                    # Cover home (obviously should be backing up bases and stuff too TODO)
                    self.immediate_goal = [0, 0]
                    playing_action.covering_home = self
                elif playing_action.running_to_home:
                    # Back up home plate
                    self.immediate_goal = [0, -8]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_home = self
                elif not playing_action.backing_up_first:
                    # Back up first base
                    self.immediate_goal = [72, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_first = self
                elif playing_action.running_to_second and not playing_action.backing_up_second:
                    # Back-up second base -- if ball is out to the outfield, back it up
                    # toward the pitcher's mound; if it's hit to the infield, back it up
                    # toward center field
                    if batted_ball.hit_to_outfield:
                        self.immediate_goal = [0, 116]
                    else:
                        self.immediate_goal = [0, 135]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_second = self
                else:
                    # Back-up third base
                    self.immediate_goal = [-72, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.person.body.full_speed_seconds_per_foot
                    )
                    playing_action.backing_up_third = self
        # Determine the slope of a straight line between fielder's
        # current location and the goal location
        x_change = self.immediate_goal[0]-self.location[0]
        y_change = self.immediate_goal[1]-self.location[1]
        if x_change == 0 and y_change == 0:
            self.at_goal = True
        elif x_change == 0:
            self._straight_ahead_y = True
        elif y_change == 0:
            self._straight_ahead_x = True
        else:
            self._slope = y_change / float(x_change)
        # Determine whether the goal is to the left (this affects
        # computation of where the player gets to as player.act()
        # is called each timestep)
        if x_change < 0:
            self._moving_left = True
        elif x_change > 0:
            self._moving_right = True
        # Miscellanea that needs to be handled
        if not self.playing_the_ball:
            self.attempting_fly_out = False

    def act(self, batted_ball):
        """Move toward the location that is your immediate goal."""
        # If you're playing the ball, potentially call off teammates of a lesser
        # fielding priority that are also playing the ball
        if not batted_ball.fielded_by and self.playing_the_ball and batted_ball.time_since_contact > 1+random.random():
            other_fielders_playing_the_ball = (
                f for f in batted_ball.at_bat.fielders if f.playing_the_ball and f is not self
            )
            if other_fielders_playing_the_ball:
                for teammate in other_fielders_playing_the_ball:
                    if (batted_ball.fielding_priorities[self.position] >=
                            batted_ball.fielding_priorities[teammate.position]):
                        dist_from_teammate_to_bb = (
                            math.hypot(teammate.location[0]-batted_ball.location[0],
                                       teammate.location[1]-batted_ball.location[1])
                        )
                        # If teammate isn't right near the ball already, call him off
                        if dist_from_teammate_to_bb > 10:
                            teammate.called_off_by = self
                            teammate.playing_the_ball = False
                            if batted_ball.at_bat.game.trace:
                                print "-- {} ({}) called off {} ({}) [{}]".format(
                                    self.person.last_name, self.position, teammate.person.last_name, teammate.position,
                                    batted_ball.time_since_contact
                                )
                        # If he is, he actually will call you off here (and any other
                        # teammates who were going to play the ball, if any)
                        else:
                            self.called_off_by = teammate
                            self.playing_the_ball = False
                            if batted_ball.at_bat.game.trace:
                                print "-- {} ({}) called off {} ({}) [{}]".format(
                                    teammate.person.last_name, teammate.position, self.person.last_name, self.position,
                                    batted_ball.time_since_contact
                                )
                            for other_teammate in other_fielders_playing_the_ball:
                                if other_teammate is not teammate:
                                    if batted_ball.at_bat.game.trace:
                                        print "-- {} ({}) called off {} ({}) [{}]".format(
                                            teammate.person.last_name, teammate.position,
                                            other_teammate.person.last_name,
                                            other_teammate.position, batted_ball.time_since_contact
                                        )
                                    other_teammate.called_off_by = teammate
                                    other_teammate.playing_the_ball = False

        # If you just got called off, revise your immediate goal
        if self.called_off_by:
            self.making_goal_revision = True
            self.decide_immediate_goal(playing_action=batted_ball.at_bat.playing_action)
        if not self.at_goal:
            # If you're within a timestep of movement of being at your goal,
            # we'll say you're there
            if (math.hypot(self.immediate_goal[0]-self.location[0],
                           self.immediate_goal[1]-self.location[1]) <= self.dist_per_timestep):
                # If you're within a timestep of your goal, we just say you're there,
                # mostly so that fielders don't go too far past their goal
                self.at_goal = True
                self.location = [self.immediate_goal[0], self.immediate_goal[1]]
            else:
                # Move toward your goal
                dist = self.dist_per_timestep
                x, y = self.location
                if self._straight_ahead_x:
                    if self.immediate_goal[0] <= self.location[0]:
                        new_x = x - dist
                    else:
                        new_x = x + dist
                    new_y = y
                elif self._straight_ahead_y:
                    new_x = x
                    if self.immediate_goal[1] <= self.location[1]:
                        new_y = y - dist
                    else:
                        new_y = y + dist
                elif self._moving_left:
                    new_x = x + (-1*dist)/(math.sqrt(1+self._slope**2))
                    new_y = y + (-1*self._slope*dist)/(math.sqrt(1+self._slope**2))
                elif self._moving_right:
                    new_x = x + dist/(math.sqrt(1+self._slope**2))
                    new_y = y + (self._slope*dist)/(math.sqrt(1+self._slope**2))
                else:
                    raise Exception(self.position + " tried to move about the field without" +
                                    "proper bearing assigned.")
                self.location = new_x, new_y
        if self.at_goal:
            # If you're playing the ball and the ball is here, as indicated by it being
            # the timestep that you planned to make your fielding attempt, then get
            # ready to make it
            if self.playing_the_ball and not batted_ball.fielded_by:
                if batted_ball.time_since_contact >= self.timestep_of_planned_fielding_attempt:
                    batted_ball.fielder_with_chance = self
                    dist_from_fielder_to_bb = (
                        math.hypot(self.location[0]-batted_ball.location[0],
                                   self.location[1]-batted_ball.location[1])
                    )
                    if dist_from_fielder_to_bb > 1:
                        print "-- {} is a 'fielder with chance' but is {} ft from the batted ball [{}]".format(
                            self.person.last_name, round(dist_from_fielder_to_bb, 1), batted_ball.time_since_contact
                        )
                        raw_input("")

    def baserun(self, playing_action):
        """Run along the base paths, as appropriate."""
        batted_ball = playing_action.batted_ball
        if not self.baserunning_full_speed:
            self.baserunning_full_speed = True
            self.tentatively_baserunning = False
            self.retreating = False
            if playing_action.at_bat.game.trace:
                print "-- {} is running full speed for the next base [{}]".format(
                    self.person.last_name, batted_ball.time_since_contact
                )
            if self is playing_action.running_to_first:
                # Otherwise they won't make conduct_offseason_activity on the first timestep
                self.percent_to_base = (
                    batted_ball.time_since_contact/self.speed_home_to_first
                )
        else:  # Already decided to baserun full-speed
            # Advance along the base path
            if self is playing_action.running_to_first:
                # Baserunner percentage to base is calculated differently for
                # batter-runners heading to first to account for running delay from
                # the duration of the follow-through, discarding of the bat, etc.
                self.percent_to_base = (
                    batted_ball.time_since_contact/self.speed_home_to_first
                )
            else:
                self.percent_to_base += (0.1/self.person.body.full_speed_seconds_per_foot) / 90
            # If you've safely reached base, either stay there and make it known that
            # you've reached the base safely, or round it and decide whether to actually
            # advance to the next base
            if self.percent_to_base >= 1.0:
                self.forced_to_advance = False
                # If batter-runner, make a note that he *did* reach this base safely, regardless of whether they
                # end up out on the throw, for later purposes of scoring the hit
                if not self.advancing_due_to_error:
                    if self is playing_action.running_to_first or self is playing_action.retreating_to_first:
                        self.base_reached_on_hit = "1B"
                    elif self is playing_action.running_to_second or self is playing_action.retreating_to_second:
                        self.base_reached_on_hit = "2B"
                    elif self is playing_action.running_to_third or self is playing_action.retreating_to_third:
                        self.base_reached_on_hit = "3B"
                    elif self is playing_action.running_to_home:
                        self.base_reached_on_hit = "H"
                if not self.will_round_base and not self.safely_on_base:
                    if playing_action.at_bat.game.trace:
                        print "-- {} has safely reached base [{}]".format(self.person.last_name, batted_ball.time_since_contact)
                    self.safely_on_base = True
                    # Record the precise time the runner reached base, for potential use by umpire.call_play_at_base()
                    if not self.timestep_reached_base:
                        surplus_percentage_to_base = self.percent_to_base-1
                        surplus_distance = surplus_percentage_to_base*90
                        surplus_time = surplus_distance * self.person.body.full_speed_seconds_per_foot
                        self.timestep_reached_base = batted_ball.time_since_contact - surplus_time
                    self.percent_to_base = 1.0
                    if playing_action.running_to_home is self:
                        self.safely_home = True
                        playing_action.running_to_home = None
                elif self.will_round_base:
                    # We can't have, e.g., two playing_action.running_to_thirds, so if the
                    # preceding runner is rounding his base -- which, if you are rounding
                    # your base, he *is* -- but hasn't quite got there yet, while you
                    # already have, keep incrementing your baserunning conduct_offseason_activity for a few
                    # timesteps until he rounds the base, at which point we can switch, e.g.,
                    # him to playing_action.running_to_home and you to playing_action.running_to_third
                    next_basepath_is_clear = False
                    if self is playing_action.running_to_third:
                        if not playing_action.running_to_home or playing_action.running_to_home.out:
                            next_basepath_is_clear = True
                    elif self is playing_action.running_to_second:
                        if not playing_action.running_to_third or playing_action.running_to_third.out:
                            next_basepath_is_clear = True
                    elif self is playing_action.running_to_first:
                        if not playing_action.running_to_second or playing_action.running_to_second.out:
                            next_basepath_is_clear = True
                    if not next_basepath_is_clear:
                        if playing_action.at_bat.game.trace:
                            print ("-- {} is waiting for the preceding runner to round the base "
                                   "to technically round the base [{}]").format(
                                self.person.last_name, batted_ball.time_since_contact
                            )
                    if next_basepath_is_clear:
                        # Round the base, retaining the remainder of last timestep's baserunning conduct_offseason_activity
                        self.percent_to_base -= 1.0
                        self.will_round_base = False
                        self._decided_finish = False
                        if self is playing_action.running_to_first:
                            if playing_action.at_bat.game.trace:
                                print "-- {} has rounded first [{}]".format(self.person.last_name, batted_ball.time_since_contact)
                            playing_action.running_to_first = None
                            playing_action.running_to_second = self
                        elif self is playing_action.running_to_second:
                            if playing_action.at_bat.game.trace:
                                print "-- {} has rounded second [{}]".format(self.person.last_name, batted_ball.time_since_contact)
                            playing_action.running_to_second = None
                            playing_action.running_to_third = self
                        elif self is playing_action.running_to_third:
                            if playing_action.at_bat.game.trace:
                                print "-- {} has rounded third [{}]".format(self.person.last_name, batted_ball.time_since_contact)
                            playing_action.running_to_third = None
                            playing_action.running_to_home = self
                        self.estimate_whether_you_can_beat_throw(playing_action=playing_action)
                        if self.believes_he_can_beat_throw:
                            self.taking_next_base = True
                            if playing_action.at_bat.game.trace:
                                print "-- {} is taking the next base because he believes he can beat the throw [{}]".format(
                                    self.person.last_name, batted_ball.time_since_contact
                                )
                        elif not batted_ball.fielded_by:
                            # Don't retreat immediately -- tentatively advance as far as you can and
                            # wait to see if the ball is fielded cleanly
                            self.tentatively_baserun(playing_action=playing_action)
                        elif batted_ball.fielded_by:
                            self.retreat(playing_action=playing_action)
            # If you haven't already, decide whether to round the base you are advancing to, which will
            # be at a 10% reduction in your percentage to base
            elif not self._decided_finish and self.percent_to_base > 0.49:
                # Of course, you will not be rounding home
                if self is playing_action.running_to_home:
                    self.will_round_base = False
                    self._decided_finish = True
                # For all other baserunners, make decision based on whether the ball has been fielded
                # already, and if it hasn't, whether it was hit to the infield or the outfield -- this
                # reasoning is precluded, however, if there is an immediately preceding runner who
                # himself will not round the base
                else:
                    if self is playing_action.running_to_first:
                        preceding_runner = playing_action.running_to_second
                    elif self is playing_action.running_to_second:
                        preceding_runner = playing_action.running_to_third
                    elif self is playing_action.running_to_third:
                        preceding_runner = playing_action.running_to_home
                    else:
                        print ("Error 8181: person.baserun() called for {} ({}), who is none of "
                               "playing_action.running_to_first, running_to_second, running_to_third, "
                               "or running_to_home").format(self.name, self.position)
                    next_basepath_is_clear = False
                    if not preceding_runner:
                        next_basepath_is_clear = True
                    elif preceding_runner and preceding_runner.out:
                        next_basepath_is_clear = True
                    elif preceding_runner and preceding_runner.will_round_base:
                        next_basepath_is_clear = True
                    elif preceding_runner and preceding_runner is playing_action.running_to_home:
                        next_basepath_is_clear = True
                    if next_basepath_is_clear:
                        if not batted_ball.fielded_by and batted_ball.hit_to_outfield:
                            self.will_round_base = True
                            self._decided_finish = True
                            self.percent_to_base -= 0.1
                            if self is playing_action.running_to_third:
                                base = "third"
                            elif self is playing_action.running_to_second:
                                base = "second"
                            else:  # elif self is playing_action.running_to_first:
                                base = "first"
                            if playing_action.at_bat.game.trace:
                                print ("-- {} will round {} because ball is hit to outfield "
                                       "and hasn't been fielded yet [{}]").format(
                                    self.person.last_name, base, batted_ball.time_since_contact
                                )
                        else:
                            self.will_round_base = False
                            self._decided_finish = True
                            if self is playing_action.running_to_third:
                                base = "third"
                            elif self is playing_action.running_to_second:
                                base = "second"
                            else:  # elif self is playing_action.running_to_first:
                                base = "first"
                            if playing_action.at_bat.game.trace:
                                if batted_ball.hit_to_infield:
                                    print "-- {} will not round {} because the ball was hit to infield [{}]".format(
                                        self.person.last_name, base, batted_ball.time_since_contact)
                                elif batted_ball.fielded_by:
                                    print ("-- {} will not round {} because, even though it was hit "
                                           "to outfield, the ball has been fielded already [{}]").format(
                                        self.person.last_name, base, batted_ball.time_since_contact)
                    elif not next_basepath_is_clear and self.percent_to_base >= 0.85:
                        # At this point, it looks like the preceding runner won't be rounding
                        # his base, so you'll be forced to stand pat at the immediately coming
                        # base, should you arrive to it safely
                        self.will_round_base = False
                        self._decided_finish = True
                        if self is playing_action.running_to_third:
                            base = "third"
                        elif self is playing_action.running_to_second:
                            base = "second"
                        else:  # elif self is playing_action.running_to_first:
                            base = "first"
                        if playing_action.at_bat.game.trace:
                            print ("-- {} will not round {} because the preceding runner {} "
                                   "is not rounding his base [{}]").format(
                                self.person.last_name, base, preceding_runner.person.last_name,
                                batted_ball.time_since_contact
                            )

        ## TODO ADD DIFFICULTY TO FIELD BALL AND CHANCE OF ERROR FOR THROW IF
        ## BATTED_BALL.HEADING_TO_SECOND, due to batter-runner threatening
        ## to take second

    def tentatively_baserun(self, playing_action):
        """Move along the base paths tentatively before resolution of a fly-ball fielding chance.

        Upon the ball being fielded, tentative baserunners will automatically realize (by virtue of
        playing_action._transpire()) they have to retreat and will begin to do so. If the ball is
        not fielded cleanly, playing_action._transpire() will cause tentative baserunners to consider
        whether they could now make it to their next base before a throw could, and if they believe
        they could, they'll start baserunning full speed."""
        batted_ball = playing_action.batted_ball
        if not self.tentatively_baserunning:
            self.tentatively_baserunning = True
            self.baserunning_full_speed = False
            self.retreating = False
            if playing_action.at_bat.game.trace:
                print "-- {} is tentatively advancing toward the next base [{}]".format(
                    self.person.last_name, batted_ball.time_since_contact
                )
        else:  # Already decided to tentatively baserun
            if not self._done_tentatively_advancing:
                # Determine what your percentage to the next base would be if you decide to
                # advance further on this timestep at 65% full speed -- this, when multiplied by 90,
                # conveniently represents the distance required to retreat would be from that position
                percent_to_base_upon_advancement = (
                    self.percent_to_base + (0.1/(self.person.body.full_speed_seconds_per_foot*1.53)) / 90
                )
                if percent_to_base_upon_advancement < 1.0:  # Don't advance onto the next base path -- too weird
                    # Estimate how long it would take to retreat if the fly-ball were caught, given
                    # your positioning on the base paths if you *were* to advance on this timestep
                    time_expected_for_me_to_retreat = (
                        (percent_to_base_upon_advancement * 90) * self.person.body.full_speed_seconds_per_foot
                    )
                    # Estimate how long the potential throw to the preceding base you would be
                    # retreating to would take -- assume typical throwing velocity and release time
                    player_fielding_the_ball = next(f for f in batted_ball.at_bat.fielders if f.playing_the_ball)
                    if self is playing_action.running_to_second:
                        preceding_base_coords = [63.5, 63.5]
                    elif self is playing_action.running_to_third:
                        preceding_base_coords = [0, 127]
                    elif self is playing_action.running_to_home:
                        preceding_base_coords = [-63.5, 63.5]
                    dist_from_fielding_chance_to_preceding_base = (
                        math.hypot(player_fielding_the_ball.immediate_goal[0]-preceding_base_coords[0],
                                   player_fielding_the_ball.immediate_goal[1]-preceding_base_coords[1])
                    )
                    time_expected_for_throw_release = (
                        math.sqrt(dist_from_fielding_chance_to_preceding_base) * 0.075
                    )
                    time_expected_for_throw_itself = self.estimate_time_for_throw_to_reach_target(
                        distance=dist_from_fielding_chance_to_preceding_base,
                        initial_velocity=110  # 110 ft/s = 75 MPH (typical velocity)
                    )
                    time_expected_for_throw_to_preceding_base = (
                        time_expected_for_throw_release + time_expected_for_throw_itself
                    )
                    # If you think you could still retreat safely, if the ball is caught, after advancing
                    # further on this timestep, then advance
                    if time_expected_for_me_to_retreat < time_expected_for_throw_to_preceding_base:
                        self.percent_to_base = percent_to_base_upon_advancement
                    else:
                        self._done_tentatively_advancing = True
                        if playing_action.at_bat.game.trace:
                            print "-- {} is waiting at {} of the way until the fielding chance is resolved [{}]".format(
                                self.person.last_name, round(self.percent_to_base, 2), batted_ball.time_since_contact
                            )

    def retreat(self, playing_action):
        """Retreat to the preceding base."""
        batted_ball = playing_action.batted_ball
        if not self.retreating:
            self.percent_to_base = 1 - self.percent_to_base
            self.retreating = True
            self.baserunning_full_speed = False
            self.tentatively_baserunning = False
            if self is playing_action.running_to_second:
                playing_action.running_to_second = None
                playing_action.retreating_to_first = self
                if playing_action.at_bat.game.trace:
                    if not self.forced_to_retreat:
                        print ("-- {} is retreating to first because the ball was fielded or because he does "
                               "not believe he can beat the throw [{}]").format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
                    elif self.forced_to_retreat:
                        print "-- {} is retreating to first to tag up [{}]".format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
            elif self is playing_action.running_to_third:
                playing_action.running_to_third = None
                playing_action.retreating_to_second = self
                if playing_action.at_bat.game.trace:
                    if not self.forced_to_retreat:
                        print ("-- {} is retreating to second because the ball was fielded or because he does "
                               "not believe he can beat the throw [{}]").format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
                    elif self.forced_to_retreat:
                        print "-- {} is retreating to second to tag up [{}]".format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
            elif self is playing_action.running_to_home:
                playing_action.running_to_home = None
                playing_action.retreating_to_third = self
                if playing_action.at_bat.game.trace:
                    if not self.forced_to_retreat:
                        print ("-- {} is retreating to third because the ball was fielded or because he does "
                               "not believe he can beat the throw [{}]").format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
                    elif self.forced_to_retreat:
                        print "-- {} is retreating to third to tag up [{}]".format(
                            self.person.last_name, batted_ball.time_since_contact
                        )
        elif self.retreating:  # Already started retreating
            self.percent_to_base += (0.1/self.person.body.full_speed_seconds_per_foot) / 90
            if self.percent_to_base >= 1.0:
                self.safely_on_base = True
                # Determine the exact timestep that you reached base
                if not self.timestep_reached_base:
                    surplus_percentage_to_base = self.percent_to_base-1
                    surplus_distance = surplus_percentage_to_base*90
                    surplus_time = surplus_distance * self.person.body.full_speed_seconds_per_foot
                    self.timestep_reached_base = batted_ball.time_since_contact - surplus_time
                self.percent_to_base = 1.0
                # Decide whether to quickly tag-up and attempt to advance to the next base --
                # if the next base path is not clear, do not advance
                next_base_path_is_clear = True
                if self is playing_action.retreating_to_first:
                    if playing_action.retreating_to_second:
                        next_base_path_is_clear = False
                elif self is playing_action.retreating_to_second:
                    if playing_action.retreating_to_third:
                        next_base_path_is_clear = False
                if next_base_path_is_clear and self.forced_to_retreat:
                    # (If you weren't forced to retreat, you're retreating because you
                    # already ascertained (via estimate_whether_you_can_beat_throw) that you
                    # wouldn't be able to beat a throw if you attempted to advance to the
                    # next base)
                    self.percent_to_base = 0.0
                    self.estimate_whether_you_can_beat_throw(playing_action=playing_action)
                    if self.believes_he_can_beat_throw:
                        if self is playing_action.retreating_to_first:
                            if playing_action.at_bat.game.trace:
                                print ("-- {} tagged up at first and will now attempt to take second "
                                       "because he believes he can beat any throw there [{}]").format(
                                    self.person.last_name, batted_ball.time_since_contact)
                            playing_action.retreating_to_first = None
                            playing_action.running_to_second = self
                        elif self is playing_action.retreating_to_second:
                            if playing_action.at_bat.game.trace:
                                print ("-- {} tagged up at second and will now attempt to take third "
                                       "because he believes he can beat any throw there [{}]").format(
                                    self.person.last_name, batted_ball.time_since_contact)
                            playing_action.retreating_to_second = None
                            playing_action.running_to_third = self
                        elif self is playing_action.retreating_to_third:
                            if playing_action.at_bat.game.trace:
                                print ("-- {} tagged up at third and will now attempt to run home "
                                       "because he believes he can beat any throw there [{}]").format(
                                    self.person.last_name, batted_ball.time_since_contact)
                            playing_action.retreating_to_third = None
                            playing_action.running_to_home = self
                        self.forced_to_retreat = False
                        self._decided_finish = False
                        self.will_round_base = False
                        self.taking_next_base = False
                        self.safely_on_base = False
                        self.baserun(playing_action=playing_action)
                    else:
                        if self is playing_action.retreating_to_first:
                            if playing_action.at_bat.game.trace:
                                print "-- {} tagged up at first and will remain there [{}]".format(
                                    self.person.last_name, batted_ball.time_since_contact
                                )
                        elif self is playing_action.retreating_to_second:
                            if playing_action.at_bat.game.trace:
                                print "-- {} tagged up at second and will remain there [{}]".format(
                                    self.person.last_name, batted_ball.time_since_contact
                                )
                        elif self is playing_action.retreating_to_third:
                            if playing_action.at_bat.game.trace:
                                print "-- {} tagged up at third and will remain there [{}]".format(
                                    self.person.last_name, batted_ball.time_since_contact
                                )

    def estimate_whether_you_can_beat_throw(self, playing_action):
        batted_ball = playing_action.batted_ball
        if self is playing_action.running_to_second or self is playing_action.retreating_to_first:
            # If retreating, it is just to tag up, so the consideration is whether to
            # then attempt to advance upon tagging up
            next_base = "2B"
            next_base_coords = (0, 127)
        elif self is playing_action.running_to_third or self is playing_action.retreating_to_second:
            next_base = "3B"
            next_base_coords = (-63.5, 63.5)
        elif self is playing_action.running_to_home or self is playing_action.retreating_to_third:
            next_base = "H"
            next_base_coords = (0, 0)
        # Estimate how long it would take you to reach your next base
        dist_from_me_to_next_base = 90 - (self.percent_to_base*90)
        time_expected_for_me_to_reach_next_base = (
            dist_from_me_to_next_base * self.person.body.full_speed_seconds_per_foot
        )
        # If there is no throw yet, form a preliminary model of it and estimate how
        # long it would take to reach the base you are considering advancing to; do
        # this assuming a fairly typical 75 MPH throwing velocity and pretty decent
        # release time
        if not playing_action.throw:
            # TODO player learns outfielders' arm strengths
            # TODO player guesses which base the throw will target
            player_fielding_the_ball = next(f for f in batted_ball.at_bat.fielders if f.playing_the_ball)
            time_expected_for_fielder_approach_to_batted_ball = (
                player_fielding_the_ball.timestep_of_planned_fielding_attempt - batted_ball.time_since_contact
            )
            if batted_ball.bobbled:
                # Add on the time it will take for the fielder to reorient himself to pick up the bobbled
                # ball -- if the batted ball gets reread by fielders after a total fielding miss,
                # reorientation time will already have been factored in to player_fielding_the_ball.
                # timestep_of_planned_fielding_attempt
                time_expected_for_fielder_approach_to_batted_ball += \
                    player_fielding_the_ball.reorienting_after_fielding_miss
            dist_from_fielding_chance_to_next_base = (
                math.hypot(player_fielding_the_ball.immediate_goal[0]-next_base_coords[0],
                           player_fielding_the_ball.immediate_goal[1]-next_base_coords[1])
            )
            time_expected_for_throw_release = (
                math.sqrt(dist_from_fielding_chance_to_next_base) * 0.075
            )

            time_expected_for_throw_itself = self.estimate_time_for_throw_to_reach_target(
                distance=dist_from_fielding_chance_to_next_base, initial_velocity=110.  # 110 ft/s = 75 MPH
            )
            time_expected_for_throw_to_next_base = (
                time_expected_for_fielder_approach_to_batted_ball +
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
        # If there is a throw already, reason about how long it would take to reach the base you
        # are considering advancing to
        elif playing_action.throw:
            throw = playing_action.throw
            # Estimate how long it will take throw to reach its target
            time_expected_for_throw_to_reach_target = throw.time_remaining_until_target_is_reached
            # If the throw's target is not the base your considering advancing to, estimate
            # how long a secondary throw from the target to your next base would take
            if throw.base == next_base:
                time_expected_for_throw_to_next_base = time_expected_for_throw_to_reach_target
            else:
                if throw.base == "1B":
                    throw_target_coords = (63.5, 63.5)
                elif throw.base == "2B":
                    throw_target_coords = (0, 127)
                elif throw.base == "3B":
                    throw_target_coords = (-63.5, 63.5)
                elif throw.base == "H":
                    throw_target_coords = (0, 0)
                else:
                    throw_target_coords = throw.thrown_to.location
                try:
                    distance_from_throw_target_to_next_base = (
                        math.hypot(throw_target_coords[0]-next_base_coords[0],
                                   throw_target_coords[1]-next_base_coords[1])
                    )
                except:
                    print "no next base coords for {}".format(self.name)
                time_expected_for_throw_release = (
                    math.sqrt(distance_from_throw_target_to_next_base) * 0.075
                )
                time_expected_for_throw_itself = self.estimate_time_for_throw_to_reach_target(
                    distance=distance_from_throw_target_to_next_base, initial_velocity=110.0  # 110 ft/s = 75 MPH
                )
                time_expected_for_throw_to_next_base = (
                    time_expected_for_throw_to_reach_target +
                    time_expected_for_throw_release + time_expected_for_throw_itself
                )
        # Determine the realistic estimate of the difference, in seconds, between when the
        # runner is expected to make it to the next base and when a throw would make it to
        # the next base, given what we calculated above -- negative values represent the
        # runner beating the throw
        realistic_estimate_of_difference = (
            time_expected_for_me_to_reach_next_base - time_expected_for_throw_to_next_base
        )

        # Pollute this estimate according to the player's confidence
        # if realistic_estimate_of_difference <= 0:
        #     my_estimate_of_difference = realistic_estimate_of_difference + self.confidence
        # else:
        #     my_estimate_of_difference = realistic_estimate_of_difference / self.confidence
        my_estimate_of_difference = realistic_estimate_of_difference

        # Determine the player's risk buffer, a value in seconds that will be added to the
        # player's estimate -- audacious players will give a negative risk buffer, and thus
        # will decide to challenge the throw even if, all other things being equal they
        # realize the throw may beat them
        try:
            risk_buffer = (1.0-self.audacity)/1.5
        except ZeroDivisionError:
            risk_buffer = 0.0
        if my_estimate_of_difference + risk_buffer < 0:
            self.believes_he_can_beat_throw = True
            if realistic_estimate_of_difference > 0:
                if playing_action.at_bat.game.trace:
                    print ("-- Due to confidence and/or audacity, {} will riskily attempt to take the next base "
                           "[realistic estimate was {}, his was {}, risk_buffer was {}] [{}]").format(
                        self.person.last_name, realistic_estimate_of_difference, my_estimate_of_difference, risk_buffer,
                        batted_ball.time_since_contact
                    )
        else:
            self.believes_he_can_beat_throw = False
            if realistic_estimate_of_difference < 0:
                if playing_action.at_bat.game.trace:
                    print ("-- Due to timidness or lack of confidence, {} will (perhaps overcautiously) not take "
                           "the next base [realistic estimate was {}, his was {}, risk_buffer was {}] [{}]").format(
                        self.person.last_name, realistic_estimate_of_difference, my_estimate_of_difference, risk_buffer,
                        batted_ball.time_since_contact)

    def field_ball(self, batted_ball):
        """Attempt to field a batted ball.."""
        assert self.reorienting_after_fielding_miss <= 0, \
            "{} is attempting to field a ball while his reorientation time is still {}".format(
                self.person.last_name, self.reorienting_after_fielding_miss
            )
        batted_ball.bobbled = False
        line_drive_at_pitcher = False
        ball_totally_missed = False
        # If the batted ball is a line drive straight to the pitcher,
        # the difficulty is fixed and depends fully on reflexes, rather
        # than on fielding skill
        if (batted_ball.time_since_contact < 0.6 and
                (batted_ball.type == "line drive" or batted_ball.type == "ground ball")):
            batted_ball.fielding_difficulty = difficulty = 0.75
            difficulty /= self.reflexes
            if difficulty >= 1.0:
                difficulty = 0.999
            if random.random() > difficulty:
                # Cleanly fielded
                batted_ball.fielded_by = self
                if not batted_ball.landed:
                    batted_ball.caught_in_flight = True
            else:
                # TODO major possibility of injury here
                assert self.position == "P", "'Line drive at pitcher' was not at pitcher!"
                line_drive_at_pitcher = True
                batted_ball.touched_by_fielder = batted_ball.bobbled = True
                # Determine how long it will take the fielder to reorient after failing to
                # field the ball here
                reorientation_time = 1.5
                reorientation_time /= self.reflexes
                if reorientation_time > 2.5:
                    reorientation_time = 2.5
                self.reorienting_after_fielding_miss = reorientation_time
        # If the batted ball has come to a stop, the difficulty is fixed
        elif batted_ball.stopped:
            batted_ball.fielding_difficulty = difficulty = 0.003
            # Simulate whether the ball is cleanly fielded
            difficulty /= self.ground_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.person.mood.composure
            if difficulty >= 1.0:
                difficulty = 0.999
            if random.random() > difficulty:
                # Cleanly fielded
                batted_ball.fielded_by = self
            else:
                reorientation_time = 0.8
                reorientation_time /= self.reflexes
                if reorientation_time > 1.3:
                    reorientation_time = 1.3
                self.reorienting_after_fielding_miss = reorientation_time
                # Bobbled
                batted_ball.touched_by_fielder = batted_ball.bobbled = True
        # Likewise, fielding chances at the wall have a fixed difficulty
        elif batted_ball.at_the_foul_wall or batted_ball.at_the_outfield_wall or batted_ball.left_playing_field:
            # (The reason batted_ball.left_the_playing_field is even a plausible attribute
            # here is because if this method is even being called, it means it only just
            # left the playing field and is within reaching distance of a player climbing
            # the wall)
            batted_ball.fielding_difficulty = difficulty = 0.97
            # Simulate whether the ball is cleanly fielded
            difficulty /= self.fly_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.person.mood.composure
            if difficulty >= 1.0:
                difficulty = 0.999
            if random.random() > difficulty:
                # Cleanly fielded
                batted_ball.fielded_by = self
                if not batted_ball.landed:
                    batted_ball.caught_in_flight = True
            else:
                reorientation_time = 1.3
                reorientation_time /= self.reflexes
                if reorientation_time > 2.1:
                    reorientation_time = 2.1
                self.reorienting_after_fielding_miss = reorientation_time
                if random.random() < 0.9:
                    ball_totally_missed = True  # Let ball continue on its normal trajectory, likely over the fence
                else:
                    # Bobbled, so it will fall to the ground
                    batted_ball.touched_by_fielder = batted_ball.bobbled = True
        elif not batted_ball.landed:  # Fly, liner, or pop-up still in flight
            difficulty = 0.001
            # Increase difficulty if fielder is running close to full speed
            if self.relative_rate_of_speed > 80:
                difficulty_due_to_fielder_speed = (
                    (self.relative_rate_of_speed-80)/100.
                )
                difficulty += difficulty_due_to_fielder_speed*1.5
            # Increase difficulty for the height of the ball at that point --
            # the ideal height for fielding a ball is (approximately) the
            # fielder's own height, since the ball would be right in front of
            # his eyes at that height
            diff_from_ideal_height = batted_ball.height - (self.height/12)
            if diff_from_ideal_height < 0:
                difficulty += -1.0 * (diff_from_ideal_height/100.)
            elif batted_ball.height < self.vertical_reach:
                difficulty += diff_from_ideal_height/100.
            elif batted_ball.height >= self.vertical_reach:  # Jumping catch required
                difficulty += 3.5 * (diff_from_ideal_height/100.)
            # Increase difficulty for running backward to make the catch -- this
            # only matters when the player is moving at close to full speed; also
            # we further increase difficulty in these cases if the fielder has
            # an awkward handedness giving that he is moving right or left
            if self.relative_rate_of_speed > 80 and self.position != "C":
                if self._straight_ahead_y:
                    difficulty += self.relative_rate_of_speed*0.003
                elif self._moving_left and self._slope < -0.5:
                    difficulty += self.relative_rate_of_speed*0.0005
                    if self.righty:
                        difficulty += self.relative_rate_of_speed*0.0002
                elif self._moving_right and self._slope > 0.5:
                    difficulty += self.relative_rate_of_speed*0.0005
                    if self.lefty:
                        difficulty += self.relative_rate_of_speed*0.0002
            # Slightly increase difficulty for the tricky aspects of pop flies
            if batted_ball.apex > batted_ball.true_distance:
                difficulty += 0.01
            # Increase difficulty if it is bouncing off the outfield fence,
            # which gives unpredictable bounces in most ballparks -- below we
            # assume that a fielder will know his own ballpark's quirks better
            if batted_ball.outfield_fence_contact_timestep:
                difficulty += 0.3
            # Simulate whether the ball is cleanly fielded
            batted_ball.fielding_difficulty = difficulty
            difficulty /= self.fly_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.person.mood.composure
            if batted_ball.outfield_fence_contact_timestep:
                if self in batted_ball.at_bat.game.home_team.players:
                    # Fielders deal more easily with their own ballpark's quirks
                    difficulty -= 0.15
            if difficulty >= 1.0:
                difficulty = 0.999
            if random.random() > difficulty:
                # Cleanly fielded
                batted_ball.fielded_by = self
                if not batted_ball.landed:
                    batted_ball.caught_in_flight = True
            else:
                reorientation_time = difficulty*3
                reorientation_time /= self.reflexes
                if reorientation_time > 4.2:
                    reorientation_time = 4.2
                self.reorienting_after_fielding_miss = reorientation_time
                if random.random() < difficulty/2:
                    ball_totally_missed = True  # Let ball continue on its normal trajectory
                else:
                    # Bobbled, so it will fall to the ground
                    batted_ball.touched_by_fielder = batted_ball.bobbled = True
        elif batted_ball.landed:  # Ground ball
            difficulty = 0.002
            # Increase difficulty for the horizontal component of the ball's
            # velocity at that point (which is referenced by batted_ball.speed),
            # but, crucially, as it is *confounded* by the runner's speed (which
            # reduces the difficulty of a ground ball hit right to an infielder)
            excess_speed = (batted_ball.speed-50.0)/100.
            if excess_speed > 0 and self.relative_rate_of_speed > 90:
                difficulty_due_to_ball_speed = (
                    excess_speed * (self.relative_rate_of_speed/100.)
                )
                difficulty += difficulty_due_to_ball_speed
            # Increase difficulty for running backward to make the catch -- this
            # only matters when the player is moving at close to full speed; also
            # we further increase difficulty in these cases if the fielder has
            # an awkward handedness giving that he is moving right or left
            if self.relative_rate_of_speed > 80 and self.position != "C":
                if self._straight_ahead_y:
                    difficulty += self.relative_rate_of_speed*0.003
                elif self._moving_left and self._slope < -0.5:
                    difficulty += self.relative_rate_of_speed*0.0005
                    if self.righty:
                        difficulty += self.relative_rate_of_speed*0.0002
                elif self._moving_right and self._slope > 0.5:
                    difficulty += self.relative_rate_of_speed*0.0005
                    if self.lefty:
                        difficulty += self.relative_rate_of_speed*0.0002
            # Increase difficulty for the height of the ball at that point, with
            # the ideal height for fielding a ground ball modelled at 0 feet,
            # since a grounder that is rolling on the ground is most predictable
            # (this computation then simulates for the difficulty of hoppers) --
            # however, this is not applicable to ground balls that take a huge
            # bounce and essentially become bunny pop-ups that are easy to
            # catch at a decent height
            if not batted_ball.apex > batted_ball.true_distance:
                difficulty_due_to_hop = batted_ball.height/100.
                difficulty += difficulty_due_to_hop
            # Simulate whether the ball is cleanly fielded
            batted_ball.fielding_difficulty = difficulty
            difficulty /= self.ground_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.person.mood.composure
            if difficulty >= 1.0:
                difficulty = 0.999
            if random.random() > difficulty:
                # Cleanly fielded
                batted_ball.fielded_by = self
            else:
                reorientation_time = 0.6
                reorientation_time /= self.reflexes
                if reorientation_time > 1.1:
                    reorientation_time = 1.1
                self.reorienting_after_fielding_miss = reorientation_time
                if random.random() < 0.3:
                    ball_totally_missed = True  # Let ball continue on its normal trajectory
                else:
                    # Bobbled, so it will fall to the ground
                    batted_ball.height += random.random()*5
                    batted_ball.touched_by_fielder = batted_ball.bobbled = True
        if ball_totally_missed:
            self.at_goal = False
        # Instantiate a FieldingAct object, which captures all this data and also modifies the fielder's
        # composure according to the results of the fielding act
        FieldingAct(fielder=self, batted_ball=batted_ball, objective_difficulty=batted_ball.fielding_difficulty,
                    subjective_difficulty=difficulty, line_drive_at_pitcher=line_drive_at_pitcher,
                    ball_totally_missed=ball_totally_missed)

    def decide_throw_or_on_foot_approach_to_target(self, playing_action):
        # TODO player should reason about how much power they need on the throw
        # TODO ego, denying aging, etc., should effect what player believes their throwing velocity is
        # TODO factor in relay throws in reasoning
        # Before reasoning about the throw, assess the baserunner situation
        chance_for_out_at_first, chance_for_out_at_second, chance_for_out_at_third, chance_for_out_at_home, \
            runner_threatening_second, runner_threatening_third, runner_threatening_home = (
                self.ascertain_baserunner_circumstances(playing_action=playing_action)
            )
        # Now, reason about the utility and chance of success for each potential throw and on-foot
        # advance, given the baserunner situation that we just surveyed above
        if chance_for_out_at_home or runner_threatening_home:
            diff_for_throw_to_home, diff_for_on_foot_approach_to_home = (
                self.estimate_whether_throw_and_or_on_foot_advance_could_beat_runner(
                    playing_action=playing_action, base="H"
                )
            )
        else:
            diff_for_throw_to_home, diff_for_on_foot_approach_to_home = None, None
        if chance_for_out_at_third or runner_threatening_third:
            diff_for_throw_to_third, diff_for_on_foot_approach_to_third = (
                self.estimate_whether_throw_and_or_on_foot_advance_could_beat_runner(
                    playing_action=playing_action, base="3B"
                )
            )
        else:
            diff_for_throw_to_third, diff_for_on_foot_approach_to_third = None, None
        if chance_for_out_at_second or runner_threatening_second:
            diff_for_throw_to_second, diff_for_on_foot_approach_to_second = (
                self.estimate_whether_throw_and_or_on_foot_advance_could_beat_runner(
                    playing_action=playing_action, base="2B"
                )
            )
        else:
            diff_for_throw_to_second, diff_for_on_foot_approach_to_second = None, None
        if chance_for_out_at_first:
            diff_for_throw_to_first, diff_for_on_foot_approach_to_first = (
                self.estimate_whether_throw_and_or_on_foot_advance_could_beat_runner(
                    playing_action=playing_action, base="1B"
                )
            )
        else:
            diff_for_throw_to_first, diff_for_on_foot_approach_to_first = None, None
        # Decide whether to throw or run, and where to throw or run to, given the chances of
        # success and potential utility of each base as a potential destination
        batted_ball = playing_action.batted_ball
        # TODO give more nuanced scoring procedure here
        # If there's two outs and a chance for the third out, you will want to throw or run afoot to the
        # surest chance for an out (assuming any have even a reasonable chance of tallying a put out),
        # so if there are two outs, determine what throw or on-foot advance has the surest chance of
        # turning an out
        chance_for_putout = (
            chance_for_out_at_first or chance_for_out_at_second or
            chance_for_out_at_third or chance_for_out_at_home
        )
        if batted_ball.at_bat.frame.outs == 2 and chance_for_putout:
            # Determine which approach will give the best chance for a putout
            pertinent_expected_throw_and_on_foot_diffs = []
            if chance_for_out_at_first:
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_throw_to_first)
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_on_foot_approach_to_first)
            if chance_for_out_at_second:
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_throw_to_second)
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_on_foot_approach_to_second)
            if chance_for_out_at_third:
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_throw_to_third)
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_on_foot_approach_to_third)
            if chance_for_out_at_home:
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_throw_to_home)
                pertinent_expected_throw_and_on_foot_diffs.append(diff_for_on_foot_approach_to_home)
            best_bet_throw_or_on_foot_approach = min(pertinent_expected_throw_and_on_foot_diffs)
        else:
            best_bet_throw_or_on_foot_approach = 999  # If there's more than two outs, never do it this way
        # Prepare lists that are needed for the method that will be called to actually decide which
        # throw or on-foot approach to make
        all_chances_for_outs = (
            chance_for_out_at_first, chance_for_out_at_second, chance_for_out_at_third, chance_for_out_at_home
        )
        all_throw_and_on_foot_advance_diffs = (
            diff_for_throw_to_first, diff_for_on_foot_approach_to_first,
            diff_for_throw_to_second, diff_for_on_foot_approach_to_second,
            diff_for_throw_to_third, diff_for_on_foot_approach_to_third,
            diff_for_throw_to_home, diff_for_on_foot_approach_to_home
        )
        if batted_ball.at_bat.frame.outs == 2 and chance_for_putout and best_bet_throw_or_on_foot_approach < 0.2:
            # If the best bet looks to have a reasonable chance of actually producing a putout (say,
            # it should get to its target less than a fifth of a second after the runner is expected
            # to get there), then throw, or go afoot with, the best bet
            self.make_throw_and_on_foot_approach_with_best_chance_for_putout(
                playing_action=playing_action, all_chances_for_outs=all_chances_for_outs,
                best_bet_throw_or_on_foot_approach=best_bet_throw_or_on_foot_approach,
                all_throw_and_on_foot_advance_diffs=all_throw_and_on_foot_advance_diffs)
        # If there's less than two outs (or two outs but no reasonable chance for making the third out),
        # throw or run to the highest base to which there is a runner advancing whom you believe you
        # could beat with your throw or on-foot advance -- or, if there appear to be no such options,
        # throw to a cut-off man potentially, or just back to the pitcher, or if you are the pitcher,
        # just walk back to the mound and end the playing action; first, however, pack up our list of
        # threatening runners, because that will be needed by the method called here
        else:
            all_runners_threatening_advance = (
                runner_threatening_second, runner_threatening_third, runner_threatening_home
            )
            self.make_throw_or_on_foot_approach_of_highest_utility(
                playing_action=playing_action, all_chances_for_outs=all_chances_for_outs,
                all_runners_threatening_advance=all_runners_threatening_advance,
                all_throw_and_on_foot_advance_diffs=all_throw_and_on_foot_advance_diffs
            )

    def set_throw_target(self, playing_action, base, back_to_pitcher=False, relay=False):
        self.will_throw = True
        self._throw_release = "Overhand"
        self._throw_power = 1.0
        if base == "1B":
            self.throwing_to_first = True
            self._throw_target = playing_action.covering_first
            self._throw_target_coords = [63.5, 63.5]
        elif base == "2B":
            self.throwing_to_second = True
            self._throw_target = playing_action.covering_second
            self._throw_target_coords = [0, 127]
        elif base == "3B":
            self.throwing_to_third = True
            self._throw_target = playing_action.covering_third
            self._throw_target_coords = [-63.5, 63.5]
        elif base == "H":
            self.throwing_to_home = True
            self._throw_target = playing_action.covering_home
            self._throw_target_coords = [0, 0]
        elif back_to_pitcher:
            self._throw_target = self.team.roster.pitcher
            self.throwing_back_to_pitcher = True
            self._throw_target_coords = [0, 60.5]
        elif relay:
            self.throwing_to_relay = True
            self._throw_target = playing_action.cut_off_man
            self._throw_target_coords = playing_action.cut_off_man.location
            # The cut-off man should now stay at his current location in
            # anticipation of the throw
            playing_action.cut_off_man.at_goal = True
        self._throw_distance_to_target = (
            math.hypot(self.location[0]-self._throw_target_coords[0],
                       self.location[1]-self._throw_target_coords[1])
        )

    def set_on_foot_advance_target(self, playing_action, base):
        self.will_throw = False
        self.dist_per_timestep = 0.1/self.person.body.full_speed_seconds_per_foot
        if base == "1B":
            self.immediate_goal = [63.5, 63.5]
            runner_to_putout = (playing_action.running_to_first or playing_action.retreating_to_first)
        elif base == "2B":
            self.immediate_goal = [0, 127]
            runner_to_putout = (playing_action.running_to_second or playing_action.retreating_to_second)
        elif base == "3B":
            self.immediate_goal = [-63.5, 63.5]
            runner_to_putout = (playing_action.running_to_third or playing_action.retreating_to_third)
        elif base == "H":
            self.immediate_goal = [0, 0]
            runner_to_putout = playing_action.running_to_home
        # Set playing_action.fielder_afoot_for_putout tuple, which is used by playing_action._transpire()
        playing_action.fielder_afoot_for_putout = self, runner_to_putout, base
        # Determine the slope of a straight line between fielder's
        # current location and the goal location
        x_change = self.immediate_goal[0]-self.location[0]
        y_change = self.immediate_goal[1]-self.location[1]
        if x_change == 0 and y_change == 0:
            self.at_goal = True
        elif x_change == 0:
            self._straight_ahead_y = True
        elif y_change == 0:
            self._straight_ahead_x = True
        else:
            self._slope = y_change / float(x_change)
        # Determine whether the goal is to the left (this affects
        # computation of where the player gets to as player.act()
        # is called each timestep)
        if x_change < 0:
            self._moving_left = True
        elif x_change > 0:
            self._moving_right = True

    def make_throw_and_on_foot_approach_with_best_chance_for_putout(self, playing_action, all_chances_for_outs,
                                                                    best_bet_throw_or_on_foot_approach,
                                                                    all_throw_and_on_foot_advance_diffs):
        batted_ball = playing_action.batted_ball
        chance_for_out_at_first, chance_for_out_at_second, chance_for_out_at_third, chance_for_out_at_home = (
            all_chances_for_outs
        )
        diff_for_throw_to_first, diff_for_on_foot_approach_to_first = all_throw_and_on_foot_advance_diffs[:2]
        diff_for_throw_to_second, diff_for_on_foot_approach_to_second = all_throw_and_on_foot_advance_diffs[2:4]
        diff_for_throw_to_third, diff_for_on_foot_approach_to_third = all_throw_and_on_foot_advance_diffs[4:6]
        diff_for_throw_to_home, diff_for_on_foot_approach_to_home = all_throw_and_on_foot_advance_diffs[6:8]
        # Pick out the best chance (throw or on-foot approach) for making a putout and act on that
        if chance_for_out_at_first and best_bet_throw_or_on_foot_approach == diff_for_throw_to_first:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to first from [{}, {}] in pursuit of third out [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="1B")
        elif chance_for_out_at_first and best_bet_throw_or_on_foot_approach == diff_for_on_foot_approach_to_first:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to first from [{}, {}] in pursuit of third out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="1B")
        elif chance_for_out_at_second and best_bet_throw_or_on_foot_approach == diff_for_throw_to_second:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to second from [{}, {}] in pursuit of third out [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="2B")
        elif chance_for_out_at_second and best_bet_throw_or_on_foot_approach == diff_for_on_foot_approach_to_second:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to second from [{}, {}] in pursuit of third out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="2B")
        elif chance_for_out_at_third and best_bet_throw_or_on_foot_approach == diff_for_throw_to_third:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to third from [{}, {}] in pursuit of third out [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="3B")
        elif chance_for_out_at_third and best_bet_throw_or_on_foot_approach == diff_for_on_foot_approach_to_third:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to third from [{}, {}] in pursuit of third out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="3B")
        elif chance_for_out_at_home and best_bet_throw_or_on_foot_approach == diff_for_throw_to_home:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to home from [{}, {}] in pursuit of third out [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="H")
        elif chance_for_out_at_home and best_bet_throw_or_on_foot_approach == diff_for_on_foot_approach_to_home:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to home plate from [{}, {}] in pursuit of third out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="H")
        else:
            print "Something went wrong -- player.py error code 09302014"
            raw_input("")

    def make_throw_or_on_foot_approach_of_highest_utility(self, playing_action, all_chances_for_outs,
                                                          all_runners_threatening_advance,
                                                          all_throw_and_on_foot_advance_diffs):
        batted_ball = playing_action.batted_ball
        chance_for_out_at_first, chance_for_out_at_second, chance_for_out_at_third, chance_for_out_at_home = (
            all_chances_for_outs
        )
        runner_threatening_second, runner_threatening_third, runner_threatening_home = all_runners_threatening_advance
        diff_for_throw_to_first, diff_for_on_foot_approach_to_first = all_throw_and_on_foot_advance_diffs[:2]
        diff_for_throw_to_second, diff_for_on_foot_approach_to_second = all_throw_and_on_foot_advance_diffs[2:4]
        diff_for_throw_to_third, diff_for_on_foot_approach_to_third = all_throw_and_on_foot_advance_diffs[4:6]
        diff_for_throw_to_home, diff_for_on_foot_approach_to_home = all_throw_and_on_foot_advance_diffs[6:8]
        if chance_for_out_at_home and diff_for_throw_to_home <= 0:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to home from [{}, {}] [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="H")
        elif chance_for_out_at_home and diff_for_on_foot_approach_to_home <= 0:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to home plate from [{}, {}] in pursuit of an out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="H")
        elif chance_for_out_at_third and diff_for_throw_to_third <= 0:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to third from [{}, {}] [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="3B")
        elif chance_for_out_at_third and diff_for_on_foot_approach_to_third <= 0:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to third from [{}, {}] in pursuit of an out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="3B")
        elif chance_for_out_at_second and diff_for_throw_to_second <= 0:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to second from [{}, {}] [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="2B")
        elif chance_for_out_at_second and diff_for_on_foot_approach_to_second <= 0:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to second from [{}, {}] in pursuit of an out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="2B")
        elif chance_for_out_at_first and diff_for_throw_to_first <= 0.2:
            # If no other runners and even positive margin for throw to first,
            # just throw there anyway for due diligence
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to first from [{}, {}] [{}]".format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="1B")
        elif chance_for_out_at_first and diff_for_on_foot_approach_to_first <= 0:
            if playing_action.at_bat.game.trace:
                print ("-- {} ({}) will run to first from [{}, {}] in pursuit of an out because"
                       " he believes the ball will get there faster that way [{}]").format(
                    self.person.last_name, self.position, int(self.location[0]), int(self.location[1]),
                    batted_ball.time_since_contact
                )
            self.set_on_foot_advance_target(playing_action=playing_action, base="1B")
        # If there's no apparent chance for you to throw or run to a putout attempt and if
        # you are an outfielder and there is a cut-off man in place, throw to him
        elif self.outfielder and playing_action.cut_off_man:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will make a cut-off throw to {} ({}) [{}]".format(
                        self.person.last_name, self.position, playing_action.cut_off_man.person.last_name,
                        playing_action.cut_off_man.position, batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base=None, relay=True)
        elif runner_threatening_home:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to home preemptively [{}]".format(
                    self.person.last_name, self.position, batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="H")
        elif runner_threatening_third:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to third preemptively [{}]".format(
                    self.person.last_name, self.position, batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="3B")
        elif runner_threatening_second:
            if playing_action.at_bat.game.trace:
                print "-- {} ({}) will throw to second preemptively [{}]".format(
                    self.person.last_name, self.position, batted_ball.time_since_contact
                )
            self.set_throw_target(playing_action=playing_action, base="2B")
        else:
            if not self.position == "P":
                if playing_action.at_bat.game.trace:
                    print "-- {} ({}) will just throw to pitcher [{}]".format(
                        self.person.last_name, self.position, batted_ball.time_since_contact
                    )
                self.set_throw_target(playing_action=playing_action, base=None, back_to_pitcher=True)
            else:
                if playing_action.at_bat.game.trace:
                    print "-- {} ({}) will just walk back to mound [{}]".format(
                        self.person.last_name, self.position, batted_ball.time_since_contact
                    )
                playing_action.resolved = True

    @staticmethod
    def ascertain_baserunner_circumstances(playing_action):
        chance_for_out_at_first = False
        chance_for_out_at_second = False
        chance_for_out_at_third = False
        chance_for_out_at_home = False
        runner_threatening_second = False
        runner_threatening_third = False
        runner_threatening_home = False
        # First, take note of baserunners who are actively advancing or who are being forced to retreat
        # by a fly out -- these represent situations in which there is a real chance of making an out
        if ((playing_action.running_to_first and not playing_action.running_to_first.will_round_base and not
            playing_action.running_to_first.safely_on_base) or
                (playing_action.retreating_to_first and playing_action.retreating_to_first.forced_to_retreat and
                    not playing_action.retreating_to_first.safely_on_base)):
            chance_for_out_at_first = True
        if ((playing_action.running_to_second and not playing_action.running_to_second.will_round_base and
            not playing_action.running_to_second.safely_on_base) or
                (playing_action.retreating_to_second and playing_action.retreating_to_second.forced_to_retreat and
                    not playing_action.retreating_to_second.safely_on_base)):
            chance_for_out_at_second = True
        if ((playing_action.running_to_third and not playing_action.running_to_third.will_round_base and
            not playing_action.running_to_third.safely_on_base) or
                (playing_action.retreating_to_third and playing_action.retreating_to_third.forced_to_retreat and
                    not playing_action.retreating_to_third.safely_on_base)):
            chance_for_out_at_third = True
        if playing_action.running_to_home and not playing_action.running_to_home.safely_home:
            chance_for_out_at_home = True
        # Also take note of baserunners who have rounded a base or who apparently will round a base,
        # but represent no real threat of advancing unless there is an error -- in these cases, the
        # throw would be made preemptively to the base that the runner is threatening to advance to
        if ((playing_action.running_to_first and playing_action.running_to_first.will_round_base) or
                (playing_action.retreating_to_first and not playing_action.retreating_to_first.safely_on_base)):
            # Batter-runner is on a banana turn to first, or has already rounded first
            runner_threatening_second = True
        if ((playing_action.running_to_second and playing_action.running_to_second.will_round_base) or
                (playing_action.retreating_to_second and not playing_action.retreating_to_second.safely_on_base)):
            runner_threatening_third = True
        if ((playing_action.running_to_third and playing_action.running_to_third.will_round_base) or
                (playing_action.retreating_to_third and not playing_action.retreating_to_third.safely_on_base)):
            runner_threatening_home = True
        return (chance_for_out_at_first, chance_for_out_at_second, chance_for_out_at_third, chance_for_out_at_home,
                runner_threatening_second, runner_threatening_third, runner_threatening_home)

    def estimate_whether_throw_and_or_on_foot_advance_could_beat_runner(self, playing_action, base):
        # First, estimate how long it will take the baserunner to reach the base
        # in question
        if base == "H":
            if playing_action.running_to_home:
                dist_from_runner_to_base = 90 - (playing_action.running_to_home.percent_to_base*90)
            elif playing_action.running_to_third:
                dist_from_runner_to_base = 180 - (playing_action.running_to_third.percent_to_base*90)
            elif playing_action.retreating_to_third:
                dist_from_runner_to_base = 180 - (playing_action.retreating_to_third.percent_to_base*90)
        elif base == "3B":
            if playing_action.running_to_third:
                dist_from_runner_to_base = 90 - (playing_action.running_to_third.percent_to_base*90)
            elif playing_action.retreating_to_third:
                dist_from_runner_to_base = 90 - (playing_action.retreating_to_third.percent_to_base*90)
            elif playing_action.running_to_second:
                dist_from_runner_to_base = 180 - (playing_action.running_to_second.percent_to_base*90)
            elif playing_action.retreating_to_second:
                dist_from_runner_to_base = 180 - (playing_action.retreating_to_second.percent_to_base*90)
        elif base == "2B":
            if playing_action.running_to_second:
                dist_from_runner_to_base = 90 - (playing_action.running_to_second.percent_to_base*90)
            elif playing_action.retreating_to_second:
                dist_from_runner_to_base = 90 - (playing_action.retreating_to_second.percent_to_base*90)
            elif playing_action.running_to_first:
                dist_from_runner_to_base = 180 - (playing_action.running_to_first.percent_to_base*90)
            elif playing_action.retreating_to_first:
                dist_from_runner_to_base = 180 - (playing_action.retreating_to_first.percent_to_base*90)
        elif base == "1B":
            # Runner going to first who is not on a banana turn or runner who is being forced to
            # tag up at first due to fly out-- determine whether your throw could beat the runner
            runner_in_question = playing_action.running_to_first or playing_action.retreating_to_first
            dist_from_runner_to_base = 90 - (runner_in_question.percent_to_base*90)
        # Assume decent footspeed for runner, but not that fast -- a ~7.0 60-yard dash
        time_expected_for_runner_to_reach_base = dist_from_runner_to_base * 0.039
        # Next, estimate how long it would take for your throw to reach the base
        if base == "H":
            throw_target = playing_action.covering_home
            base_coords = [0, 0]
        elif base == "3B":
            throw_target = playing_action.covering_third
            base_coords = [-63.5, 63.5]
        elif base == "2B":
            throw_target = playing_action.covering_second
            base_coords = [0, 127]
        else:  # elif base == "1B":
            throw_target = playing_action.covering_first
            base_coords = [63.5, 63.5]
        if throw_target is self:
            # To preclude players throwing to themselves, we give an arbitrary high number here --
            # also calculate dist_from_me_to_base because it won't be calculated in the else block
            # below this
            dist_from_me_to_base = math.hypot(self.location[0]-base_coords[0], self.location[1]-base_coords[1])
            diff_for_throw_to_base = 999
        else:
            # Estimate how long it will take the throw target to be near the base in
            # question (within five feet) and ready to receive the throw
            if throw_target.at_goal:
                time_expected_for_target_to_be_ready_for_throw = 0.0
            else:
                dist_from_target_to_base = math.hypot(
                    throw_target.location[0]-base_coords[0], throw_target.location[1]-base_coords[1])
                if dist_from_target_to_base > 5:
                    time_expected_for_target_to_be_ready_for_throw = (
                        dist_from_target_to_base * throw_target.full_speed_seconds_per_foot
                    )
                else:
                    time_expected_for_target_to_be_ready_for_throw = 0.0
            # Estimate how long both the throw release and throw itself will take, which
            # depends on the throw distance
            dist_from_me_to_base = math.hypot(self.location[0]-base_coords[0], self.location[1]-base_coords[1])
            time_expected_for_throw_release = (
                math.sqrt(dist_from_me_to_base) * self.throwing_release_time
            )
            time_expected_for_throw_itself = self.estimate_time_for_throw_to_reach_target(
                distance=dist_from_me_to_base, initial_velocity=self.throwing_velocity
            )
            time_expected_for_throw_to_base = (
                time_expected_for_target_to_be_ready_for_throw +
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
            diff_for_throw_to_base = time_expected_for_throw_to_base - time_expected_for_runner_to_reach_base
        # Finally, estimate how long it would take for you to run to the base yourself -- if you are
        # covering a base but aren't *exactly* at its coordinates, preclude any potential
        # decision to go afoot toward that base, since if a throw has reached you there, the umpire has
        # already made a call at the base that you're covering (e.g. had a catcher trying to run from
        # [0, 2] to [0, 0] after getting a throw at the plate in advance of a runner threatening home)
        if base == "1B" and self is playing_action.covering_first:
            diff_for_on_foot_approach_to_base = 999
        elif base == "2B" and self is playing_action.covering_second:
            diff_for_on_foot_approach_to_base = 999
        elif base == "3B" and self is playing_action.covering_third:
            diff_for_on_foot_approach_to_base = 999
        elif base == "H" and self is playing_action.covering_home:
            diff_for_on_foot_approach_to_base = 999
        else:
            time_expected_for_on_foot_approach_to_base = (
                dist_from_me_to_base * self.person.body.full_speed_seconds_per_foot
            )
            diff_for_on_foot_approach_to_base = (
                time_expected_for_on_foot_approach_to_base - time_expected_for_runner_to_reach_base
            )
        return diff_for_throw_to_base, diff_for_on_foot_approach_to_base

    @staticmethod
    def estimate_time_for_throw_to_reach_target(distance, initial_velocity):
        """Roughly simulate how long a throw would take to reach its target."""
        distance_traveled = 0.0
        time_elapsed = 0.0
        velocity = initial_velocity
        while distance_traveled < distance:
            time_elapsed += 0.1
            distance_traveled += velocity/10.
            velocity *= 0.99
        return time_elapsed

    @staticmethod
    def estimate_time_for_runner_to_reach_location(runner, distance):
        """Roughly simulate how long it would take a runner putting in full effort to reach a location."""
        # TODO players should have different acceleration times -- generate for each
        # player the number of feet it takes for him to complete acceleration (should be
        # 80-210 feet)
        # TODO there is no deceleration factored in yet
        # IF YOU CHANGE THIS, RECHECK ALL 180-YARD DASH TIMES AND FIX DISTRIBUTION
        distance_traveled = 0.0
        time_elapsed = 0.0
        full_speed = runner.full_speed_feet_per_second  # In feet per second
        feet_to_complete_initial_acceleration = 75.0
        feet_to_full_speed = 120.0
        while distance_traveled < distance:
            time_elapsed += 0.1
            if distance_traveled < feet_to_complete_initial_acceleration:
                speed = (distance_traveled/feet_to_complete_initial_acceleration) * (full_speed*0.9)
            elif distance_traveled < feet_to_full_speed:
                speed = (0.9 + (((distance_traveled-75)/(feet_to_full_speed-75)) * 0.1)) * full_speed
            else:
                speed = full_speed
            distance_traveled += speed/10.
        return time_elapsed

    def throw(self, playing_action):
        """Throw a ball to a target."""
        # Determine the base that is being thrown to, and the runner
        # approaching that base, if any, whose putout would be assisted
        # by the throw
        if self.throwing_to_first:
            targeted_base = "1B"
            if playing_action.running_to_first:
                runner_to_putout = playing_action.running_to_first
            elif playing_action.retreating_to_first:
                runner_to_putout = playing_action.retreating_to_first
            else:
                runner_to_putout = None
        elif self.throwing_to_second:
            targeted_base = "2B"
            if playing_action.running_to_second:
                runner_to_putout = playing_action.running_to_second
            elif playing_action.retreating_to_second:
                runner_to_putout = playing_action.retreating_to_second
            else:
                runner_to_putout = None
        elif self.throwing_to_third:
            targeted_base = "3B"
            if playing_action.running_to_third:
                runner_to_putout = playing_action.running_to_third
            elif playing_action.retreating_to_third:
                runner_to_putout = playing_action.retreating_to_third
            else:
                runner_to_putout = None
        elif self.throwing_to_home:
            targeted_base = "H"
            if playing_action.running_to_home:
                runner_to_putout = playing_action.running_to_home
            else:
                runner_to_putout = None
        else:
            targeted_base = None
            runner_to_putout = None
        if self._throw_release == "Overhand":
            release_time = (
                math.sqrt(self._throw_distance_to_target) * self.throwing_release_time
            )
            error = self.throwing_error_per_foot * self._throw_distance_to_target
            height_error = normal(0, error)
            lateral_error = normal(0, error)
        # TODO sidearm throws
        throw = Throw(playing_action=playing_action, thrown_by=self, thrown_to=self._throw_target, base=targeted_base,
                      runner_to_putout=runner_to_putout, release_time=release_time,
                      distance_to_target=self._throw_distance_to_target, release=self._throw_release,
                      power=self._throw_power, height_error=height_error, lateral_error=lateral_error,
                      back_to_pitcher=self.throwing_back_to_pitcher)
        self.will_throw = False
        self.throwing_to_first = self.throwing_to_second = self.throwing_to_third = self.throwing_to_home = False
        self.throwing_back_to_pitcher = self.throwing_to_relay = False
        return throw

    def tag(self, baserunner):
        pass
        # TODO NEXT!

    @property
    def bat_speed(self):
        if not self.bat:
            self.bat = Bat()
        return self.batting_power_coefficient * self.bat.weight + 103