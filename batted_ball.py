import math


class BattedBall(object):

    def __init__(self, swing, exit_speed, horizontal_launch_angle,
                 vertical_launch_angle, bunt=None):
        self.at_bat = swing.at_bat
        self.ballpark = self.at_bat.game.ballpark
        self.swing = swing
        self.bunt = bunt
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
        self.passed_first_or_third_base = False
        self.touched_by_fielder = False
        self.landed = False  # Ball has landed at least once
        self.stopped = False  # Ball has stopped moving
        self.in_foul_territory = False
        self.fieldable = True  # Ball is less than eight feet off the ground
        self.at_the_wall = False  # Ball is right at the wall
        self.left_playing_field = False
        # Prepare a dictionary that will map timesteps to batted
        # ball x-, y-, and z-coordinates; modified below
        self.position_at_timestep = {}
        # Set initial physics values at point of contact in preparation
        # for a timestep-by-timestep simulation of the ball's trajectory
        self._x, self._y = 0, 1.0668  # Coordinates at point of contact, in meters
        self._v = self.exit_speed * 0.44704  # Convert mph to m/s
        self._g = 9.81  # Standard gravitational acceleration in m/s
        th = math.radians(self.vertical_launch_angle)
        self._vx = self._v * math.cos(th)  # Initial horizontal component of velocity
        self._vy = self._v * math.sin(th)  # Initial vertical component of velocity
        self._m = self.ball.weight * 0.0283495  # Convert ounces to kg
        rho = 1.2  # Air density -- TODO change depending on weather, altitude
        C = 0.3  # Drag coefficient  -- TODO change depending on certain things
        A = 0.004208351855042743  # Cross-sectional area of ball in meters
        self._D = (rho * C * A) / 2  # Drag
        self._COR = 0.48  # Coefficient of restitution TODO should be self.ballpark.COR[(x, y)]
        self._COF = 0.31  # Coefficient of friction TODO should be self.ballpark.COF[(x, y)]
        # Initial horizontal component of acceleration
        self._ax = -(self._D/self._m)*self._v*self._vx
        # Initial vertical component of acceleration
        self._ay = -self._g-(self._D/self._m)*self._v*self._vy
        # Record position at the initial timestep -- [NOTE: While it is
        # convenient for the physics computation to call the the horizontal
        # axis 'x' and the vertical axis 'y', in the baseball simulation it
        # makes more sense to call the vertical axis 'z', the axis moving
        # from home plate to center field 'y', and the axis moving from
        # third base to first base 'x'. As such, we convert the physics-
        # sim 'y' values to coordinate 'z' values, and then consider the
        # swing's horizontal launch angle to compute the additional
        # coordinate 'x' and 'y' values.]
        self.coordinate_x = 0.0
        self.coordinate_y = 0.0  # Right over home plate still
        self.coordinate_z = 3.5  # This is pre-converted to feet
        self.position_at_timestep[0.0] = self.coordinate_x, self.coordinate_y, self.coordinate_z
        # Determine landing point and hang time, disregarding potential
        # fielder or obstacle interruption, and fielder distances from
        # that landing point, given how they positioned themselves prior
        # to the pitch -- these will be used by fielders so that they can
        # read the ball as it comes off the bat and decide their immediate goals
        self.get_landing_point_and_hang_time()
        self.get_distances_from_fielders_to_landing_point()

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
        # Simulate movement of the ball up to the point that it "stops" -- to
        # avoid computational overkill, we say that a ball has stopped once
        # its horizontal component of velocity falls below 1 m/s and it is not
        # six or more inches in the air
        while vx >= 1 or y > 0.1524:  # Baseball hasn't stopped moving
            # Increment time
            time_since_contact += timestep
            # If ball hit the ground on the last timestep, make
            # it bounce
            if y <= 0:
                # If this was the first time the ball hit the ground,
                # record distance in feet
                if not self.true_distance:
                    self.true_distance = int(x * 3.28084)
                    self.true_landing_point = int(coordinate_x), int(coordinate_y)
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

    def get_landing_point_and_hang_time(self, timestep=0.1):
        """Simulate the initial trajectory of a batted ball.

        The point of this method is to get the batted ball's true landing
        point and hang time -- which disregard any potential interruption to
        its trajectory that may actually end up occurring -- which are used
        by fielders as they make an initial read of the ball as it comes off
        the bat. So that computational efforts aren't doubled, we also record
        the position of the ball at every timestep up through its initial
        landing, even though eventually these positions may not actually
        come to exist in the reality of the play.
        """
        # Simulate movement of the ball up to the point where it
        # would initially land, if uninterrupted in its flight
        time_since_contact = 0.0
        while not self.true_landing_point:
            if self._y <= 0:  # Baseball just landed
                # Baseball would land at this point -- record landing spot, distance,
                # and hangtime
                self.true_distance = int(self._x * 3.28084)
                self.true_landing_point = int(self.coordinate_x), int(self.coordinate_y)
                self.hang_time = time_since_contact
            else:  # Baseball still in flight
                # Increment time
                time_since_contact += timestep
                # Calculate new physics x and y coordinates
                self._x += (self._vx*timestep) + (self._ax * timestep**2) / 2
                self._y += (self._vy*timestep) + (self._ay * timestep**2) / 2
                if self._y < 0:
                    self._y = 0  # A necessary approximation
                # Calculate new acceleration components
                self._ax = -(self._D/self._m)*self._v*self._vx
                self._ay = -self._g-(self._D/self._m)*self._v*self._vy
                # Calculate new velocity components
                self._vx += self._ax*timestep
                self._vy += self._ay*timestep
                self._v = math.sqrt(self._vx**2 + self._vy**2)
                # Calculate, convert, and record new actual ball x-, y-, z-coordinates
                self.coordinate_x = self._x * math.sin(math.radians(self.horizontal_launch_angle))
                self.coordinate_x *= 3.28084  # Convert meters to feet
                self.coordinate_y = self._x * math.cos(math.radians(self.horizontal_launch_angle))
                self.coordinate_y *= 3.28084
                self.coordinate_z = self._y * 3.28084
                self.position_at_timestep[time_since_contact] = (
                    self.coordinate_x, self.coordinate_y, self.coordinate_z
                )

    def get_distances_from_fielders_to_landing_point(self):
        closest = (None, 1000)
        second_closest = (None, 1001)
        third_closest = (None, 1002)
        for fielder in self.at_bat.fielders:
            fielder.batted_ball_pecking_order = None
            x_diff = (fielder.location[0]-self.true_landing_point[0])**2
            y_diff = (fielder.location[1]-self.true_landing_point[1])**2
            dist = math.sqrt(x_diff + y_diff)
            fielder.dist_to_landing_point = dist
            if dist <= closest[1]:
                third_closest = second_closest
                second_closest = closest
                closest = (fielder, dist)
            elif dist <= second_closest[1]:
                third_closest = second_closest
                second_closest = (fielder, dist)
            elif dist <= third_closest[1]:
                third_closest = (fielder, dist)
        closest[0].batted_ball_pecking_order = 1
        second_closest[0].batted_ball_pecking_order = 2
        third_closest[0].batted_ball_pecking_order = 3

    def move(self, time_since_contact, timestep=0.1):
        """Move the batted ball along its course for one timestep."""
        # Make sure the ball hasn't already stopped moving
        assert not(self._vx < 1 and self._y < 0.1524), \
            "A call to BattedBall.move() was made to a ball " \
            "that had already stopped moving."
        # Check if we have already computed the ball's position at this
        # timestep during our simulation of its initial trajectory
        if time_since_contact in self.position_at_timestep:
            self.coordinate_x, self.coordinate_y, self.coordinate_z = (
                self.position_at_timestep[time_since_contact]
            )
        else:
            # If the ball hit the ground on the last timestep, make it bounce
            if self._y <= 0:
                self._vy *= -1  # Reverse vertical component of velocity
                self._vy *= self._COR  # Adjust for coefficient of restitution of the turf
                self._vx *= self._COF  # Adjust for friction of the turf
                self._v = math.sqrt(self._vx**2 + self._vy**2)
            # Calculate new physics x and y coordinates
            self._x += (self._vx * timestep) + (self._ax * timestep**2) / 2
            self._y += (self._vy * timestep) + (self._ay * timestep**2) / 2
            if self._y < 0:
                self._y = 0  # A necessary approximation
            # Calculate new acceleration components
            ax = -(self._D/self._m)*self._v*self._vx
            ay = -self._g-(self._D/self._m)*self._v*self._vy
            # Calculate new velocity components
            self._vx += ax * timestep
            self._vy += ay * timestep
            self._v = math.sqrt(self._vx**2 + self._vy**2)
            # Calculate, convert, and record new actual ball x-, y-, z-coordinates
            self.coordinate_x = (
                self._x * math.sin(math.radians(self.horizontal_launch_angle))
            )
            self.coordinate_x *= 3.28084  # Convert meters to feet
            self.coordinate_y = (
                self._x * math.cos(math.radians(self.horizontal_launch_angle))
            )
            self.coordinate_y *= 3.28084
            self.coordinate_z = self._y * 3.28084
            self.position_at_timestep[time_since_contact] = (
                self.coordinate_x, self.coordinate_y, self.coordinate_z
            )
            # Check if ball will now (essentially) stop moving -- to avoid computational
            # overkill, we say that a ball has stopped once its horizontal component of
            # velocity falls below 1 m/s and it is not six or more inches in the air
            if self._vx < 1 and self._y < 0.1524:
                self.stopped = True
        # Check for any change in batted ball attributes
        if self.coordinate_z <= 0:
            self.landed = True
        if self.coordinate_z <= 8:
            self.fieldable = True
        if (self.coordinate_y < 0 or
                abs(self.coordinate_x) > self.coordinate_y):
            self.in_foul_territory = True
        else:
            self.in_foul_territory = False
        playing_field_lower_bound_at_this_x = (
            self.ballpark.playing_field_lower_bound[self.coordinate_x]
        )
        playing_field_upper_bound_at_this_x = (
            self.ballpark.playing_field_upper_bound[self.coordinate_x]
        )
        if 0 <= playing_field_lower_bound_at_this_x-self.coordinate_y < 1.5:
            self.at_the_wall = True
        elif 0 <= self.coordinate_y-playing_field_upper_bound_at_this_x < 1.5:
            self.at_the_wall = True
        elif self.coordinate_y < playing_field_lower_bound_at_this_x:
            self.left_playing_field = True
        elif self.coordinate_y > playing_field_upper_bound_at_this_x:
            self.left_playing_field = True

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

