from random import normalvariate as normal
from batted_ball import BattedBall, FoulTip
from outcome import Bean

import os, time  # for radio


# TODO checked swings

class Pitch(object):

    def __init__(self, ball, at_bat, handedness, batter_handedness, count,
                 kind, speed, intended_x, intended_y, actual_x, actual_y):
        self.ball = ball
        self.at_bat = at_bat
        self.pitcher = at_bat.pitcher
        self.pitcher.pitches.append(self)
        self.batter = at_bat.batter
        self.catcher = at_bat.catcher
        self.umpire = at_bat.umpire
        if handedness == "R":
            self.right_handed = True
            self.left_handed = False
        else:
            self.right_handed = False
            self.left_handed = True
        if batter_handedness == "R":
            self.batter_right_handed = True
            self.batter_left_handed = False
        else:
            self.batter_left_handed = True
            self.batter_right_handed = False
        self.count = count  # Count prior to the delivery of this pitch
        self.kind = kind
        self.speed = speed
        self.pitcher_intended_x = intended_x
        self.pitcher_intended_y = intended_y
        self.actual_x = actual_x
        self.actual_y = actual_y
        self.bean = False
        # Determine the pitcher's intention, ball or strike
        if (-2.83 < self.pitcher_intended_x < 2.83 and
                self.batter.strike_zone[0] < self.pitcher_intended_y <
                self.batter.strike_zone[1]):
            self.pitcher_intention = "Strike"
        else:
            self.pitcher_intention = "Ball"
        # Determine the true call, ball or strike
        if (-2.83 < actual_x < 2.83 and
                self.batter.strike_zone[0] < actual_y <
                self.batter.strike_zone[1]):
            self.true_call = "Strike"
        else:
            self.true_call = "Ball"
        # These attributes, which represent the batter's hypothesis of the
        # pitch, are modified by batter.decide_whether_to_swing()
        self.batter_hypothesized_x = None
        self.batter_hypothesized_y = None
        self.batter_hypothesis = None
        # The result of this pitch will be either a Strike (looking), Ball,
        # Bean, or Swing object and will be modified to point to the
        # appropriate object by that object's initializer
        self.result = None
        # This attribute, which relates the umpire's call of the pitch
        # is modified by umpire.call_pitch() -- it represents only a
        # hypothetical call unless the batter doesn't swing at the pitch
        self.would_be_call = self.umpire.call_pitch(self)
        # The actual call will be set to the would-be call by AtBat.enact()
        # if the batter doesn't swing
        self.call = None
        # Check if batter is hit by pitch
        if self.batter_right_handed:
            if (-15.0 < self.actual_x < -11.0 and
                    self.actual_y < self.batter.height / 3.0):
                self.bean = True
                Bean(pitch=self)
        elif self.batter_left_handed:
            if (11 < self.actual_x < 15 and
                    self.actual_y < self.batter.height / 3.0):
                self.bean = True
                Bean(pitch=self)
        # If the pitch is not swung at, or it results in a foul tip, whether
        # or not it is caught will be modified by at_bat.enact() via
        # catcher.receive_pitch()
        self.caught = False
        # Finally, append this to the AtBat's list of pitches -- do this last,
        # because other methods, notably umpire.call_pitch(), may want to
        # reference the prior pitch, and will do so by AtBat.pitches[-1]
        self.at_bat.pitches.append(self)


class Swing(object):

    def __init__(self, pitch, handedness, power, incline,
                 intended_pull, timing, contact_x_coord, contact_y_coord):
        self.at_bat = pitch.at_bat
        self.batter = pitch.batter
        self.pitcher = pitch.pitcher
        self.pitch = pitch
        self.bunt = False
        pitch.result = self
        self.ball = pitch.ball
        if handedness == "R":
            self.right_handed = True
            self.left_handed = False
        elif handedness == "L":
            self.right_handed = False
            self.left_handed = True
        self.bat = self.batter.bat
        self.power = power
        self.bat_speed = power * self.batter.bat_speed * self.bat.weight
        self.incline = incline
        self.intended_pull = intended_pull
        self.timing = timing
        self.contact_x_coord = contact_x_coord
        self.contact_y_coord = contact_y_coord
        # Modified below, as appropriate
        self.swing_and_miss = False
        self.whiff_properties = []
        self.contact = False
        self.foul_tip = False
        self.power_reduction = 0.0
        # Check for whether contact is made -- if not, attribute that
        # as well as the reason for the swing and miss
        if timing < -0.135:
            # Horrible timing -- too early
            self.swing_and_miss = True
            self.whiff_properties.append("too early")
        if timing > 0.135:
            # Horrible timing -- too late
            self.swing_and_miss = True
            self.whiff_properties.append("too late")
        if contact_x_coord >= 0.49:
            # Bad swing -- too inside
            self.swing_and_miss = True
            self.whiff_properties.append("too inside")
        # [Note: impossible to swing too outside -- it will just hit
        # the bat at a point closer to the batter's hands.]
        if contact_y_coord <= -0.08:
            # Bad swing -- too low
            self.swing_and_miss = True
            self.whiff_properties.append("too low")
        if contact_y_coord >= 0.08:
            # Bad swing -- too high
            self.swing_and_miss = True
            self.whiff_properties.append("too high")
        if not self.swing_and_miss:
            self.contact = True
        # Determine how exit speed will be decreased due to any
        # deviation from the sweet spot on the x-axis
        if contact_x_coord == 0:  # Hit on sweet spot -- no decrease
            self.power_reduction = 0.0
        elif contact_x_coord >= 0.49:  # Bat misses ball
            self.power_reduction = 0.0
        elif 0 < contact_x_coord <= 0.49:  # Contact toward end of bat
            self.power_reduction = contact_x_coord * 2
        elif -0.49 < contact_x_coord < 0:  # Contact toward the hands
            self.power_reduction = abs(contact_x_coord * 2)
        elif contact_x_coord <= -0.49:  # Contact on the bat handle
            self.power_reduction = 0.99
        # Determine how exit speed will be decreased due to major
        # deviation from the sweet spot on the y-axis
        if contact_y_coord >= 0.07:
            # Contact at the top of the bat -- either a foul tip or
            # contact with reduced power
            if contact_y_coord >= 0.79:
                self.foul_tip = True
            else:
                self.power_reduction += 0.3
        elif contact_y_coord <= -0.07:
            # Contact at the bottom of the bat -- either a foul tip or
            # contact with reduced power
            if contact_y_coord <= -0.79:
                self.foul_tip = True
            else:
                self.power_reduction += 0.3
        if self.power_reduction > 0.99:
            self.power_reduction = 0.99
        # Determine the vertical launch angle of the ball, with
        # deviation from the sweet spot on the y-axis altering the
        # intended launch angle, which is represented as incline
        if contact_y_coord == 0:
            # Contact at the sweet spot -- the launch angle is as intended
            self.vertical_launch_angle = incline
        elif contact_y_coord >= 0.08 or contact_y_coord <= -0.08:
            # Missed the ball
            self.vertical_launch_angle = None
        elif 0 < contact_y_coord < 0.07:
            # Contact above the sweet spot
            multiplier = (90 - self.incline) / 0.08
            self.vertical_launch_angle = incline + (contact_y_coord * multiplier)
        elif 0 >= contact_y_coord > -0.07:
            # Contact below the sweet spot
            multiplier = (90 + incline) / 0.08
            self.vertical_launch_angle = 0 + incline + (contact_y_coord * multiplier)
        elif contact_y_coord >= 0.07:
            # Contact at the top of the bat; produces 90 to 180 angle --
            # i.e., ball projects backward
            multiplier = 9000
            contact_y_coord_remainder = abs(0.07-contact_y_coord)
            self.vertical_launch_angle = 90 + (contact_y_coord_remainder * multiplier)
        elif contact_y_coord <= -0.07:
            # Contact at the bottom of the bat; produces -90 to -180 angle --
            # i.e., ball projects backward
            multiplier = 9000
            contact_y_coord_remainder = -abs(-0.07-contact_y_coord)
            self.vertical_launch_angle = -90 - (contact_y_coord_remainder * multiplier)
        # Determine the horizontal launch angle of the ball, which is
        # probabilistically determined given the batter's handedness
        # and then altered according to deviation from contact at the
        # sweet spot on the x-axis
        if self.left_handed:
            base_angle = normal(22.5, 10)
        elif self.right_handed:
            base_angle = normal(-22.5, 10)
        if contact_x_coord == 0:  # Hit on sweet spot -- no change in angle
            self.horizontal_launch_angle = base_angle
        elif contact_x_coord >= 0.49:  # Bat misses ball
            self.horizontal_launch_angle = None
        elif contact_x_coord <= -0.49:  # Contact right near the hands
            if self.left_handed:
                self.horizontal_launch_angle = 90
            elif self.right_handed:
                self.horizontal_launch_angle = -90
        elif 0 < contact_x_coord < 0.49:  # Contact toward end of bat
            if self.left_handed:
                multiplier = (-90 - contact_x_coord) / 0.49
                self.horizontal_launch_angle = (
                    base_angle + (contact_x_coord * multiplier)
                )
            if self.right_handed:
                multiplier = (90 - contact_x_coord) / 0.49
                self.horizontal_launch_angle = (
                    base_angle + (contact_x_coord * -multiplier)
                )
        elif -0.49 < contact_x_coord < 0:  # Contact toward the hands
            if self.left_handed:
                multiplier = (90 - contact_x_coord) / 0.49
                self.horizontal_launch_angle = (
                    base_angle + (contact_x_coord * -multiplier)
                )
            elif self.right_handed:
                multiplier = (-90 - contact_x_coord) / 0.49
                self.horizontal_launch_angle = (
                    base_angle + (contact_x_coord * multiplier)
                )
        # Lastly, determine exit speed, which is the initial velocity of
        # the ball as it moves off the bat, in miles per hour; exit speed
        # is a function of pitch speed, bat speed, and bat weight and is
        # reduced by the percentage represented by power_reduction, which
        # is determined according to deviations from contact at the sweet
        # spot on the x-axis (see above)
        if self.contact:
            q = self.bat.weight * 0.006  # TODO ball_liveliness should matter here too
            max_exit_speed = (
                (q * self.pitch.speed) + ((1+q) * self.bat_speed) * power
            )
            self.exit_speed = max_exit_speed * (1-self.power_reduction)
        else:
            self.exit_speed = None
        if self.contact:
            if self.foul_tip:
                foul_tip = FoulTip(swing=self)
                self.result = foul_tip
            else:
                batted_ball = BattedBall(
                    swing=self, exit_speed=self.exit_speed,
                    horizontal_launch_angle=self.horizontal_launch_angle,
                    vertical_launch_angle=self.vertical_launch_angle)
                self.result = batted_ball
                self.batter.at_the_plate = False
                self.batter.forced_to_advance = True


class Bunt(object):

    def __init__(self, at_bat, batter, pitch):
        self.at_bat = at_bat
        self.bunt = True


class FieldingAct(object):

    def __init__(self, fielder, batted_ball, objective_difficulty, subjective_difficulty,
                 line_drive_at_pitcher, ball_totally_missed):
        self.fielder = fielder
        self.fielder.fielding_acts.append(self)
        self.location = self.fielder.location
        self.fielder_position = fielder.position
        self.batted_ball = batted_ball
        batted_ball.result = self
        batted_ball.fielding_acts.append(self)
        self.objective_difficulty = objective_difficulty
        self.subjective_difficulty = subjective_difficulty
        if batted_ball.fielded_by:
            self.successful = True
        else:
            self.successful = False
        if not batted_ball.bobbled:
            self.fielder.attempting_fly_out = False
        self.line_drive_at_pitcher = line_drive_at_pitcher
        self.ball_totally_missed = ball_totally_missed
        self.ball_bobbled = batted_ball.bobbled
        self.fielder_composure = fielder.composure
        # Affect player composure according to the objective difficulty of the fielding act and
        # whether it was successful
        if self.successful:
            if batted_ball.fielding_difficulty > 0.4:
                fielder.composure += batted_ball.fielding_difficulty / 20.
        else:
            ease = 1-batted_ball.fielding_difficulty
            if ease > 0.4:
                fielder.composure -= ease / 40.
        self.fielder_composure_after = fielder.composure
        if line_drive_at_pitcher:
            print "-- Line drive right at {} ({}) [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        elif batted_ball.at_the_foul_wall or batted_ball.at_the_outfield_wall or batted_ball.left_playing_field:
            print "-- {} ({}) is attempting a catch at the wall! [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
            if batted_ball.at_bat.game.radio:
                os.system('say {} is going for the catch at the wall!'.format(self.fielder))
                time.sleep(0.5)
        else:
            print "-- {} ({}) is attempting to field the ball at [{}, {}] [Diff: {}] [{}]".format(
                self.fielder.last_name, self.fielder_position, int(self.location[0]), int(self.location[1]),
                round(self.objective_difficulty, 3), batted_ball.time_since_contact
            )
        if self.successful and batted_ball.landed:
            print "-- {} ({}) cleanly fields the ball [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        elif self.successful and not batted_ball.landed:
            print "-- {} ({}) makes the catch [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        elif batted_ball.stopped and batted_ball.bobbled:
            print "-- {} ({}) bobbles the stopped ball [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        elif not batted_ball.stopped and batted_ball.bobbled:
            print "-- {} ({}) gets a glove on the ball, but drops it [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        elif ball_totally_missed:
            print "-- {} ({}) misses the ball [{}]".format(
                self.fielder.last_name, self.fielder_position, batted_ball.time_since_contact
            )
        if round(self.fielder_composure, 2) != round(self.fielder_composure_after):
            print "-- {}'s composure changed from {} to {}".format(
                self.fielder.last_name, round(self.fielder_composure, 2), round(self.fielder_composure_after, 2)
            )
        else:
            print "-- {}'s composure remains {}".format(self.fielder.last_name, round(self.fielder_composure, 2))


class Throw(object):

    # TODO add self as appropriate fielding_act.result

    def __init__(self, batted_ball, thrown_by, thrown_to, base, runner_to_putout, release_time,
                 distance_to_target, release, power, height_error, lateral_error, back_to_pitcher=False):
        self.batted_ball = batted_ball
        self.thrown_by = thrown_by
        self.thrown_to = thrown_to
        self.base = base
        self.runner = runner_to_putout  # Runner that via the throw will be tagged or forced out
        self.release_time = release_time
        self.release = release
        self.power = power
        self.distance_to_target = distance_to_target
        self.dist_per_timestep = thrown_by.throwing_dist_per_timestep * power
        self.height_error = height_error
        self.lateral_error = lateral_error
        self.back_to_pitcher = back_to_pitcher
        if not back_to_pitcher:
            batted_ball.at_bat.potential_assistants.add(self.thrown_by)
        # Dynamic; modified during play
        self.time_until_release = release_time
        self.distance_traveled = 0.0
        self.percent_to_target = 0.0
        self.reached_target = False
        self.timestep_reached_target = None
        self.resolved = False

    def move(self):
        if self.time_until_release > 0:
            self.time_until_release -= 0.1
        else:
            self.distance_traveled += self.dist_per_timestep
            self.percent_to_target = (
                self.distance_traveled/self.distance_to_target
            )
            if self.percent_to_target >= 1.0:
                self.reached_target = True
                # Record the precise time the throw reached its target, for potential use
                # by umpire.call_play_at_base()
                surplus_distance = self.distance_traveled-self.distance_to_target
                surplus_time = (surplus_distance / self.dist_per_timestep) * 0.1
                self.timestep_reached_target = self.batted_ball.time_since_contact - surplus_time
                self.percent_to_target = 1.0
