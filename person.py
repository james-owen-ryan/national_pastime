import random
import os
from random import normalvariate as normal

from play import Pitch, Swing
from equipment import Bat, Ball

FORENAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/male_names.txt', 'r')
]

class Person(object):

    def __init__(self, birthplace):

        self.country = birthplace.country
        self.hometown = birthplace
        self.location = birthplace
        self.first_name = random.choice(FORENAMES)
        self.middle_name = random.choice(FORENAMES)
        self.last_name = random.choice(self.hometown.surnames)
        self.ln = self.last_name  # Used in game narratives
        self.full_name = (self.first_name + ' ' + self.middle_name + ' ' +
                          self.last_name)
        self.name = self.first_name + ' ' + self.last_name

        self.init_physical_attributes()
        self.init_mental_attributes()
        self.init_baseball_attributes()
        self.init_umpire_attributes()

        self.strike_zone = self.init_strike_zone()

        # Put here for now
        self.bat = Bat()
        self.primary_position = None
        self.position = None  # Position currently at -- used during game
        self.location = None  # Exact x, y coordinates on the field

    def init_physical_attributes(self):
        self.height = int(normal(69, 2))  # Average for 1870s
        # Determine weight, which is correlated with height
        self.weight = int(normal(self.height*2.25, self.height*0.2))
        # Determine body mass index (BMI)
        self.bmi = float(self.weight)/self.height**2 * 703
        # Determine coordination, which is correlated to BMI
        if self.bmi > 24:
            base = (21-abs(21-self.bmi))/23.
        else:
            base = 0.85
        self.coordination = normal(base, base/10)
        self.reflexes = normal(self.coordination, self.coordination/10)
        # Ball tracking ability affects a player's ability to anticipate
        # the trajectories and landing points of balls in movement
        self.ball_tracking_ability = 0.9 + random.random()/10
        if self.coordination > 1:
            self.coordination = 1.0
        if self.reflexes > 1:
            self.reflexes = 1.0
        if random.random() < 0.1:
            self.lefty = True
            self.righty = False
        else:
            self.lefty = False
            self.righty = True
        self.prime = int(round(normal(29, 1)))


    def init_mental_attributes(self):
        self.cleverness = random.random()


    def init_baseball_attributes(self):

        #       -- Fundamental attributes --

        # Every fielding chance has a specified difficulty, which
        # approximately represents the percentage likelihood that an
        # average player would successfully field the ball given the
        # circumstances at hand -- a player's fielding rating specifies
        # how increased their likelihood of successfully fielding a
        # batted ball is above the average player (ratings near 1.2
        # represent once-a-generation talents)
        primitive_fielding_ability = (
            self.coordination + (self.reflexes * 0.5) + self.ball_tracking_ability
        )
        diff_from_avg = primitive_fielding_ability - 2.16
        diff_from_avg /= 6.8
        if diff_from_avg >= 0:
            percentage_above_avg = abs(normal(0, diff_from_avg))
            self.fielding = 1 + percentage_above_avg
        else:
            percentage_below_avg = abs(normal(0, abs(diff_from_avg)))
            self.fielding = 1 - percentage_below_avg

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
        self.pitch_speed_mean = normal(65, 10)
        self.pitch_speed_sd = normal(self.pitch_speed_mean/20,
                                     self.pitch_speed_mean/30)

        # Pitch recognition is modeled similarly to pitch control,
        # with it being the player's standard deviation, in number of
        # baseball widths, that both horizontally and vertically a
        # pitched ball will deviate in where it crosses the vertical
        # plane of home plate with regard to where the batter believes
        # it will cross the plane
        self.pitch_recognition = abs(normal(2, 0.8))

        #           -- Batting attributes --

        # Batting power is composed by two values -- one represents
        # the player's mean hit distance when swinging with full
        # power, perfect contact, and perfect timing; the other
        # gives a standard deviation for swings having the same
        # conditions. These two values are then used to generate
        # a hit distance from a normal distribution
        # self.swing_power_mean = normal(300, 50)
        # self.swing_power_sd = normal(self.swing_power_mean/10,
        #                              self.swing_power_mean/15)

        # Bat speed is the speed with which a player swings his
        # bat at the point of contact with a pitched ball -- we
        # represent it in units representing mph/oz, i.e., the mph
        # of a swing for each ounce of bat weight; bat speed is
        # correlated to a player's weight
        self.bat_speed = normal(self.weight/2.6, self.weight/35.) / 33
        # Swing-timing error is a measure of a batter's standard
        # deviation from perfect swing timing (represented as 0);
        # swing timing is correlated to a player's coordination
        self.swing_timing_error = abs(normal(0, (1.5-self.coordination)/10.))
        # Swing-contact error is a measure of a batter's standard
        # deviation, both on the x- and y-axis, from perfect swing
        # contact, i.e., bat-ball contact at the bat's sweet spot;
        # it is generated as a correlate to swing timing error
        self.swing_contact_error = abs(normal(self.swing_timing_error, 0.03))
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
            (self.coordination * 0.5) + self.reflexes + (self.ball_tracking_ability * 1.5)
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
            (self.coordination * 1.25) + self.reflexes + (self.ball_tracking_ability * 1.5)
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
            self.coordination + (self.cleverness * 0.75)
        )
        diff_from_avg = primitive_pitch_framing_ability - 1.18
        diff_from_avg /= 1.5
        if diff_from_avg < -0.2:
            diff_from_avg = normal(-0.2, 0.03)
        if diff_from_avg >= 0:
            self.pitch_framing = abs(normal(0, diff_from_avg))
        else:
            self.pitch_framing = -abs(normal(0, diff_from_avg))


    # def init_tendencies(self):
    #     hitter_type = random.choice(["Slap", "Contact", "Power"])
    #     if hitter_type == "Slap":
    #         self.batting_power_tendency = 0

    def init_umpire_attributes(self):
        """Initialize umpire attributes for a person.

        These biases are enacted cumulatively, in call_pitch()>

        Primary source: http://www.sloansportsconference.com/wp-content/
        uploads/2014/02/2014_SSAC_What-Does-it-Take-to-Call-a-Strike.pdf
        """

        # Pitch call consistency represents how consistent an
        # umpire will be in attributing a certain call to a specific
        # pitch location over multiple pitches; we represent this as
        # a standard deviation in number of ball widths (the same units
        # with which we represent the strike zone)
        self.pitch_call_consistency = normal(0, 0.15)
        # Pitch edge biases represent the umpire's mean deviation
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

    def init_strike_zone(self):
        height_in_baseballs = self.height/3.
        height_at_hollow_of_knee = height_in_baseballs * 0.25
        height_at_torso_midpoint = height_in_baseballs * 0.6
        height_of_strike_zone = height_at_torso_midpoint-height_at_hollow_of_knee
        return -height_of_strike_zone/2, height_of_strike_zone/2

    def __str__(self):

        rep = self.name + ' (' + self.hometown.name + ')'
        return rep

    def age_v(self):

        self.age += 1

        d = self.prime - self.age

        self.power += int(round(normal(d, 1)))
        self.contact += int(round(normal(d, 1)))

        self.speed += int(round(normal(d, 1)))
        self.control += int(round(normal(d, 1)))
        # self.changeup += int(round(normal(d, 1)))
        # self.curveball += int(round(normal(d, 1)))

    def get_in_position(self):
        """Get into defensive position prior to a pitch."""
        if self.position == "P":
            self.location = [0, 60.5]
        elif self.position == "C":
            self.location = [0, -2]
        elif self.position == "1B":
            self.location = [69, 79]
        elif self.position == "2B":
            self.location = [32, 132]
        elif self.position == "SS":
            self.location = [-32, 132]
        elif self.position == "3B":
            self.location = [-65, 75]
        elif self.position == "RF":
            self.location = [30, 180]
        elif self.position == "CF":
            self.location = [2, 225]
        elif self.position == "LF":
            self.location = [-30, 180]

    def decide_pitch(self, batter, count):

        # Here, I'll want to add in sidespin and downspin, which
        # will determine how a ball curves and breaks, respectively

        if count == 00 or count == 10:
            # Count is 0-0 or 1-0
            if random.random() < 0.35:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 01:
            if random.random() < 0.15:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 20:
            if random.random() < 0.4:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 11:
            if random.random() < 0.2:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 02:
            if random.random() < 0.1:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 30:
            if random.random() < 0.6:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 21:
            if random.random() < 0.28:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 12:
            if random.random() < 0.11:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 31:
            if random.random() < 0.31:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 22:
            if random.random() < 0.15:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y
        if count == 32:
            if random.random() < 0.17:
                # Throw strike -- simple fastball down the middle for now
                x, y = 0, 0
                return "fastball", x, y
            else:
                # Throw ball -- high and outside for now
                x, y = 5, 4
                return "fastball", x, y

    def pitch(self, batter, catcher, at_bat, x, y, kind, drop=None, curve=None):

        # TODO remove kind, add speed, break, curve -- then reason
        # over that to determine the kind; with increased speed comes
        # increased x and y error

        count = at_bat.count
        # Determine pitch speed and behavior
        kind = "fastball"
        speed = normal(self.pitch_speed_mean, self.pitch_speed_sd)
        # Determine where it will intersect the vertical plane at home plate
        actual_x = normal(x, self.pitch_control)
        actual_y = normal(y, self.pitch_control)
        if self.righty:
            handedness = "R"
        else:
            handedness = "L"
        if batter.righty:
            batter_handedness = "R"
        else:
            batter_handedness = "L"
        pitch = Pitch(ball=Ball(), at_bat=at_bat, pitcher=self, batter=batter,
                      catcher=catcher, handedness=handedness,
                      batter_handedness=batter_handedness, count=count, kind=kind,
                      speed=speed, intended_x=x, intended_y=y, actual_x=actual_x,
                      actual_y=actual_y)
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
                    return True
                else:
                    return False
            if pitch.count == 10:
                if random.random() < 0.41:
                    return True
                else:
                    return False
            if pitch.count == 01:
                if random.random() < 0.68:
                    return True
                else:
                    return False
            if pitch.count == 20:
                if random.random() < 0.4:
                    return True
                else:
                    return False
            if pitch.count == 11:
                if random.random() < 0.63:
                    return True
                else:
                    return False
            if pitch.count == 02:
                if random.random() < 0.995:
                    return True
                else:
                    return False
            if pitch.count == 30:
                if random.random() < 0.03:
                    return True
                else:
                    return False
            if pitch.count == 21:
                if random.random() < 0.65:
                    return True
                else:
                    return False
            if pitch.count == 12:
                if random.random() < 0.995:
                    return True
                else:
                    return False
            if pitch.count == 31:
                if random.random() < 0.3:
                    return True
                else:
                    return False
            if pitch.count == 22:
                if random.random() < 0.995:
                    return True
                else:
                    return False
            if pitch.count == 32:
                if random.random() < 0.995:
                    return True
                else:
                    return False
        elif pitch.batter_hypothesis == "Ball":
            if pitch.count == 00:
                # Count before this pitch is 0-0
                if random.random() < 0.01:
                    return True
                else:
                    return False
            if pitch.count == 10:
                if random.random() < 0.03:
                    return True
                else:
                    return False
            if pitch.count == 01:
                if random.random() < 0.15:
                    return True
                else:
                    return False
            if pitch.count == 20:
                if random.random() < 0.02:
                    return True
                else:
                    return False
            if pitch.count == 11:
                if random.random() < 0.15:
                    return True
                else:
                    return False
            if pitch.count == 02:
                if random.random() < 0.46:
                    return True
                else:
                    return False
            if pitch.count == 30:
                if random.random() < 0.01:
                    return True
                else:
                    return False
            if pitch.count == 21:
                if random.random() < 0.1:
                    return True
                else:
                    return False
            if pitch.count == 12:
                if random.random() < 0.4:
                    return True
                else:
                    return False
            if pitch.count == 31:
                if random.random() < 0.05:
                    return True
                else:
                    return False
            if pitch.count == 22:
                if random.random() < 0.35:
                    return True
                else:
                    return False
            if pitch.count == 32:
                if random.random() < 0.3:
                    return True
                else:
                    return False

    def decide_how_to_swing(self, pitch):
        """

        """
        # Decide whether to bunt
        bunt = False
        if bunt:
            return "bunt"
        # Decide swing power -- this will be the main determinant of
        # how far the ball, if batted, will travel in the air; with
        # increasing swing power comes increasing chances to swing
        # and miss [Naively asserting medium-high power for now]
        power = normal(0.6, 0.1)
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
        upward_force = normal(15, 5)  # TODO [this is naive]
        # Decide whether to attempt to pull the ball to the opposite
        # field
        if random.random() < 0.3:
            intended_pull = True
        else:
            intended_pull = False
        return power, upward_force, intended_pull

    def bunt(self, pitch):
        pass

    def swing(self, pitch, power, upward_force, intended_pull):
        """Swing at a pitch.

        Keyword arguments:
        power -- a real number between 0 and 1 indicating how much power
                 the batter will put into the swing
        upward_force -- the angle the ball will launch off the bat, if
                        it's struck right at the sweet spot
        pull -- a boolean indicating whether the batter will attempt to
                pull the ball, if batted, toward the opposite field
        """
        # Determine swing timing -- timing generally becomes worse with
        # more powerful swings, as well as utterly powerless swings (a
        # swing with 0.2 power produces ideal timing); likewise,
        # TODO: also effect this by pitch speed (higher = harder), expected
        # pitch speed,
        timing = normal(0, self.swing_timing_error+(abs(0.2-power)/7))
        # Determine swing contact point -- this is represented
        # as an (x, y) coordinate, where (0, 0) represents contact
        # at the bat's sweet spot; contact x-coordinate is determined
        # by the batter's swing contact error and then offset by their
        # timing (these could interact such that bad timing incidentally
        # corrects bad contact); contact y-coordinate is determined by the
        # batter's swing contact error and is negatively affected as more
        # power is put into the swing
        contact_x_coord = normal(0, self.swing_contact_error) + timing
        contact_y_coord = normal(0, self.swing_contact_error + abs(0.2-power)/15)
        if self.righty:
            handedness = "R"
        elif self.lefty:
            handedness = "L"
        swing = Swing(batter=self, pitch=pitch, handedness=handedness,
                      power=power, upward_force=upward_force,
                      intended_pull=intended_pull, timing=timing,
                      contact_x_coord=contact_x_coord,
                      contact_y_coord=contact_y_coord)
        return swing

    def call_pitch(self, pitch):
        """Call a pitch that is not swung at either a strike or a ball."""
        self.pitch_call_consistency = normal(0, 0.25)

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
            normal(framed_x, self.pitch_call_consistency),
            normal(framed_y, self.pitch_call_consistency)
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

    def receive_pitch(self, pitch):
        """Receive a pitch that is not swung at."""
        distance_from_strike_zone_center = (
            abs(0-pitch.actual_x) + abs(0-pitch.actual_y)
        )
        difficulty = (distance_from_strike_zone_center**2 / 20) * 0.015
        difficulty /= self.pitch_receiving
        # It's slightly harder to cleanly receive a pitch when framing,
        # so we increase the difficulty, just barely, for this
        difficulty += self.pitch_framing/1000
        if random.random() < difficulty:
            return False
        else:
            return True

    def receive_foul_tip(self, pitch):
        """Receive a foul tip.

        TODO: Considerable possibility of injury here.
        """
        difficulty = 0.8
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

