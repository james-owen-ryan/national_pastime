import math
import random


class BattedBall(object):

    def __init__(self, swing, exit_speed, horizontal_launch_angle,
                 vertical_launch_angle):
        # Note: swing may be a Bunt
        self.at_bat = swing.at_bat
        self.ballpark = self.at_bat.game.ballpark
        self.swing = swing
        swing.result = self
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
        self.landing_timestep = None  # Used as annotation of potential for a fly out
        self.second_landing_timestep = None  # Likewise, for games with bounding fly outs
        self.outfield_fence_contact_timestep = None  # Timestep batted ball hit the outfield fence
        self.foul_fence_contact_timestep = None
        self.foul_pole_contact_timestep = None
        self.contacted_outfield_wall = False
        self.contacted_foul_fence = False
        self.contacted_foul_pole = False
        self.apex = 0.0
        self.location = [0, 0]
        self.final_location = None
        self.height = 3.5
        self.time_since_contact = 0.0  # Adjusted by at_bat.enact()
        self.speed = exit_speed
        self.obligated_fielder = None
        self.fielder_with_chance = None
        self.fielded_by = None
        self.fielding_difficulty = None  # Modified by fielder.field_ball()
        self.fielding_acts = []
        self.touched_by_fielder = False   # Modified by fielder.field_ball()
        self.bobbled = False  # Modified by fielder.field_ball()
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
        # This attribute is dynamic, and used so that multiple fly outs aren't awarded by umpire.officiate()
        self.fly_out_call_given = False
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
        self.classify_self()

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
        # six or more inches in the air -- or contacts the foul pole, in which
        # case we know a home run will be called and the rest of the trajectory
        # is irrelevant and thus not worth computing
        while (vx >= 1 or y > 0.1524 or time_since_contact < 0.6) and not self.foul_pole_contact_timestep:
            # Increment time
            last_timestep = time_since_contact
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
                if not self.landing_timestep:
                    self.landing_timestep = time_since_contact-timestep  # The landing actually happened last timestep
                elif not self.second_landing_timestep:
                    self.second_landing_timestep = time_since_contact-timestep
                vy *= -1  # Reverse vertical component of velocity
                vy *= COR  # Adjust for coefficient of restitution of the turf
                vx *= COF  # Adjust for friction of the turf
                v = math.sqrt(vx**2 + vy**2)
            # If a ball hit the foul pole on last timestep, make note of it -- this will be called
            # a home run on this timestep by umpire.officiate()
            if abs(coordinate_x) >= 226 and int(coordinate_x) == int(coordinate_y):
                self.foul_pole_contact_timestep = last_timestep
            else:
                # If ball hit an outfield fence or foul fence on last timestep, make it bounce off that
                if (abs(coordinate_x) < 227 and not
                        (self.foul_fence_contact_timestep or self.outfield_fence_contact_timestep)):
                    # If the absolute value of the batted ball's coordinate x is greater than 226,
                    # we know that the ball left the playing field above the fence (I think -- otherwise,
                    # it's a reasonable approximation anyway, I think)
                    if coordinate_x > coordinate_y or coordinate_y < 0:
                        # Ball is heading foul -- check for whether the ball contacted a foul fence between
                        # the last timestep and now
                        if coordinate_y <= self.ballpark.playing_field_lower_bound[int(coordinate_x)]:
                            if coordinate_z <= self.ballpark.foul_fence_height[int(coordinate_x)]:
                                # Rewrite the coordinates of the last timestep so that coordinate-y is the exact
                                # coordinate of the wall -- otherwise it would be that a ball passed the
                                # wall and was then sucked back through it to simulate hitting it
                                self.position_at_timestep[last_timestep] = (
                                    coordinate_x, self.ballpark.playing_field_lower_bound[int(coordinate_x)], coordinate_z
                                )
                                self.foul_fence_contact_timestep = last_timestep
                                vx *= -1  # Reverse horizontal component of velocity
                                # TODO should be self.ballpark.outfield_fence_COR[x] or self.ballpark.foul_fence_COR[x]
                                vx *= 0.6  # Adjust for coefficient of restitution of the fence
                                # TODO should be self.ballpark.outfield_fence_COF[x] or self.ballpark.foul_fence_COF[x]
                                vy *= 0.15  # Adjust for friction of the fence
                                v = math.sqrt(vx**2 + vy**2)
                    else:
                        # Ball is heading fair -- check for whether the ball contacted the outfield fence
                        # between the last timestep and now
                        if coordinate_y >= self.ballpark.playing_field_upper_bound[int(coordinate_x)]:
                            if coordinate_z <= self.ballpark.outfield_fence_height[int(coordinate_x)]:
                                # Rewrite the coordinates of the last timestep so that coordinate-y is the exact
                                # coordinate of the wall -- otherwise it would be that a ball passed the
                                # wall and was then sucked back through it to simulate hitting it
                                self.position_at_timestep[last_timestep] = (
                                    coordinate_x, self.ballpark.playing_field_upper_bound[int(coordinate_x)], coordinate_z
                                )
                                self.outfield_fence_contact_timestep = last_timestep
                                vx *= -1  # Reverse horizontal component of velocity
                                # TODO should be self.ballpark.outfield_fence_COR[x] or self.ballpark.foul_fence_COR[x]
                                vx *= 0.6  # Adjust for coefficient of restitution of the fence
                                # TODO should be self.ballpark.outfield_fence_COF[x] or self.ballpark.foul_fence_COF[x]
                                vy *= 0.15  # Adjust for friction of the fence
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
        if not self.landing_timestep:
            self.landing_timestep = time_since_contact-timestep
        self.final_location = [coordinate_x, coordinate_y]

    def classify_self(self):
        """Determine batted-ball type and destination."""
        # Determine the type of batted ball
        if self.vertical_launch_angle < 5 and self.apex > 10:
            self.type = "Chopper"
        elif self.vertical_launch_angle < 5:
            if self.true_distance < 90:
                self.type = "Ground ball"
            else:
                self.type = "Line drive"
        elif float(self.true_distance)/self.apex >= 7.5:
            self.type = "Line drive"
        elif self.apex > self.true_distance:
            self.type = "Pop-up"
        else:
            self.type = "Fly ball"
        # Determine the destination area of the batted ball
        if self.true_distance <= 0:
            self.destination = "behind home plate"
        elif self.type == "Chopper" or self.type == "Ground ball":
            if self.horizontal_launch_angle < -45:
                self.destination = "left foul territory"
            elif -45 <= self.horizontal_launch_angle < -22.5:
                self.destination = "third"
            elif -22.5 <= self.horizontal_launch_angle <= 0:
                self.destination = "shortstop"
            elif 0 < self.horizontal_launch_angle <= 22.5:
                self.destination = "second"
            elif 22.5 < self.horizontal_launch_angle <= 45:
                self.destination = "first"
            else:
                self.destination = "right foul territory"
        else:
            if self.horizontal_launch_angle < -45:
                if self.true_distance < 90:
                    self.destination = "shallow left foul territory"
                elif self.true_distance > 250:
                    self.destination = "deep left foul territory"
                else:
                    self.destination = "left foul territory"
            elif -45 <= self.horizontal_launch_angle < -22.5:
                if self.true_distance < 100:
                    self.destination = "third"
                elif -45 <= self.horizontal_launch_angle < -27:
                    if self.true_distance < 150:
                        self.destination = "shallow left"
                    elif self.true_distance > 250:
                        self.destination = "deep left"
                    else:
                        self.destination = "left"
                else:  # -27 <= self.horizontal_launch_angle <= -22.5
                    if self.true_distance < 175:
                        self.destination = "shallow left-center"
                    elif self.true_distance > 275:
                        self.destination = "deep left-center"
                    else:
                        self.destination = "left-center"
            elif -22.5 <= self.horizontal_launch_angle <= 0:
                if self.true_distance < 140:
                    self.destination = "shortstop"
                elif -22.5 <= self.horizontal_launch_angle < -9:
                    if self.true_distance < 175:
                        self.destination = "shallow left-center"
                    elif self.true_distance > 275:
                        self.destination = "deep left-center"
                    else:
                        self.destination = "left-center"
                else:  # -9 <= self.horizontal_launch_angle <= 0
                    if self.true_distance < 200:
                        self.destination = "shallow center"
                    elif self.true_distance > 300:
                        self.destination = "deep center"
                    else:
                        self.destination = "center"
            elif 0 < self.horizontal_launch_angle <= 22.5:
                if self.true_distance < 140:
                    self.destination = "second"
                elif 0 <= self.horizontal_launch_angle < 9:
                    if self.true_distance < 200:
                        self.destination = "shallow center"
                    elif self.true_distance > 300:
                        self.destination = "deep center"
                    else:
                        self.destination = "center"
                else:  # 9 <= self.horizontal_launch_angle <= 22.5
                    if self.true_distance < 175:
                        self.destination = "shallow right-center"
                    elif self.true_distance > 275:
                        self.destination = "deep right-center"
                    else:
                        self.destination = "right-center"
            elif 22.5 < self.horizontal_launch_angle <= 45:
                if self.true_distance < 100:
                    self.destination = "first"
                elif 22.5 <= self.horizontal_launch_angle < 27:
                    if self.true_distance < 175:
                        self.destination = "shallow right-center"
                    elif self.true_distance > 275:
                        self.destination = "deep right-center"
                    else:
                        self.destination = "right-center"
                else:  # 27 <= self.horizontal_launch_angle <= 45
                    if self.true_distance < 150:
                        self.destination = "shallow right"
                    elif self.true_distance > 250:
                        self.destination = "deep right"
                    else:
                        self.destination = "right"
            else:
                self.destination = "right foul territory"
        if self.destination in (
            "first", "second", "third", "shortstop", "shallow left foul territory", "shallow right foul territory"
        ):
            self.hit_to_infield = True
            self.hit_to_outfield = False
        else:
            self.hit_to_infield = False
            self.hit_to_outfield = True

    def get_read_by_fielders(self):
        """Obligate fielders to their defensive responsibilities."""
        timesteps = self.position_at_timestep.keys()
        timesteps.sort()
        for fielder in self.at_bat.fielders:
            for timestep in timesteps[6:]:  # Fielders take 0.5s to react
                height_of_ball_at_timestep = (
                    self.position_at_timestep[timestep][2]
                )
                if height_of_ball_at_timestep < fielder.fieldable_ball_max_height:
                    # Determine distance between fielder origin location and
                    # ball location at that timestep
                    x1, y1 = fielder.location
                    x2, y2 = self.position_at_timestep[timestep][:2]
                    dist_from_fielder_origin_at_timestep = math.hypot(x1-x2, y1-y2)
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
                        (fielder.person.body.full_speed_seconds_per_foot * max_rate_of_speed_to_this_location)
                    )
                    # Account for the fact that it takes fielders 0.5 seconds to begin
                    # moving once the ball is hit
                    time_to_ball_location_at_timestep += 0.5
                    # Check if fielder could make it to that ball location in time
                    # to potentially field it
                    if time_to_ball_location_at_timestep <= timestep:
                        # Note whether the fielder would be attempting to record a fly out if
                        # they do end up playing the ball in the manner decided here -- here we
                        # allow for a two-timestep buffer, so that baserunners don't have perfect
                        # knowledge that, e.g., an actual close one-hopper wasn't going to be fly-out attempt
                        if timestep < self.landing_timestep+0.21:
                            fielder.attempting_fly_out = True
                        elif self.second_landing_timestep and timestep < self.second_landing_timestep:
                            # Depending on the rules enforced for this game, bounding balls
                            # could also represent fly-out opportunities
                            ball_in_foul_territory_at_this_timestep = bool(y2 < 0 or abs(x2) > y2)
                            if ball_in_foul_territory_at_this_timestep:
                                if self.at_bat.game.rules.foul_ball_on_first_bounce_is_out:
                                    fielder.attempting_fly_out = True
                            else:
                                if self.at_bat.game.rules.fair_ball_on_first_bounce_is_out:
                                    fielder.attempting_fly_out = True
                        # Note how long it would take the fielder to reach the location of
                        # the fielding chance, which is used below to determine the obligated
                        # fielder (though this person may be called off)
                        fielder.time_needed_to_field_ball = time_to_ball_location_at_timestep
                        fielder.timestep_of_planned_fielding_attempt = timestep
                        # Set location where fielding attempt will occur, if this
                        # fielder ends up playing the ball
                        fielder.immediate_goal = self.position_at_timestep[timestep]
                        # Set speed, in feet per timestep, that fielder will act
                        # at in his approach to the immediate goal location (again,
                        # should he end up fielding the ball)
                        fielder.dist_per_timestep = (
                            (dist_from_fielder_origin_at_timestep/(timestep-0.5)) * 0.1
                        )
                        fielder.relative_rate_of_speed = (
                            1000 * fielder.dist_per_timestep *
                            (fielder.person.body.full_speed_seconds_per_foot * max_rate_of_speed_to_this_location)
                        )
                        break
                    elif timestep == timesteps[-1]:
                        # Fielder can only make it to the ball after it has stopped
                        # moving, so the time needed to field it is simply the time
                        # it would take the fielder to run full speed to the point
                        # where the ball will come to a stop
                        fielder.time_needed_to_field_ball = max(timestep, time_to_ball_location_at_timestep)
                        actual_timestep_it_will_happen = timestep
                        while actual_timestep_it_will_happen < fielder.time_needed_to_field_ball:
                            actual_timestep_it_will_happen += 0.1
                        fielder.timestep_of_planned_fielding_attempt = actual_timestep_it_will_happen
                        # Set location where fielding attempt will occur, if this
                        # fielder ends up playing the ball
                        fielder.immediate_goal = self.position_at_timestep[timestep]
                        # This fielder will act at full speed in his approach to the
                        # immediate goal location (again, should he end up fielding
                        # the ball)
                        fielder.dist_per_timestep = (
                            (0.1/fielder.person.body.full_speed_seconds_per_foot) * max_rate_of_speed_to_this_location
                        )
                        fielder.relative_rate_of_speed = 90
        self.obligated_fielder = (
            min(self.at_bat.fielders, key=lambda f: f.time_needed_to_field_ball)
        )
        self.obligated_fielder.playing_the_ball = True

    def get_reread_by_fielders(self):
        """Obligate a new fielder to field the ball after it was not cleanly fielded."""
        self.fielder_with_chance = None
        self.obligated_fielder = None
        timesteps = self.position_at_timestep.keys()
        timesteps.sort()
        index_of_current_timestep = timesteps.index(self.time_since_contact)
        available_fielders = [f for f in self.at_bat.fielders if f not in (
            self.at_bat.playing_action.covering_first, self.at_bat.playing_action.covering_second,
            self.at_bat.playing_action.covering_third, self.at_bat.playing_action.covering_home
        )]
        fielder_max_rates_of_speed = {}
        for fielder in available_fielders:
            fielder.attempting_fly_out = False
            for timestep in timesteps[index_of_current_timestep+1:]:
                # 'index_of_current_timestep+1' because the fielder won't begin moving until
                # the while-loop iteration representing the *next* timestep -- sort of like how
                # we had to add 0.5s to all considerations in batted_ball.get_read_by_fielders to
                # simulate their delayed reaction time, here we have to add 0.1s to all considerations
                # to accommodate the control sequence of playing_action.enact()
                height_of_ball_at_timestep = (
                    self.position_at_timestep[timestep][2]
                )
                if height_of_ball_at_timestep < fielder.fieldable_ball_max_height:
                    # Determine distance between fielder current location and
                    # ball location at that timestep
                    x1, y1 = fielder.location
                    x2, y2 = self.position_at_timestep[timestep][:2]
                    dist_from_current_fielder_location_at_timestep = math.hypot(x1-x2, y1-y2)
                    # Determine slope between fielder origin location and
                    # ball location at that timestep
                    x_change = x2-x1
                    y_change = y2-y1
                    if x_change == 0:
                        if random.random() > 0.5:
                            x_change = 0.001
                        else:
                            x_change = -0.001
                    while y_change == 0:
                        if random.random() > 0.5:
                            y_change = 0.001
                        else:
                            y_change = -0.001
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
                    fielder_max_rates_of_speed[fielder] = max_rate_of_speed_to_this_location
                    # Determine how long it would take fielder to get to the ball
                    # location at that timestep -- here we consider the direction of
                    # movement in the fielder's approach to the ball location at that
                    # timestep, which affected the maximum rate of speed that we
                    # calculated in the above block
                    full_speed_dist_per_timestep = 0.1/fielder.person.body.full_speed_seconds_per_foot
                    full_speed_dist_per_timestep *= max_rate_of_speed_to_this_location
                    time_to_ball_location_at_timestep = (
                        dist_from_current_fielder_location_at_timestep / full_speed_dist_per_timestep
                    )
                    time_to_ball_location_at_timestep += fielder.reorienting_after_fielding_miss
                    time_to_ball_location_at_timestep += 0.1  # For reason stated at beginning of for loop
                    # Check if fielder could make it to that ball location in time
                    # to potentially field it
                    if time_to_ball_location_at_timestep <= timestep-self.time_since_contact:
                        # Note whether the fielder would be attempting to record a fly out if
                        # they do end up playing the ball in the manner decided here
                        if timestep < self.landing_timestep:
                            fielder.attempting_fly_out = True
                        elif self.second_landing_timestep and timestep < self.second_landing_timestep:
                            # Depending on the rules enforced for this game, bounding balls
                            # could also represent fly-out opportunities
                            ball_in_foul_territory_at_this_timestep = (
                                bool(y2 < 0 or abs(x2) > y2)
                            )
                            if ball_in_foul_territory_at_this_timestep:
                                if self.at_bat.game.rules.foul_ball_on_first_bounce_is_out:
                                    fielder.attempting_fly_out = True
                            else:
                                if self.at_bat.game.rules.fair_ball_on_first_bounce_is_out:
                                    fielder.attempting_fly_out = True
                        # Note how long it would take the fielder to reach the location of
                        # the fielding chance, which is used below to determine the obligated
                        # fielder (though this person may be called off)
                        fielder.time_needed_to_field_ball = timestep-self.time_since_contact
                        fielder.timestep_of_planned_fielding_attempt = timestep
                        break
                    elif timestep == timesteps[-1]:
                        # Fielder can only make it to the ball after it has stopped
                        # moving, so the time needed to field it is simply the time
                        # it would take the fielder to run full speed to the point
                        # where the ball will come to a stop
                        fielder.time_needed_to_field_ball = time_to_ball_location_at_timestep+self.time_since_contact
                        actual_timestep_it_will_happen = timestep
                        while actual_timestep_it_will_happen < fielder.time_needed_to_field_ball:
                            actual_timestep_it_will_happen += 0.1
                        fielder.timestep_of_planned_fielding_attempt = actual_timestep_it_will_happen
        self.obligated_fielder = min(available_fielders, key=lambda f: f.time_needed_to_field_ball)
        if self.obligated_fielder.playing_the_ball:
            if self.at_bat.game.trace:
                print "-- {} ({}) will try again to field the ball [{}]".format(
                    self.obligated_fielder.person.last_name, self.obligated_fielder.position, self.time_since_contact
                )
        else:
            if self.at_bat.game.trace:
                print "-- {} ({}) will now attempt to field the ball [{}]".format(
                    self.obligated_fielder.person.last_name, self.obligated_fielder.position, self.time_since_contact
                )
        self.obligated_fielder.making_goal_revision = True
        self.obligated_fielder.playing_the_ball = True
        # Set these attributes here, because, unlike with batted_ball.get_read_by_fielders(), any
        # available fielders who don't end up playing the ball will not then decide their actual
        # goals, thereby writing over the temporary .immediate_goal, etc., set during the above
        # computation -- rather, we want them to retain their goals and only the one who now
        # will play the ball to set the goal decided in the above computation
        if self.obligated_fielder.timestep_of_planned_fielding_attempt in self.position_at_timestep:
            self.obligated_fielder.immediate_goal = (
                self.position_at_timestep[self.obligated_fielder.timestep_of_planned_fielding_attempt]
            )
        else:
            # Fielder is planning to field the ball after it has stopped, thus his planned timestep
            # for the fielding attempt in not in batted_ball.position_at_timestep
            self.obligated_fielder.immediate_goal = self.final_location
        fielder_full_speed_dist_per_timestep = 0.1/self.obligated_fielder.person.body.full_speed_seconds_per_foot
        fielder_full_speed_dist_per_timestep *= fielder_max_rates_of_speed[self.obligated_fielder]
        self.obligated_fielder.dist_per_timestep = fielder_full_speed_dist_per_timestep
        # Assume flat-rate relative rate of speed, because there will always be a rush
        # to get to a missed ball, but the ball won't be flying through the air in a way
        # that would allow any fielder to reach full speed before attempting to field it
        self.obligated_fielder.relative_rate_of_speed = fielder_max_rates_of_speed[self.obligated_fielder] * 100
        # Make it so that our new obligated fielder is calling the ball and the
        # guy who was just playing the ball and missed is no longer playing it
        self.obligated_fielder.playing_the_ball = True
        for fielder in self.at_bat.fielders:
            if fielder is not self.obligated_fielder:
                fielder.playing_the_ball = False
                fielder.attempting_fly_out = False
        self.obligated_fielder.decide_immediate_goal(playing_action=self.at_bat.playing_action)

    def move(self):
        """Move the batted ball along its course for one timestep."""
        if self.at_the_foul_wall or self.at_the_outfield_wall:
            # A batted ball can't be at the wall for more than a single timestep, so
            # set these to False again
            self.at_the_foul_wall = self.at_the_outfield_wall = False
        if self.touched_by_fielder and self.height > 0.0:
            # self.location doesn't change
            self.height -= 3.2185  # Just gravity pulling it down
            self.speed = 0.0
            if self.height <= 0.0:
                self.height = 0.0
                if not self.landed:
                    if self.at_bat.game.trace:
                        print "-- Ball has landed at [{}, {}] [{}]".format(
                            int(self.location[0]), int(self.location[1]), self.time_since_contact
                        )
                    self.landed = True
                    if self.in_foul_territory:
                        self.landed_foul = True
                while self.n_bounces < 2:
                    self.n_bounces += 1  # Just picture it plopping down without a bounce -- no bounding fly outs here
            if self.speed == 0 and self.height == 0:
                self.stopped = True
            # Overwrite final resting location, in case someone needs to use that as their
            # immediate goal
            self.final_location = [self.location[0], self.location[1]]
            # Overwrite self.position_at_timestep and self.x_velocity_at_timestep
            # for what actually occurred at this timestep
            self.position_at_timestep[self.time_since_contact] = (
                self.location[0], self.location[1], self.height
            )
            self.x_velocity_at_timestep[self.time_since_contact] = self.speed
        elif not self.touched_by_fielder:
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
                if self.outfield_fence_contact_timestep == self.time_since_contact:
                    self.contacted_outfield_wall = True
                    if self.at_bat.game.trace:
                        print "-- Ball bounces off the outfield wall [{}]".format(self.time_since_contact)
                    for fielder in self.at_bat.fielders:
                        fielder.attempting_fly_out = False
                elif self.foul_fence_contact_timestep == self.time_since_contact:
                    self.contacted_foul_fence = True
                    if self.at_bat.game.trace:
                        print "-- Ball bounces off a foul fence [{}]".format(self.time_since_contact)
                elif self.foul_pole_contact_timestep == self.time_since_contact:
                    self.contacted_foul_pole = True
                    if self.at_bat.game.trace:
                        print "-- Ball bounces off a foul pole [{}]".format(self.time_since_contact)
                if (self.location[1] < 0 or
                        abs(self.location[0]) > self.location[1]):
                    self.in_foul_territory = True
                else:
                    self.in_foul_territory = False
                if self.height <= 0:
                    if not self.landed:
                        if self.at_bat.game.trace:
                            print "-- Ball has landed at [{}, {}] [{}]".format(
                                int(self.location[0]), int(self.location[1]), self.time_since_contact
                            )
                        self.landed = True
                        if self.in_foul_territory:
                            self.landed_foul = True
                    if not self.left_playing_field:
                        self.n_bounces += 1
                if self.location[1] > 67:
                    self.passed_first_or_third_base = True
                # If ball doesn't contact the wall at some point in its trajectory,
                # it may potentially have left the playing field at this timestep, so
                # check for that
                if not (self.contacted_foul_pole or self.contacted_foul_fence or self.contacted_outfield_wall):
                    if self.location[0] < -226:
                        # Ball crossed the plane of the playing field
                        # sometime during the last timestep, right at the
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
                # Modify self.position_at_timestep and self.x_velocity_at_timestep to
                # add these additional timesteps in which the ball is stopped
                self.position_at_timestep[self.time_since_contact] = (
                    self.location[0], self.location[1], self.height
                )
                self.stopped = True  # Ball has stopped moving, so nothing will change
                self.x_velocity_at_timestep[self.time_since_contact] = self.speed
            else:
                raise Exception("Call to BattedBall.move() for an invalid timestep: {}.".format(
                    self.time_since_contact)
                )

    def __str__(self):
        return "{} hit by {} toward {}".format(self.type, self.batter.person.last_name, self.destination)

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