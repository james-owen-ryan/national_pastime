### CAN DELETE ASAP IF NOT NEEDED

if self.throw.runner:
                                if not self.throw.runner.safely_on_base:
                                    self.true_call = "Out"
                                    if (self.throw.runner is batted_ball.running_to_first and
                                            self.throw.runner.percent_to_base > 0.9):

                                        # If it's close, umpire could potentially get it wrong
                                        # TODO current method is designed for plays at first only...
                                        call = self.umpire.call_play_at_base(baserunner=self.throw.runner,
                                                                             throw=self.throw)
                                    else:
                                        call = self.true_call
                                    if call == "Out":
                                        if self.throw.runner.forced_to_advance or self.throw.runner.forced_to_retreat:
                                            ForceOut(batted_ball=batted_ball, baserunner=self.throw.runner,
                                                     base=self.throw.base, true_call=self.true_call,
                                                     forced_by=self.throw.thrown_to, assisted_by=[self.throw.thrown_by])
                                        else:
                                            TagOut(batted_ball=batted_ball, baserunner=self.throw.runner,
                                                   true_call=self.true_call, tagged_by=self.throw.thrown_to,
                                                   assisted_by=[self.throw.thrown_by])
                                    elif call == "Safe":
                                        # if self.batter is batted_ball.running_to_first:
                                        #     hit = Single(batted_ball=batted_ball, true_call=true_call)
                                        # elif self.batter is batted_ball.running_to_second:
                                        #     hit = Double(batted_ball=batted_ball, true_call=true_call)
                                        # hit.beat_throw_by = -0.1
                                        pass
                                elif self.throw.runner.safely_on_base and batted_ball.landed:
                                    self.true_call = "Safe"
                                    if (self.throw.runner is batted_ball.running_to_first and
                                            self.throw.percent_to_target > 0.9):
                                        print "-- Close play at {} -- umpire {} will make the call...".format(
                                            self.throw.base, self.umpire.name
                                        )
                                        # If it's close, umpire could potentially get it wrong
                                        call = self.umpire.call_play_at_base(baserunner=self.batter, throw=self.throw)
                                    else:
                                        call = self.true_call
                                    if call == "Safe":
                                        # if self.throw:
                                        #     beat_throw_by = 0.0
                                        #     while not self.throw.reached_target:
                                        #         self.throw.move()
                                        #         beat_throw_by += 0.1
                                        #     hit.beat_throw_by = beat_throw_by
                                        pass
                                    elif call == "Out":
                                        if self.throw.runner.forced_to_advance or self.throw.runner.forced_to_retreat:
                                            ForceOut(batted_ball=batted_ball, baserunner=self.throw.runner,
                                                     base=self.throw.base, true_call=self.true_call,
                                                     forced_by=self.throw.thrown_to, assisted_by=[self.throw.thrown_by])
                                        else:
                                            TagOut(batted_ball=batted_ball, baserunner=self.throw.runner,
                                                   true_call=self.true_call, tagged_by=self.throw.thrown_to,
                                                   assisted_by=[self.throw.thrown_by])
                            elif not self.throw.runner:
                                batted_ball.resolved = True


###################
###################
###################



if count == 00 or count == 10:
            # Count is 0-0 or 1-0
            if random.random() < 0.35:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 01:
            if random.random() < 0.15:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 20:
            if random.random() < 0.4:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 11:
            if random.random() < 0.2:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 02:
            if random.random() < 0.1:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 30:
            if random.random() < 0.6:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 21:
            if random.random() < 0.28:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 12:
            if random.random() < 0.11:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 31:
            if random.random() < 0.31:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 22:
            if random.random() < 0.15:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
        elif count == 32:
            if random.random() < 0.17:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                self.kind, self.intended_x, self.intended_y = "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                self.kind, self.intended_x, self.intended_y = "fastball", x, y




def test(self, pitch_coords=None, count=None, power=0.8):
        p = self.pitcher
        b = self.batter
        c = self.catcher
        if count is None:
            count = random.choice((00, 01, 02,
                               10, 11, 12,
                               20, 21, 22,
                               30, 31, 32))
        if not self.pitches:
            count = 00
        self.count = count
        print "\n\tCount: {}\n".format(count)
        for fielder in self.fielders:
            fielder.get_in_position(at_bat=self)
        _, x, y = p.decide_pitch(at_bat=self)  # _ is kind
        if pitch_coords:
            x, y = pitch_coords
        pitch = p.pitch(at_bat=self, x=x, y=y)
        print "Pitcher intends {} at [{}, {}]".format(
            pitch.pitcher_intention, pitch.pitcher_intended_x,
            pitch.pitcher_intended_y)
        print "\n\tThe pitch...\n"
        print "The ball is a {} at [{}, {}]".format(
            pitch.true_call, round(pitch.actual_x, 2),
            round(pitch.actual_y, 2))
        decided_to_swing = (
            b.decide_whether_to_swing(pitch)
        )
        print "Batter hypothesizes {} at [{}, {}]".format(
            pitch.batter_hypothesis, round(pitch.batter_hypothesized_x, 2),
            round(pitch.batter_hypothesized_y, 2))
        if not decided_to_swing:
            pitch.call = pitch.would_be_call
            print "\n\tBatter does not swing.\n"
            print "\n\tAnd the call is..."
            if pitch.call == "Strike":
                print "\n\t\tSTRIKE!"
            elif pitch.call == "Ball":
                print "\n\t\tBall."
            return pitch
        if decided_to_swing:
            print "\n\tBatter swings..."
            _, incline, pull = (
                b.decide_swing(pitch)
            )
            power = power
            swing = b.swing(pitch, power, incline,
                            pull)
            print "Timing is {}".format(swing.timing)
            print "Contact x-coord is {}".format(swing.contact_x_coord)
            print "Contact y-coord is {}".format(swing.contact_y_coord)
            if swing.contact:
                print "\n\tThe ball is hit!\n"
                bb = swing.result
                bb.get_landing_point_and_hang_time(timestep=0.1)
                self.turtle.penup()
                self.turtle.goto(bb.true_landing_point)
                self.turtle.color("purple")
                self.turtle.dot(3)
                print "\n\tVertical launch angle: {}".format(bb.vertical_launch_angle)
                print "\tHorizontal launch angle: {}".format(bb.horizontal_launch_angle)
                print "\tDistance: {}".format(bb.true_distance)
                print "\tLanding point: {}".format(bb.true_landing_point)
                bb.get_distances_from_fielders_to_landing_point()
                for fielder in self.fielders:
                    print "\t\n{} distance to landing point: {}".format(
                        fielder.position, fielder.dist_to_landing_point
                    )
                for fielder in self.fielders:
                    if fielder.batted_ball_pecking_order:
                        print "{} has pecking order {}".format(fielder.position, fielder.batted_ball_pecking_order)
                return bb
            elif not swing.contact:
                print "\n\tSwing and a miss!"
                print "Reasons: {}\n".format(swing.swing_and_miss_reasons)
                return swing



def dist(fielder, ball_coords):
    x1, y1 = fielder.location
    x2, y2 = ball_coords
    x_diff = (x2-x1)**2
    y_diff = (y2-y1)**2
    return math.sqrt(x_diff + y_diff)




 ### CODE USED TO BUILD FIELDER RESPONSIBILITY DICT 09-08-2014

 def test(es, vla, hla):
    # ab.turtle.clearscreen()
    # ab.draw_playing_field()
    # turtle = ab.turtle
    bb = BattedBallTest(es,vla, hla)
    timesteps = bb.position_at_timestep.keys()
    timesteps.sort()
    # for timestep in timesteps:
    #     x, y, z = bb.position_at_timestep[timestep]
    #     turtle.goto(x, y)
    #     if z >= 8.5 or timestep < 0.65:
    #         turtle.color("red")
    #     else:
    #         turtle.color("green")
    #         fieldable.append([x, y])
    #     turtle.dot(2)
    # turtle.update()
    for fielder in ab.fielders:
        fielder.timestep = 1001  # Means they can only make it to ball after it stops
        for timestep in timesteps:
            height_of_ball_at_timestep = (
                bb.position_at_timestep[timestep][2]
            )
            if timestep > 0.4 and height_of_ball_at_timestep < 8.5:  # Ball is fieldable
                # Determine distance between fielder origin location and
                # ball location at that timestep
                x1, y1 = fielder.location
                x2, y2 = bb.position_at_timestep[timestep][:2]
                x_diff = (x2-x1)**2
                y_diff = (y2-y1)**2
                dist_from_fielder_origin_at_timestep = math.sqrt(x_diff + y_diff)
                time_to_ball_location_at_time = dist_from_fielder_origin_at_timestep * 0.041
                if time_to_ball_location_at_time <= timestep:
                    # Set location where fielding attempt will occur
                    fielder.timestep = timestep
                    break
    responsible = min(ab.fielders, key=lambda f: f.timestep)
    return responsible.position

def build_fielder_responsibility_dict():
    responsible = {}
    for es in xrange(0, 150):
        print es
        for vla in xrange(-180, 181):
            for hla in xrange(-90, 91):
                responsible[(es, vla, hla)] = test(es, vla, hla)
    return responsible



 # while self.outs < 3:
        #     # batting_team.consider_changes(game=self.game)
        #     # .pitching_team.consider_changes(game=self.game)
        #     # self.simulate_deadball_events()
        #     ab = AtBat(inning=self, pitcher=pitching_team.pitcher,
        #                batter=batting_team.batter, fielders=pitching_team.fielders)
        #     print ab.outcome
        #     print "1B: {}  2B: {}  3B: {}".format(self.first, self.second, self.third)
        #     raw_input("")
        # self.outs = 0
        # # Enact bottom frame
        # self.frame = 'Bottom'
        # print "\t {} \n".format(self)
        # raw_input("")
        # batting_team = self.game.home_team
        # pitching_team = self.game.away_team
        # if not batting_team.runs > pitching_team.runs:
        #     while self.outs < 3:
        #         # self.batting_team.consider_changes(game=self.game)
        #         # self.pitching_team.consider_changes(game=self.game)
        #         # self.simulate_deadball_events()
        #         ab = AtBat(inning=self, pitcher=pitching_team.pitcher,
        #                    batter=batting_team.batter, fielders=pitching_team.fielders)
        #         print ab.outcome
        #         print "1B: {}  2B: {}  3B: {}".format(self.first, self.second, self.third)
        #         raw_input('')


def enact(self):
        # if pitcher.intent == "bean":
        #     batter.walk(beanball=True)
        # if pitcher.intent == "walk":
        #     batter.walk(intentional=True)
        x = random.random()
        if x < 0.1:
            return self.home_run()
        elif x < 0.4:
            return self.strikeout(swing_and_a_miss=True)
        elif x < 0.75:
            return self.strikeout(called_third_strike=True)
        elif x < 0.8:
            return self.walk(beanball=True)
        elif x < 0.9:
            return self.walk(hit_by_pitch=True)
        elif x < 0.95:
            return self.walk(intentional=True)
        else:
            return self.walk()

    def strikeout(self, called_third_strike=False, swing_and_a_miss=False):
        # Articulate the outcome
        if called_third_strike:
            outcome = "{} called out on strikes".format(self.batter.ln)
        elif swing_and_a_miss:
            outcome = "{} strikes out".format(self.batter.ln)
        # Increment batting team's outs
        self.inning.outs += 1
        # Get batting team's next batter
        self.batter.team.batter = self.game.get_next_batter(self.batter.team)
        return outcome

    def walk(self, beanball=False, hit_by_pitch=False, intentional=False):
        # Begin to articulate the outcome
        if beanball:
            outcome = "{} intentionally beans {}".format(
                self.pitcher.ln, self.batter.ln
            )
        elif hit_by_pitch:
            outcome = "{} hit by pitch".format(
                self.batter.ln
            )
        elif intentional:
            outcome = "{} intentionally walks {}".format(
                self.pitcher.ln, self.batter.ln
            )
        else:
            outcome = "{} walks".format(
                self.batter.ln
            )
        # Advance this runner and any preceding runners, as necessary
        if self.inning.first and self.inning.second and self.inning.third:
            outcome += (
                " [{} scores, {} to third, {} to second]".format(
                    self.inning.third.ln, self.inning.second.ln, self.inning.first.ln
                )
            )
            self.batter.team.runs += 1
            self.inning.third = self.inning.second
            self.inning.second = self.inning.first
            self.inning.first = self.batter
        elif self.inning.first and self.inning.second:
            outcome += (
                " [{} to third, {} to second]".format(
                    self.inning.second.ln, self.inning.first.ln
                )
            )
            self.inning.third = self.inning.second
            self.inning.second = self.inning.first
            self.inning.first = self.batter
        elif self.inning.first:
            outcome += " [{} to second]".format(self.inning.first.ln)
            self.inning.second = self.inning.first
            self.inning.first = self.batter
        else:
            self.inning.first = self.batter
        # If it's a beanball, simulate extracurricular activity [TODO]
        if beanball:
            pass
        # Get batting team's next batter
        self.batter.team.batter = self.game.get_next_batter(self.batter.team)
        return outcome

    def home_run(self):
        # Begin to articulate the outcome
        outcome = "{} homers".format(self.batter.ln)
        if self.inning.third or self.inning.second or self.inning.first:
            outcome += " ["
            # Score for any preceding runners
            if self.inning.third:
                outcome += "{} scores, ".format(self.inning.third.ln)
                self.batter.team.runs += 1
                self.inning.third = None
            if self.inning.second:
                outcome += "{} scores, ".format(self.inning.second.ln)
                self.batter.team.runs += 1
                self.inning.second = None
            if self.inning.first:
                outcome += "{} scores, ".format(self.inning.first.ln)
                self.batter.team.runs += 1
                self.inning.first = None
            outcome = outcome[:-2] + "]"
        # Get batting team's next batter
        self.batter.team.batter = self.game.get_next_batter(self.batter.team)
        return outcome


def compute_full_trajectory(self):
    # Enact a timestep-by-timestep physics simulation of the ball's
    # full course, recording its x-, y-, and z-coordinates at each
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
    coordinate_x = 0
    coordinate_y = 0  # Right over home plate still
    coordinate_z = 3.5
    self.position[0.0] = coordinate_x, coordinate_y, coordinate_z
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
        self.position[time_since_contact] = coordinate_x, coordinate_y, coordinate_z