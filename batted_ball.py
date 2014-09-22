import math


class BattedBall(object):

    def __init__(self, swing, exit_speed, horizontal_launch_angle,
                 vertical_launch_angle):
        # Note: swing may be a Bunt
        self.at_bat = swing.at_bat
        self.ballpark = self.at_bat.game.ballpark
        self.swing = swing
        if swing.bunt:
            self.bunt = True
        else:
            self.bunt = False
        self.ball = self.swing.ball
        self.batter = swing.batter
        self.pitch = swing.pitch
        self.pitcher = swing.pitcher
        self.exit_speed = exit_speed
        self.horizontal_launch_angle = horizontal_launch_angle
        self.vertical_launch_angle = vertical_launch_angle
        # Modified below, as necessary
        self.true_distance = None
        self.true_landing_point = None
        self.hang_time = None
        self.apex = 0.0
        self.location = [0, 0]
        self.height = 3.5
        self.time_since_contact = 0.0  # Adjusted by at_bat.enact()
        self.speed = exit_speed
        self.obligated_fielder = None
        self.fielder_with_chance = None
        self.fielded_by = None
        self.fielding_difficulty = None  # Modified by fielder.field_ball()
        self.touched_by_fielder = False   # Modified by fielder.field_ball()
        self.passed_first_or_third_base = False
        self.landed = False  # Ball has landed at least once
        self.landed_foul = False  # Ball has landed foul, putting it out of play (depending on the rule set)
        self.caught_in_flight = False
        self.n_bounces = 0  # Matters if fair- or foul-bound rules still in effect
        self.stopped = False  # Ball has stopped moving
        self.in_foul_territory = False
        self.at_the_foul_wall = False  # Ball is right at the wall
        self.at_the_outfield_wall = False
        self.crossed_plane_fair = False
        self.crossed_plane_foul = False
        self.left_playing_field = False
        self.ground_rule_incurred = False
        # Dynamic attributes that specify game actions while the ball is in play
        self.dead = False  # Dead ball
        self.result = None
        self.running_to_first = self.at_bat.batter
        self.running_to_second = self.at_bat.frame.on_first
        self.running_to_third = self.at_bat.frame.on_second
        self.running_to_home = self.at_bat.frame.on_third

        # print "i am a batted ball my running to 1b, 2b, 3b are {}, {}, {}".format(
        #     self.running_to_first, self.running_to_second, self.running_to_third
        # )

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
        # Prepare a dictionary that will map timesteps to batted ball
        # x-, y-, and z-coordinates; modified by compute_full_trajectory()
        self.position_at_timestep = {}
        # And one that will map timesteps to batted ball velocity, in
        # mph; modified by compute_full_trajectory()
        self.x_velocity_at_timestep = {}
        # This dictionary is used by players to call off other players
        # whose positions have less fielding priority
        self.fielding_priorities = {
            'C': 0, 'P': 1, '1B': 2, '3B': 2, '2B': 3,
            'SS': 4, 'LF': 5, 'RF': 5, 'CF': 6
        }

        self.compute_full_trajectory()

    def compute_full_trajectory(self):
        # Enact a timestep-by-timestep physics simulation of the ball's
        # full course, recording its x-, y-, and z-coordinates at each
        # timestep; first, set initial values at point of contact
        x, y = 0, 1.0668  # Coordinates at point of contact, in meters
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
        COR = 0.48  # Coefficient of restitution TODO should be self.ballpark.COR[(x, y)]
        COF = 0.31  # Coefficient of friction TODO should be self.ballpark.COF[(x, y)]
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
        coordinate_x = 0.0
        coordinate_y = 0.0  # Right over home plate still
        coordinate_z = 3.5
        self.position_at_timestep[0.0] = coordinate_x, coordinate_y, coordinate_z
        self.x_velocity_at_timestep[0.0] = v * 2.23694  # Convert to mph
        # Simulate movement of the ball up to the point that it "stops" -- to
        # avoid computational overkill, we say that a ball has stopped once
        # its horizontal component of velocity falls below 1 m/s and it is not
        # six or more inches in the air
        while vx >= 1 or y > 0.1524 or time_since_contact < 0.6:  # Baseball hasn't stopped moving
            # Increment time
            time_since_contact += timestep
            # If ball hit the ground on the last timestep, make
            # it bounce
            if y <= 0:
                # If this was the first time the ball hit the ground,
                # record distance in feet
                if self.true_distance is None:
                    self.true_distance = int(x * 3.28084)
                    self.true_landing_point = int(coordinate_x), int(coordinate_y)
                    self.hang_time = time_since_contact
                vy *= -1  # Reverse vertical component of velocity
                vy *= COR  # Adjust for coefficient of restitution of the turf
                vx *= COF  # Adjust for friction of the turf
                v = math.sqrt(vx**2 + vy**2)
            # Calculate new physics x and y coordinates
            x += (vx*timestep) + (ax * timestep**2) / 2
            y += (vy*timestep) + (ay * timestep**2) / 2
            if y < 0:
                y = 0  # A necessary approximation
            # Calculate new acceleration components
            ax = -(D/m)*v*vx
            ay = -g-(D/m)*v*vy
            # Calculate new velocity components
            vx += ax*timestep
            vy += ay*timestep
            v = math.sqrt(vx**2 + vy**2)
            # Calculate, convert, and record new actual ball x-, y-, z-coordinates
            coordinate_x = x * math.sin(math.radians(self.horizontal_launch_angle))
            coordinate_x *= 3.28084  # Convert meters to feet
            coordinate_y = x * math.cos(math.radians(self.horizontal_launch_angle))
            coordinate_y *= 3.28084
            coordinate_z = y * 3.28084
            self.position_at_timestep[time_since_contact] = (
                coordinate_x, coordinate_y, coordinate_z
            )
            self.x_velocity_at_timestep[time_since_contact] = v * 2.23694  # Convert to mph
            if coordinate_z > self.apex:
                self.apex = coordinate_z
        # Baseball has now stopped moving (to avoid computational overkill, we
        # say that a ball has stopped once its horizontal component of velocity
        # falls below 1 m/s and it is not six or more inches in the air) --
        # record resting data for a final timestep
        time_since_contact += timestep
        self.position_at_timestep[time_since_contact] = (
            coordinate_x, coordinate_y, 0.0
        )
        self.x_velocity_at_timestep[time_since_contact] = 0.0
        # If the ball just landed for the first time on the last timestep, the
        # true landing point, etc., may not have been recorded (pesky bug, but
        # I believe this, though inelegant, should fix it)
        if self.true_distance is None:
            self.true_distance = int(x * 3.28084)
            self.true_landing_point = int(coordinate_x), int(coordinate_y)
            self.hang_time = time_since_contact

    def get_read_by_fielders(self):
        """Obligate fielders to their defensive responsibilities."""
        timesteps = self.position_at_timestep.keys()
        timesteps.sort()
        for fielder in self.at_bat.fielders:
            for timestep in timesteps[5:]:  # Fielders take 0.4s to react
                height_of_ball_at_timestep = (
                    self.position_at_timestep[timestep][2]
                )
                if height_of_ball_at_timestep < fielder.fieldable_ball_max_height:
                    # Determine distance between fielder origin location and
                    # ball location at that timestep
                    x1, y1 = fielder.location
                    x2, y2 = self.position_at_timestep[timestep][:2]
                    x_diff = (x2-x1)**2
                    y_diff = (y2-y1)**2
                    dist_from_fielder_origin_at_timestep = math.sqrt(x_diff + y_diff)
                    # Determine slope between fielder origin location and
                    # ball location at that timestep
                    x_change = x2-x1
                    y_change = y2-y1
                    slope = y_change/float(x_change)
                    # Determine the maximum rate of speed with which the fielder could
                    # make his approach to the ball location at this timestep while
                    # still tracking the ball properly -- the more you are moving toward
                    # home plate, the faster you can move; the more you are moving toward
                    # the center field wall, the less quickly you can move
                    if x_change < 0:
                        # You are moving left, so invert the slope so that it
                        # becomes intuitive for our computation here
                        temp_slope = slope * -1
                    else:
                        temp_slope = slope
                    if temp_slope <= 0:
                        # You are moving toward home plate, so you can run much
                        # faster -- the maximum speed will be 90% of your full speed
                        # multiplied by your ball-tracking ability (this allows
                        # ball-tracking wizards like Willie Mays to run faster while
                        # fielding), and the minimum speed (for when you are running
                        # laterally) will be that percentage less ~20%
                        temp_slope = abs(temp_slope)
                        if temp_slope > 15:
                            temp_slope = 15
                        diff = 15-temp_slope
                        max_speed = 0.9 * fielder.ball_tracking_ability
                        max_rate_of_speed_to_this_location = max_speed - (0.013333333333333333 * diff)
                        if max_rate_of_speed_to_this_location > 0.97:
                            # Enforce a 0.97 ceiling to account for time spent accelerating
                            max_rate_of_speed_to_this_location = 0.97
                    elif temp_slope > 0:
                        # You are moving toward the outfield fence -- here, max speed
                        # represents lateral movement, which was minimum speed in above
                        # block; now, minimum speed is lateral speed less ~20%
                        if temp_slope > 15:
                            temp_slope = 15
                        diff = abs(0-temp_slope)
                        max_speed = (0.7 * fielder.ball_tracking_ability)
                        max_rate_of_speed_to_this_location = max_speed - (0.013333333333333333 * diff)
                        if max_rate_of_speed_to_this_location > 0.97:
                            max_rate_of_speed_to_this_location = 0.97
                    # Determine how long it would take fielder to get to the ball
                    # location at that timestep -- here we consider the direction of
                    # movement in the fielder's approach to the ball location at that
                    # timestep, which affected the maximum rate of speed that we
                    # calculated in the above block
                    time_to_ball_location_at_timestep = (
                        dist_from_fielder_origin_at_timestep *
                        (fielder.full_speed_sec_per_foot * max_rate_of_speed_to_this_location)
                    )
                    # Account for the fact that it takes fielders 0.4 seconds to begin
                    # moving once the ball is hit
                    time_to_ball_location_at_timestep += 0.4
                    # Check if fielder could make it to that ball location in time
                    # to potentially field it
                    if time_to_ball_location_at_timestep <= timestep:
                        fielder.time_needed_to_field_ball = time_to_ball_location_at_timestep
                        # Set location where fielding attempt will occur, if this
                        # fielder ends up playing the ball
                        fielder.immediate_goal = self.position_at_timestep[timestep]
                        # Set speed, in feet per timestep, that fielder will act
                        # at in his approach to the immediate goal location (again,
                        # should he end up fielding the ball)
                        fielder.dist_per_timestep = (
                            (dist_from_fielder_origin_at_timestep/(timestep-0.4)) * 0.1
                        )
                        fielder.relative_rate_of_speed = (
                            1000 * fielder.dist_per_timestep *
                            (fielder.full_speed_sec_per_foot * max_rate_of_speed_to_this_location)
                        )
                        break
                    elif timestep == timesteps[-1]:
                        # Fielder can only make it to the ball after it has stopped
                        # moving, so the time needed to field it is simply the time
                        # it would take the fielder to run full speed to the point
                        # where the ball will come to a stop
                        fielder.time_needed_to_field_ball = time_to_ball_location_at_timestep
                        # Set location where fielding attempt will occur, if this
                        # fielder ends up playing the ball
                        fielder.immediate_goal = self.position_at_timestep[timestep]
                        # This fielder will act at full speed in his approach to the
                        # immediate goal location (again, should he end up fielding
                        # the ball)
                        fielder.dist_per_timestep = (
                            (0.1/fielder.full_speed_sec_per_foot) * max_rate_of_speed_to_this_location
                        )
                        fielder.relative_rate_of_speed = 100

        self.obligated_fielder = (
            min(self.at_bat.fielders, key=lambda f: f.time_needed_to_field_ball)
        )

    def move(self):
        """Move the batted ball along its course for one timestep."""
        # Since we've already computed the ball's full trajectory, we
        # simply look up where it will be at this timestep
        if self.time_since_contact in self.position_at_timestep:
            self.location = self.position_at_timestep[self.time_since_contact][:2]
            self.height = self.position_at_timestep[self.time_since_contact][-1]
            self.speed = self.x_velocity_at_timestep[self.time_since_contact]
            # Check if the ball has stopped moving
            if self.speed == 0 and self.height == 0:
                self.stopped = True
            # Check for any change in batted ball attributes
            if self.height <= 0:
                self.landed = True
                if not self.left_playing_field:
                    self.n_bounces += 1
                if self.in_foul_territory:
                    self.landed_foul = True
            if (self.location[1] < 0 or
                    abs(self.location[0]) > self.location[1]):
                self.in_foul_territory = True
            else:
                self.in_foul_territory = False
            if self.location[1] > 67:
                self.passed_first_or_third_base = True
            if self.location[0] < -226:
                # Ball crossed either the plane of the playing field
                # sometime during the last timestep, and right at the
                # junction of the foul and outfield walls -- we will
                # have to approximate where it crossed the plane, which
                # due to the control sequence of elifs below will
                # favor home runs ever so slightly
                playing_field_lower_bound_at_this_x = (
                    self.ballpark.playing_field_lower_bound[-226]
                )
                playing_field_upper_bound_at_this_x = (
                    self.ballpark.playing_field_upper_bound[-226]
                )
            elif self.location[0] > 226:
                # We will have to approximate where it crossed the plane
                # (see above comment block for explanation)
                playing_field_lower_bound_at_this_x = (
                    self.ballpark.playing_field_lower_bound[-226]
                )
                playing_field_upper_bound_at_this_x = (
                    self.ballpark.playing_field_upper_bound[-226]
                )
            else:
                playing_field_lower_bound_at_this_x = (
                    self.ballpark.playing_field_lower_bound[int(self.location[0])]
                )
                playing_field_upper_bound_at_this_x = (
                    self.ballpark.playing_field_upper_bound[int(self.location[0])]
                )
            if 0 <= abs(playing_field_lower_bound_at_this_x-self.location[1]) < 1.5:
                self.at_the_foul_wall = True
                self.crossed_plane_foul = True
            elif 0 <= abs(self.location[1]-playing_field_upper_bound_at_this_x) < 1.5:
                self.at_the_outfield_wall = True
                self.crossed_plane_fair = True
            elif self.location[1] > playing_field_upper_bound_at_this_x:
                self.left_playing_field = True
                self.crossed_plane_fair = True
            elif self.location[1] < playing_field_lower_bound_at_this_x:
                self.left_playing_field = True
                self.crossed_plane_foul = True
            if ((int(self.location[0]), int(self.location[1])) in
                    self.at_bat.game.ballpark.ground_rule_coords):
                self.ground_rule_incurred = True
        elif self.time_since_contact > max(self.position_at_timestep.keys()):
            self.stopped = True  # Ball has stopped moving, so nothing will change
        else:
            raise Exception("Call to BattedBall.move() for an invalid timestep.")

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


class FoulTip(object):

    def __init__(self, swing):
        # Note: the swing may be a Bunt.
        self.swing = swing
        if swing.bunt:
            self.bunt = True
        self.at_bat = swing.at_bat
        # Result will either be a Strike object or FoulBall object,
        # depending on whether the catcher receives the foul tip
        # cleanly
        self.result = None