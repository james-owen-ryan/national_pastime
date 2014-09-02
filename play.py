import math
from random import normalvariate as normal


# CORs:     0.562 for non-turfed base paths (increases with more sub-surface soil compaction)
#           0.479 for turf grass (varies per cutting height and moisture)
#           0.520 for synthetic turf (varies according to material composition)

class Pitch(object):

    def __init__(self, ball, at_bat, pitcher, batter, catcher, handedness,
                 batter_handedness, count, kind, speed, intended_x,
                 intended_y, actual_x, actual_y):
        self.ball = ball
        self.at_bat = at_bat
        self.pitcher = pitcher
        self.batter = batter
        self.catcher = catcher
        self.umpire = self.at_bat.umpire
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
        # The count prior to the delivery of this pitch
        self.count = count
        self.kind = kind
        self.speed = speed
        self.pitcher_intended_x = intended_x
        self.pitcher_intended_y = intended_y
        self.actual_x = actual_x
        self.actual_y = actual_y
        # Determine the pitcher's intention, ball or strike
        if (-2.83 < self.pitcher_intended_x < 2.83 and
                batter.strike_zone[0] < self.pitcher_intended_y <
                batter.strike_zone[1]):
            self.pitcher_intention = "Strike"
        else:
            self.pitcher_intention = "Ball"
        # Determine the true call, ball or strike
        if (-2.83 < actual_x < 2.83 and
                batter.strike_zone[0] < actual_y < batter.strike_zone[1]):
            self.true_call = "Strike"
        else:
            self.true_call = "Ball"
        # These attributes, which represent the batter's hypothesis of the
        # pitch, are modified by batter.decide_whether_to_swing()
        self.batter_hypothesized_x = None
        self.batter_hypothesized_y = None
        self.batter_hypothesis = None
        # This attribute, which relates the umpire's call of the pitch
        # is modified by umpire.call_pitch() -- it represents only a
        # hypothetical call unless the batter doesn't swing at the pitch
        self.would_be_call = self.umpire.call_pitch(self)
        # The actual call will be set to the would-be call by AtBat.?????
        # if the batter doesn't swing
        self.call = None
        # Finally, append this to the AtBat's list of pitches -- do this last,
        # because other methods, notably umpire.call_pitch(), may want to
        # reference the prior pitch, and will do so by AtBat.pitches[-1]
        self.at_bat.pitches.append(self)


class Bunt(object):

    def __init__(self, batter, pitch):
        pass


class Swing(object):

    def __init__(self, batter, pitch, handedness, power, upward_force,
                 intended_pull, timing, contact_x_coord, contact_y_coord):
        self.batter = batter
        self.pitch = pitch
        self.ball = pitch.ball
        if handedness == "R":
            self.right_handed = True
            self.left_handed = False
        elif handedness == "L":
            self.right_handed = False
            self.left_handed = True
        self.bat = batter.bat
        self.power = power
        self.bat_speed = power * batter.bat_speed * self.bat.weight
        self.upward_force = upward_force
        self.intended_pull = intended_pull
        self.timing = timing
        self.contact_x_coord = contact_x_coord
        self.contact_y_coord = contact_y_coord
        # Modified below, as appropriate
        self.swing_and_miss = False
        self.swing_and_miss_reasons = []
        self.contact = False
        self.power_reduction = 0.0
        # Check for whether contact is made -- if not, attribute that
        # as well as the reason for the swing and miss
        if timing < -0.135:
            # Horrible timing -- too early
            self.swing_and_miss = True
            self.swing_and_miss_reasons.append("too early")
        if timing > 0.135:
            # Horrible timing -- too late
            self.swing_and_miss = True
            self.swing_and_miss_reasons.append("too late")
        if contact_x_coord >= 0.49:
            # Bad swing -- too inside
            self.swing_and_miss = True
            self.swing_and_miss_reasons.append("too inside")
        # [Note: impossible to swing too outside -- it will just hit
        # the bat at a point closer to the batter's hands.]
        if contact_y_coord <= -0.08:
            # Bad swing -- too low
            self.swing_and_miss = True
            self.swing_and_miss_reasons.append("too low")
        if contact_y_coord >= 0.08:
            # Bad swing -- too high
            self.swing_and_miss = True
            self.swing_and_miss_reasons.append("too high")
        if not self.swing_and_miss:
            self.contact = True
        # Determine how exit speed will be decreased due to any
        # deviation from the sweet spot on the x-axis
        if contact_x_coord == 0:  # Hit on sweet spot -- no decrease
            self.power_reduction = 0.0
        elif contact_x_coord >= 0.49:  # Bat misses ball
            self.power_reduction = None
        elif 0 < contact_x_coord <= 0.49:  # Contact toward end of bat
            self.power_reduction = contact_x_coord * 2
        elif -0.49 < contact_x_coord < 0:  # Contact toward the hands
            self.power_reduction = abs(contact_x_coord * 2)
        elif contact_x_coord <= -0.49:  # Contact on the bat handle
            self.power_reduction = 0.99
        # Determine the vertical launch angle of the ball, with
        # deviation from the sweet spot on the y-axis altering the
        # intended launch angle, which is represented as upward_force
        if contact_y_coord == 0:
            # Contact at the sweet spot -- the launch angle is as intended
            self.vertical_launch_angle = upward_force
        elif contact_y_coord >= 0.08 or contact_y_coord <= -0.08:
            # Missed the ball
            self.vertical_launch_angle = None
        elif 0 < contact_y_coord < 0.07:
            # Contact above the sweet spot
            multiplier = (90 - self.upward_force) / 0.08
            self.vertical_launch_angle = upward_force + (contact_y_coord * multiplier)
        elif 0 >= contact_y_coord > -0.07:
            # Contact below the sweet spot
            multiplier = (90 + upward_force) / 0.08
            self.vertical_launch_angle = 0 + upward_force + (contact_y_coord * multiplier)
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
            q = self.bat.weight * 0.006  # ball_liveliness should matter here too
            max_exit_speed = (
                (q * self.pitch.speed) + ((1+q) * self.bat_speed) * power
            )
            self.exit_speed = max_exit_speed * (1-self.power_reduction)
        else:
            self.exit_speed = None
        if self.contact:
            batted_ball = BattedBall(swing=self, exit_speed=self.exit_speed,
                                     horizontal_launch_angle=self.horizontal_launch_angle,
                                     vertical_launch_angle=self.vertical_launch_angle)
            self.result = batted_ball
            self.pitch.result = batted_ball


class BattedBall(object):

    def __init__(self, swing, exit_speed, horizontal_launch_angle,
                 vertical_launch_angle):
        self.swing = swing
        self.ball = self.swing.ball
        self.batter = self.swing.batter
        self.pitch = swing.pitch
        self.pitcher = self.pitch.pitcher
        self.exit_speed = exit_speed
        self.horizontal_launch_angle = horizontal_launch_angle
        self.vertical_launch_angle = vertical_launch_angle
        # Prepare a dictionary that will map timesteps to batted
        # ball x-, y-, and z-coordinates; modified below
        self.position = {}
        # Enact a timestep-by-timestep physics simulation of the ball's
        # trajectory, recording its x-, y-, and z-coordinates at each
        # timestep; first, set initial values at point of contact
        x, y = 0, 3.5  # Coordinates at point of contact
        time_since_contact = 0.0  # Time at point of contact
        v = self.exit_speed * 0.44704  # Convert mph to m/s
        g = 9.81  # Standard gravitational acceleration in m/s
        th = math.radians(self.vertical_launch_angle)
        vx = v * math.cos(th)  # Initial horizontal component of velocity
        vy = v * math.sin(th)  # Initial vertical component of velocity
        m = self.ball.weight * 0.0283495  # Convert ounces to kg
        rho = 1.2  # Air density -- TODO change depending on weather, altitude
        C = 0.3  # Drag coefficient  -- TODO change depending on certain things
        A = 0.004208351855042743  # Cross-sectional area of ball in meters
        D = (rho * C * A) / 2  # Drag
        ax = -(D/m)*v*vx  # Initial horizontal component of acceleration
        ay = -g-(D/m)*v*vy  # Initial vertical component of acceleration
        timestep = 0.1
        # Record position at the initial timestep -- [NOTE: While it is
        # convenient for the physics computation to call the the horizontal
        # axis 'x' and the vertical axis 'y', in the baseball simulation it
        # makes more sense to call the vertical axis 'z', the axis moving
        # from home plate to center field 'y', and the axis moving from
        # third base to first base 'x'. As such, we convert the physics-
        # sim 'y' values to coordinate 'z' values, and then consider the
        # swing's horizontal launch angle to compute the additional
        # coordinate 'x' and 'y' values.]
        coordinate_x = 0
        coordinate_y = 0  # Right over home plate still
        coordinate_z = 3.5
        self.position[0.0] = coordinate_x, coordinate_y, coordinate_z
        while y > 0:  # Ball hasn't hit ground yet
            # Increment time
            time_since_contact += timestep
            # Calculate new physics x and y coordinates
            x += (vx*timestep) + (ax * timestep**2) / 2
            y += (vy*timestep) + (ay * timestep**2) / 2
            print "y is now {}".format(y)
            # Calculate new acceleration components
            ax = -(D/m)*v*vx
            ay = -g-(D/m)*v*vy
            print "ay is now {}".format(ay)
            # Calculate new velocity components
            vx += ax*timestep
            vy += ay*timestep
            print "vy is now {}".format(vy)
            v = math.sqrt(vx**2 + vy**2)
            # Calculate, convert, and record new actual ball x-, y-, z-coordinates
            coordinate_x = x * math.sin(math.radians(self.horizontal_launch_angle))
            coordinate_x *= 3.28084  # Convert meters to feet
            coordinate_y = x * math.cos(math.radians(self.horizontal_launch_angle))
            coordinate_y *= 3.28084
            coordinate_z = y * 3.28084
            self.position[time_since_contact] = coordinate_x, coordinate_y, coordinate_z
        self.true_distance = x * 3.28084
        self.true_landing_point = int(coordinate_x), int(coordinate_y)

    @property
    def vacuum_distance(self):
        """Return how far the ball would have traveled if hit in a vacuum."""
        # Determine the total distance the batted ball would have traveled
        # in a vacuum, if uninterrupted by a fielder or other obstacle --
        # this is determined by the ball's exit speed and vertical launch angle
        velocity = 1.466666666667 * self.exit_speed  # Convert mph to ft/s
        vacuum_distance =  (
            (velocity**2 / 32.185) * math.sin(2 * math.radians(self.vertical_launch_angle)))
        return vacuum_distance

    @property
    def vacuum_landing_point(self):
        """Return where the ball would have landed if hit in a vacuum."""
        vacuum_landing_point_x = (
            self.vacuum_distance * math.sin(math.radians(self.horizontal_launch_angle))
        )
        vacuum_landing_point_y = (
            self.vacuum_distance * math.cos(math.radians(self.horizontal_launch_angle))
        )
        return [vacuum_landing_point_x, vacuum_landing_point_y]

