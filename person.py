import random
import os
import math
from random import normalvariate as normal

from equipment import Bat, Baseball, Glove, Mitt
from play import Pitch, Swing, Bunt, FieldingAct, Throw
from call import PlayAtBaseCall, FlyOutCall
from outcome import FoulBall, FlyOut, HomeRun, GrandSlam, AutomaticDouble, GroundRuleDouble

FORENAMES = [name[:-1] for name in open(
    os.getcwd()+'/corpora/male_names.txt', 'r')
]


# TODO model baseball scoring, where the main intrigue will be the scorer
# having biases and inconsistency with how he decides what 'ordinary effort'
# is in potentially assigning errors -- a big consideration here is any
# statistical context of the game, e.g., the scorer will be more likely to
# call an error when a potential no-hitter is developing


class Person(object):

    def __init__(self, birthplace):
        self.father = self.mother = None
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
        self.team = None
        self.init_physical_attributes()
        self.init_personality_and_mental_attributes()
        self.init_baseball_attributes()
        self.init_umpire_biases()

        self.strike_zone = self.init_strike_zone()

        # Miscellaneous -- put here for now
        self.bat = Bat()
        self.glove = Glove()
        self.primary_position = None
        self.outfielder = self.infielder = False
        # Dynamic attributes that change during a game
        self.position = None  # Position currently at -- used during game
        self.location = None  # Exact x, y coordinates on the field
        self.percent_to_base = None  # Percentage of way to base you're running to
        self.safely_on_base = False  # Physically reached the next base, not necessarily safely
        self.safely_home = False
        self._started_retreating = False
        self.time_needed_to_field_ball = None
        self.playing_the_ball = False
        self.attempting_fly_out = False
        self.immediate_goal = None
        self.dist_per_timestep = None  # Feet per timestep in approach to immediate goal
        self.relative_rate_of_speed = None
        self._slope = None
        self.at_goal = None
        self._straight_ahead_x = None
        self._straight_ahead_y = None
        self._moving_left = False
        self._moving_right = False
        # Prepare statistical lists
        # --
        self.games_played = []
        # -- Pitching
        self.innings_pitched = []
        self.pitches = []
        self.strikes = []
        self.balls = []
        self.beans = []
        self.pitching_strikeouts = []
        self.pitching_walks = []
        self.hits_allowed = []
        self.home_runs_allowed = []
        self.grand_slams_allowed = []
        # -- Batting
        self.batting_strikeouts = []
        self.batting_walks = []
        self.plate_appearances = []
        self.at_bats = []
        self.hits = []
        self.singles = []
        self.doubles = []
        self.triples = []
        self.home_runs = []
        self.grand_slams = []
        self.rbi = []
        self.runs = []
        self.outs = []  # Instances where a player was called out
        self.double_plays_grounded_into = []
        self.left_on_base = 0
        self.stolen_bases = []
        # -- Fielding
        self.putouts = []
        self.assists = []
        self.double_plays_participated_in = []
        self.triple_plays_participated_in = []
        # -- Umpiring
        self.games_umpired = []
        self.play_at_base_calls = []
        self.fly_out_calls = []
        # Prepare extra-statistical lists
        self.throws = []
        self.fielding_acts = []

    def init_physical_attributes(self):
        self.height = int(normal(71, 2))  # TODO
        # Determine weight, which is correlated with height
        self.weight = int(normal(self.height*2.45, self.height*0.2))
        # Determine body mass index (BMI)
        self.bmi = float(self.weight)/self.height**2 * 703
        # Determine coordination, which is correlated to BMI
        if self.bmi > 24:
            primitive_coordination = (21-(self.bmi-21))/23.
        else:
            primitive_coordination = 1.0
        self.coordination = normal(primitive_coordination, 0.1)
        # Determine reflexes, which is correlated to coordination
        self.reflexes = normal(self.coordination, self.coordination/10)
        # Determine agility, which is correlated to coordination and
        # height (with 5'6 somewhat arbitrarily being the ideal height
        # for agility)
        primitive_agility = (
            self.coordination - abs((self.height-66)/66.)
        )
        self.agility = normal(primitive_agility, 0.1)
        # Determine jumping ability, which is correlated to coordination and
        # height (with 6'6 somewhat arbitrarily being the ideal height
        # for jumping)
        primitive_jumping = (
            self.coordination - abs((self.height-78)/78.)
        )
        if primitive_jumping < 0.3:
            primitive_jumping = 0.3
        self.vertical = normal(primitive_jumping**1.5 * 22, 3)
        if self.vertical < 2:
            self.vertical = 2 + random.random()*2
        # Determine the maximum height of fieldable batted balls for the player,
        # which is determined by sum of the player's vertical and vertical reach
        # (the latter being how high they can reach while standing on the ground)
        self.vertical_reach = (self.height * 1.275) / 12.0
        self.fieldable_ball_max_height = (
            self.vertical_reach + (self.vertical / 12.0)
        )
        # Determine footspeed, which is correlated to coordination and
        # height (with 6'1 somewhat arbitrarily being the ideal height
        # for footspeed) -- we do this by generating a 60-yard dash time
        # and then dividing that by its 180 feet to get a full-speed
        # second-per-foot time
        primitive_footspeed = (
            (1.5 * self.coordination) - abs((self.height-73)/73.)
        )
        diff_from_avg = primitive_footspeed - 1.21
        if diff_from_avg >= 0:
            diff_from_avg /= 2.3
            self.full_speed_sec_per_foot = (7.3 - abs(normal(0, diff_from_avg))) / 180
        else:
            diff_from_avg /= 1.8
            self.full_speed_sec_per_foot = (7.3 + abs(normal(0, abs(diff_from_avg)))) / 180
        # Determine baserunning speed,
        # [TODO penalize long follow-through and lefties on speed to first]
        self.speed_home_to_first = (
            (self.full_speed_sec_per_foot*180) / (1.62 + normal(0, 0.01))
        )
        self.speed_rounding_a_base = None
        7.2 - abs(normal(0, 0.17*2))
        if random.random() < 0.1:
            self.lefty = True
            self.righty = False
        else:
            self.lefty = False
            self.righty = True
        self.prime = int(round(normal(29, 1)))

    def init_personality_and_mental_attributes(self):
        """Initialize values for each of the Big Five personality traits and other mental traits."""
        #       --    INHERENT ATTRIBUTES     --
        # Initialize values for Big 5 personality traits
        if self.father:
            # Openness to experience (studies indicate 57% heritability)
            takes_after = random.choice([self.father, self.mother])
            self.openness_to_experience = normal(takes_after.openness_to_experience, 0.15)
            if self.openness_to_experience > 1:
                self.openness_to_experience = 1.0
            elif self.openness_to_experience < -1:
                self.openness_to_experience = -1.0
            # Conscientiousness (studies indicate 54% heritability)
            takes_after = random.choice([self.father, self.mother])
            self.conscientiousness = normal(takes_after.conscientiousness, 0.13)
            if self.conscientiousness > 1:
                self.conscientiousness = 1.0
            elif self.conscientiousness < -1:
                self.conscientiousness = -1.0
            # Extroversion (studies indicate 49% heritability)
            takes_after = random.choice([self.father, self.mother])
            self.extroversion = normal(takes_after.extroversion, 0.11)
            if self.extroversion > 1:
                self.extroversion = 1.0
            elif self.extroversion < -1:
                self.extroversion = -1.0
            # Agreeableness (studies indicate 48% heritability)
            takes_after = random.choice([self.father, self.mother])
            self.agreeableness = normal(takes_after.agreeableness, 0.11)
            if self.agreeableness > 1:
                self.agreeableness = 1.0
            elif self.agreeableness < -1:
                self.extroversion = -1.0
            # Neuroticism (studies indicate 42% heritability)
            takes_after = random.choice([self.father, self.mother])
            self.neuroticism = normal(takes_after.neuroticism, 0.09)
            if self.neuroticism > 1:
                self.neuroticism = 1.0
            elif self.neuroticism < -1:
                self.neuroticism = -1.0
        elif not self.father:
            # Openness to experience (study indicates mean of ~3.75 -- 0.375 on my scale)
            self.openness_to_experience = normal(0.375, 0.35)
            if self.openness_to_experience > 1:
                self.openness_to_experience = 1.0
            elif self.openness_to_experience < -1:
                self.openness_to_experience = -1.0
            # Conscientiousness (study indicates mean of ~3.5 -- 0.25 on my scale)
            self.conscientiousness = normal(0.25, 0.35)
            if self.conscientiousness > 1:
                self.conscientiousness = 1.0
            elif self.conscientiousness < -1:
                self.conscientiousness = -1.0
            # Extroversion (study indicates mean of ~3.3 -- 0.15 on my scale)
            self.extroversion = normal(0.15, 0.35)
            if self.extroversion > 1:
                self.extroversion = 1.0
            elif self.extroversion < -1:
                self.extroversion = -1.0
            # Agreeableness (study indicates mean of ~3.7 -- 0.35 on my scale)
            self.agreeableness = normal(0.35, 0.35)
            if self.agreeableness > 1:
                self.agreeableness = 1.0
            elif self.agreeableness < -1:
                self.extroversion = -1.0
            # Neuroticism (study indicates mean of ~3.0 -- 0.0 on my scale)
            self.neuroticism = normal(0.0, 0.35)
            if self.neuroticism > 1:
                self.neuroticism = 1.0
            elif self.neuroticism < -1:
                self.neuroticism = -1.0
        # -- Confidence (high values have the signal E+, N-); follows a normal distribution
        # around 0.8, where 1.0 represents ideal confidence (in the sense of accurately judging
        # one's own abilities), while lower and higher values represent under- and overconfidence,
        # respectively; affects estimating whether you can beat a throw on the base paths,
        base_confidence = self.extroversion + -self.neuroticism
        self.confidence = 0.78 + base_confidence/0.49158017656787317/10
        # -- Audacity (high values have the signal E+, O+); follows a normal distribution
        # around 0.8, where there is no ideal audacity, just that lower values will make the
        # player less likely to take risks (which may or may have paid off) and higher values will
        # make the player more likely to take risks; affects deciding whether to challenge a close
        # throw on the base paths,
        base_audacity = self.extroversion + self.openness_to_experience
        self.audacity = 0.7 + base_audacity/0.487468441582416/10
        # -- Cleverness (high values have the signal O+, N-); follows a normal distribution
        # around 1.0 -- average people have average cleverness, and the higher cleverness the better;
        # affects typical composure
        base_cleverness = self.openness_to_experience + -self.neuroticism
        self.cleverness = 0.93 + base_cleverness/0.48588506450686808/10
        # -- Focus (high values have the signal N-, C+); follows a normal distribution
        # around 1.0 -- average people have average focus, and the higher focus the better;
        # affects ball-tracking ability, fly-ball fielding ability, ground-ball fielding
        # ability, throwing accuracy,
        base_focus = -self.neuroticism + self.conscientiousness
        self.focus = 0.95 + base_focus/0.49030688680600359/10
        # -- Baseball tracking ability is correlated to a player's focus rating
        # and affects a player's ability to anticipate the trajectories of
        # balls in movement -- most saliently, it affects the speed with
        # which a fielder can move in getting in position to field a fly ball
        # while still properly tracking that ball; values approaching 1.5
        # represent once-in-a-generation talents that would be capable of
        # something like Willie Mays' catch.
        self.ball_tracking_ability = (self.focus * 0.6666666666666666) * 1.5
        #       --    DYNAMIC ATTRIBUTES     --
        # These take inherent attributes as primitives, but can change over time, either
        # rapidly or gradually
        # -- Composure; this is a dynamic confidence measure that can change over the course
        # of a game or more gradually over longer stretches of time; it works as a feedback
        # loop on player performance; affects fielding, swing timing; is increased by impressive
        # acts, good plate-appearance outcomes; is decreased by fielding bloopers, bad
        # plate-appearance outcomes
        self.composure = (self.confidence + self.focus) / 2
        if self.composure > 1:
            self.composure = 1.0

    def init_intangibles(self):
        self.hustle = 1.0

    def init_baseball_attributes(self):

        #       -- Fundamental attributes --

        # Every fielding chance has a specified difficulty, which
        # approximately represents the percentage likelihood that an
        # average player would successfully field the ball given the
        # circumstances at hand -- a player's fielding rating specifies
        # how increased their likelihood of successfully fielding a
        # batted ball is above the average player (ratings near 1.3-1.5
        # represent once-a-generation talents); first, we start with
        # fly-ball fielding ability (which subsumes line drives and
        # pop-ups)
        primitive_fly_ball_fielding_ability = (
            self.coordination + self.agility*0.5 +
            self.ball_tracking_ability + self.focus
        )
        diff_from_avg = primitive_fly_ball_fielding_ability - 3.342
        diff_from_avg /= 6.8
        if diff_from_avg >= 0:
            percentage_above_avg = abs(normal(0, diff_from_avg))
            self.fly_ball_fielding = 1 + percentage_above_avg
        else:
            percentage_below_avg = abs(normal(0, abs(diff_from_avg)))
            self.fly_ball_fielding = 1 - percentage_below_avg
        # Ground-ball fielding ability
        primitive_ground_ball_fielding_ability = (
            self.coordination*0.5 + self.agility*1.5 +
            self.ball_tracking_ability*0.25 + self.focus*0.75
        )
        diff_from_avg = primitive_ground_ball_fielding_ability - 2.756
        diff_from_avg /= 6.8
        if diff_from_avg >= 0:
            percentage_above_avg = abs(normal(0, diff_from_avg))
            self.ground_ball_fielding = 1 + percentage_above_avg
        else:
            percentage_below_avg = abs(normal(0, abs(diff_from_avg)))
            self.ground_ball_fielding = 1 - percentage_below_avg
        # Throwing velocity
        primitive_throwing_velocity = (
            self.coordination + (100-self.height)/100.
        )
        if primitive_throwing_velocity < 0.52:
            primitive_throwing_velocity = 0.52
        elif primitive_throwing_velocity > 0.72:
            primitive_throwing_velocity = 0.72
        self.throwing_velocity_mph = (
            normal(primitive_throwing_velocity, primitive_throwing_velocity/10.) * 100
        )
        self.throwing_velocity = self.throwing_velocity_mph * 1.46667  # Ft/s is more convenient
        self.throwing_dist_per_timestep = self.throwing_velocity * 0.1
        # Throwing release time
        primitive_throwing_release_time = self.coordination * 0.0964
        diff_from_avg = primitive_throwing_release_time - 0.08
        if diff_from_avg >= 0:
            diff_from_avg /= 6
            self.throwing_release_time = 0.08 - abs(normal(0.0, diff_from_avg))
        elif diff_from_avg < 0:
            diff_from_avg /= 4.5
            self.throwing_release_time = 0.08 + abs(normal(0.0, diff_from_avg))
        # Regular throwing accuracy (accuracy on normal release) --
        # modeled as the typical error, in feet on both the x- and
        # y-axes, per foot of throwing distance
        primitive_throwing_accuracy = self.coordination + self.focus
        diff_from_avg = primitive_throwing_accuracy - 1.91
        self.throwing_error_per_foot = (
            abs(normal(1.5-diff_from_avg, 0.5))/30
        )
        if self.throwing_error_per_foot < 0.008:
            # Enforce that the best throwing accuracy can be about
            # one foot of error for every 130 feet
            self.throwing_error_per_foot = 0.008 - random.random()*0.001
        # Sidearm throwing accuracy -- by default is quite worse, since
        # this requires a lot of practice
        self.sidearm_throwing_error_per_foot = (
            normal(self.throwing_error_per_foot*2, self.throwing_error_per_foot/10.)
        )

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

    def init_umpire_biases(self):
        """Initialize umpire biases for a person.

        These biases are enacted cumulatively, in call_pitch().

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

    def get_in_position(self, at_bat):
        """Get into position prior to a pitch."""
        if self.composure < 0.5:
            self.composure = 0.5
        elif self.composure > 1.5:
            self.composure = 1.5
        # Offensive players
        if self is at_bat.batter:
            self.location = [0, 0]
            self.forced_to_advance = True
            self.percent_to_base = 0.0
        elif self is at_bat.frame.on_first:
            self.location = [63.5, 63.5]
            self.forced_to_advance = True
            # Lead off about 10 feet
            self.percent_to_base = normal(0.08, 0.1)
        elif self is at_bat.frame.on_second:
            self.location = [0, 127]
            if at_bat.frame.on_first:
                self.forced_to_advance = True
            # Lead off about 15 feet
            self.percent_to_base = normal(0.11, 0.1)
        elif self is at_bat.frame.on_third:
            self.location = [-63.5, 63.5]
            if at_bat.frame.on_first and at_bat.frame.on_second:
                self.forced_to_advance = True
            # Lead off about 10 feet
            self.percent_to_base = normal(0.08, 0.1)
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
        self.attempting_fly_out = False
        self.immediate_goal = None
        self.dist_per_timestep = None
        self.playing_the_ball = False
        self.called_off = False
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
        self._done_tentatively_advancing = False
        self._decided_finish = False
        self.will_round_base = False
        self.believes_he_can_beat_throw = False
        self.taking_next_base = False
        self._started_retreating = False
        self.safely_on_base = False
        self.base_reached_on_hit = None
        self.timestep_reached_base = None
        self.forced_to_retreat = False
        self.advancing_due_to_error = False
        self.throwing_to_first = False
        self.throwing_to_second = False
        self.throwing_to_third = False
        self.throwing_to_home = False
        self.throwing_back_to_pitcher = False
        self.making_goal_revision = False

    def decide_pitch(self, at_bat):

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
        if self._swing_power > 1.0:
            self._swing_power = 1.0
        if self.position == "RF" or self.position == "1B":
            self._swing_power = 1.0  # That's where the power hitters are put in my testing right now
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
        # swing with 0.2 power produces ideal timing); likewise,
        # TODO: also effect this by pitch speed (higher = harder), expected
        # pitch speed,
        timing = (
            normal(0, self.swing_timing_error+(abs(0.2-self._swing_power)/7))
        )
        timing /= self.composure
        # Determine swing contact point -- this is represented
        # as an (x, y) coordinate, where (0, 0) represents contact
        # at the bat's sweet spot; contact x-coordinate is determined
        # by the batter's swing contact error and then offset by their
        # timing (these could interact such that bad timing incidentally
        # corrects bad contact); contact y-coordinate is determined by the
        # batter's swing contact error and is negatively affected as more
        # power is put into the swing
        contact_x_coord = normal(0, self.swing_contact_error) + timing
        contact_y_coord = (
            normal(0, self.swing_contact_error + abs(0.2-self._swing_power)/15)
        )
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

    def call_pitch(self, pitch):
        """Call a pitch that is not swung at either a strike or a ball."""
        self.pitch_call_inconsistency = normal(0, 0.25)

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

    def call_play_at_base(self, baserunner, throw):
        """Call a baserunner either safe or out."""
        # This is some housekeeping that can probably be deleted if the specified errors never pop up
        batted_ball = throw.batted_ball
        if throw.base == "1B":
            assert baserunner is batted_ball.running_to_first or baserunner is batted_ball.retreating_to_first, "" \
                "Umpire was tasked with calling out {} at first, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif throw.base == "2B":
            assert baserunner is batted_ball.running_to_second or baserunner is batted_ball.retreating_to_second, "" \
                "Umpire was tasked with calling out {} at second, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif throw.base == "3B":
            assert baserunner is batted_ball.running_to_third or baserunner is batted_ball.retreating_to_third, "" \
                "Umpire was tasked with calling out {} at third, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        elif throw.base == "H":
            assert baserunner is batted_ball.running_to_home or baserunner.safely_on_base, "" \
                "Umpire was tasked with calling out {} at home, but that runner " \
                "is not attempting to take that base.".format(baserunner.last_name)
        # If the baserunner hasn't reached base yet, we need to calculate at what timestep
        # they *will/would have* reached base
        if not baserunner.timestep_reached_base:
            dist_from_baserunner_to_base = 90 - (baserunner.percent_to_base*90)
            time_until_baserunner_reaches_base = dist_from_baserunner_to_base * baserunner.full_speed_sec_per_foot
            baserunner.timestep_reached_base = (
                throw.batted_ball.time_since_contact + time_until_baserunner_reaches_base
            )
        # Get the difference in time between the baserunner reaching base
        # and the throw reached the first baseman's glove -- this will be
        # negative if the runner beat the throw
        baserunner_diff_from_throw = true_difference = (
            baserunner.timestep_reached_base - throw.timestep_reached_target
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
        # is to a prior-entry bias, explained in init_umpire_biases()
        if throw.base == "1B":
            baserunner_diff_from_throw += self.play_at_first_prior_entry_bias
        # Finally, *to simulate umpire inconsistency*, further pollute the
        # difference by regenerating it from a normal distribution around
        # itself with the umpire's inconsistency standard error as the
        # standard deviation
        baserunner_diff_from_throw = (
            normal(baserunner_diff_from_throw, self.play_at_base_inconsistency)
        )
        if baserunner_diff_from_throw <= 0:
            PlayAtBaseCall(umpire=self, call="Safe", true_call=true_call, true_difference=true_difference,
                           baserunner=baserunner, throw=throw)
        else:
            PlayAtBaseCall(umpire=self, call="Out", true_call=true_call, true_difference=true_difference,
                           baserunner=baserunner, throw=throw)

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
        elif not batted_ball.in_foul_territory:
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

    def officiate(self, batted_ball):
        """Officiate as necessary, including making (pseudo) dead-ball determination."""
        # TODO umpire biases
        if batted_ball.ground_rule_incurred:
            GroundRuleDouble(batted_ball=batted_ball)
            batted_ball.resolved = True
        elif batted_ball.fielded_by and not batted_ball.fly_out_awarded:
            # If a fly out was potentially made, make the call as to whether it was
            # indeed a fly out or else a trap; don't even bother if the ball has
            # clearly bounced one or more times too many
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
                batted_ball.resolved = True
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
                        batted_ball.resolved = True
                    else:
                        AutomaticDouble(batted_ball=batted_ball)
                        batted_ball.resolved = True
                elif not batted_ball.n_bounces and batted_ball.at_bat.game.rules.home_run_must_land_fair:
                    # A ball that crosses the plane of the outfield fence in flight
                    # will be either a foul ball or home run, depending on whether
                    # this rule is in effect -- if it is, the ball must also land fair
                    # to be a home run
                    if batted_ball.landed:
                        if batted_ball.in_foul_territory:
                            FoulBall(batted_ball=batted_ball, anachronic_home_run=True)
                            batted_ball.resolved = True
                        elif not batted_ball.in_foul_territory:
                            # Batted ball crosses plane of the outfield fence fair
                            # and lands fair -- a home run in any era
                            if batted_ball.at_bat.frame.bases_loaded:
                                GrandSlam(batted_ball=batted_ball)
                            else:
                                HomeRun(batted_ball=batted_ball)
                            batted_ball.resolved = True
                else:
                    # Batted ball crossed the plane of the outfield fence, which is
                    # good enough for a home run if the above rule is not in effect
                    if batted_ball.at_bat.frame.bases_loaded:
                        GrandSlam(batted_ball=batted_ball)
                    else:
                        HomeRun(batted_ball=batted_ball)
                    batted_ball.resolved = True
        elif batted_ball.landed_foul:
            # Generally, a batted ball that lands foul incur a foul ball -- the exception
            # is if the rule allowing a bounding foul to be caught for a FlyOut is in effect;
            # in that case, we don't score the foul ball until a timestep after the batted ball's
            # second bounce -- this allows a fielder to potentially make the catch (if the ball
            # doesn't have a second bounce in its trajectory, we just score the foul right away)
            if not batted_ball.at_bat.game.rules.foul_ball_on_first_bounce_is_out:
                FoulBall(batted_ball=batted_ball)
                batted_ball.resolved = True
            else:
                if (not batted_ball.second_landing_timestep or
                        batted_ball.time_since_contact > batted_ball.second_landing_timestep+0.1):
                    FoulBall(batted_ball=batted_ball)
                    batted_ball.resolved = True
        elif batted_ball.landed and batted_ball.in_foul_territory:
            if batted_ball.passed_first_or_third_base or batted_ball.stopped or batted_ball.touched_by_fielder:
                FoulBall(batted_ball=batted_ball)
                batted_ball.resolved = True
        # Determine whether the current playing action has ended
        if batted_ball.at_bat.frame.outs == 3:
            print "-- Since there are three outs, the playing action is over [{}]".format(
                batted_ball.time_since_contact
            )
            batted_ball.resolved = True
        # elif all(b.safely_on_base or b.out for b in batted_ball.at_bat.frame.baserunners + [batted_ball.at_bat.batter]):
        #     if batted_ball.landed and (not batted_ball.at_bat.throw or batted_ball.at_bat.throw.reached_target):
        #         print "-- Since all baserunners are either out or safe, the playing action is over [{}]".format(
        #             batted_ball.time_since_contact
        #         )
        #         batted_ball.resolved = True

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

    def decide_immediate_goal(self, batted_ball):
        """Decide immediate goal other than playing the ball.

        This method is called by batted_ball.get_obligated_fielder()
        """
        if self.making_goal_revision:
            self._moving_left = self._moving_right = self._straight_ahead_x = self._straight_ahead_y = False
            self.at_goal = False
            self._slope = None
            self.making_goal_revision = False
        if self is batted_ball.obligated_fielder and not self.called_off:
            self.playing_the_ball = True
        else:
            if self.position == "1B":
                # Cover first base
                self.immediate_goal = [63.5, 63.5]
                # Get there ASAP, i.e., act at full speed
                self.dist_per_timestep = (
                    0.1/self.full_speed_sec_per_foot
                )
                batted_ball.covering_first = self
            elif self.position == "2B":
                # If ball is hit to the left of second base, cover second;
                # else, if the ball is hit to the right of second, cover first
                if batted_ball.horizontal_launch_angle <= 0:
                    # Cover second base
                    self.immediate_goal = [0, 127]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.full_speed_sec_per_foot
                    )
                    batted_ball.covering_second = self
                else:
                    # Cover first base
                    self.immediate_goal = [63.5, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.full_speed_sec_per_foot
                    )
                    batted_ball.covering_first = self
            elif self.position == "SS":
                # If ball is hit to the left of second base, cover third;
                # else, if the ball is hit to the right of second, cover second
                if batted_ball.horizontal_launch_angle <= 0:
                    # Cover third base
                    self.immediate_goal = [-63.5, 63.5]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.full_speed_sec_per_foot
                    )
                    batted_ball.covering_third = self
                else:
                    # Cover second base
                    self.immediate_goal = [0, 127]
                    # Get there ASAP, i.e., act at full speed
                    self.dist_per_timestep = (
                        0.1/self.full_speed_sec_per_foot
                    )
                    batted_ball.covering_second = self
            elif self.position == "3B":
                # Cover first base
                self.immediate_goal = [-63.5, 63.5]
                # Get there ASAP, i.e., act at full speed
                self.dist_per_timestep = (
                    0.1/self.full_speed_sec_per_foot
                )
                batted_ball.covering_third = self
            elif self.position == "LF":
                if -46 <= batted_ball.true_landing_point[0] <= 0:
                    # SS ([-32, 132]) may be closer
                    if (batted_ball.horizontal_launch_angle <= 0 and not self.called_off and
                            batted_ball.true_landing_point[1] > 150):
                        # Play the ball by keeping the immediate goal that
                        # you set when you read it (in batted_ball.get_read_by_fielders())
                        self.playing_the_ball = True
                    else:
                        # Just stay put -- TODO
                        self.immediate_goal = self.location
                elif batted_ball.true_landing_point[0] < -46:
                    # 3B ([-60, 80]) may be closer
                    if (batted_ball.horizontal_launch_angle <= 0 and not self.called_off and
                            batted_ball.true_landing_point[1] > 95):
                        # Play the ball by keeping the immediate goal that
                        # you set when you read it (in batted_ball.get_read_by_fielders())
                        self.playing_the_ball = True
                    else:
                        # Just stay put -- TODO
                        self.immediate_goal = self.location
                else:
                    self.immediate_goal = self.location  # Precautionary else block
            elif self.position == "RF":
                if 0 <= batted_ball.true_landing_point[0] <= 51:
                    # 2B ([32, 135]) may be closer
                    if (batted_ball.horizontal_launch_angle > 0 and not self.called_off and
                            batted_ball.true_landing_point[1] > 150):
                        # Play the ball by keeping the immediate goal that
                        # you set when you read it (in batted_ball.get_read_by_fielders())
                        self.playing_the_ball = True
                    else:
                        # Just stay put -- TODO
                        self.immediate_goal = self.location
                elif batted_ball.true_landing_point[0] < -46:
                    # 1B ([69, 79]) may be closer
                    if (batted_ball.horizontal_launch_angle > 0 and not self.called_off and
                            batted_ball.true_landing_point[1] > 95):
                        # Play the ball by keeping the immediate goal that
                        # you set when you read it (in batted_ball.get_read_by_fielders())
                        self.playing_the_ball = True
                    else:
                        # Just stay put -- TODO
                        self.immediate_goal = self.location
                else:
                    self.immediate_goal = self.location  # Precautionary else block
            elif self.position == "C":
                # Stay put and cover home
                self.immediate_goal = self.location
                batted_ball.covering_home = self
            elif self.position == "P":
                if self.team.catcher is batted_ball.obligated_fielder:
                    # Cover home (obviously should be backing up bases and stuff too TODO)
                    self.immediate_goal = [0, 0]
                    batted_ball.covering_home = self
                else:
                    # Just stay put
                    self.immediate_goal = self.location
            else:
                # Just stay put -- TODO
                self.immediate_goal = self.location
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
        if self.playing_the_ball and batted_ball.time_since_contact > 1+random.random():
            other_fielders_playing_the_ball = (
                f for f in batted_ball.at_bat.fielders if f.playing_the_ball and f is not self
            )
            if other_fielders_playing_the_ball:
                for teammate in other_fielders_playing_the_ball:
                    if (batted_ball.fielding_priorities[self.position] >=
                            batted_ball.fielding_priorities[teammate.position]):
                        # Call off the teammate
                        teammate.called_off = True
                        teammate.playing_the_ball = False
                        print "-- {} ({}) called off {} ({}) [{}]".format(
                            self.last_name, self.position, teammate.last_name, teammate.position,
                            batted_ball.time_since_contact
                        )
        # If you just got called off, revise your immediate goal
        if self.called_off:
            self.making_goal_revision = True
            self.decide_immediate_goal(batted_ball=batted_ball)
            self.called_off = False
        # Move toward your goal
        dist = self.dist_per_timestep
        x, y = self.location
        if self.at_goal:
            new_x, new_y = x, y
        elif self._moving_left:
            new_x = x + (-1*dist)/(math.sqrt(1+self._slope**2))
            new_y = y + (-1*self._slope*dist)/(math.sqrt(1+self._slope**2))
        elif self._moving_right:
            new_x = x + dist/(math.sqrt(1+self._slope**2))
            new_y = y + (self._slope*dist)/(math.sqrt(1+self._slope**2))
        elif self._straight_ahead_x:
            new_x = x + dist
            new_y = y
        elif self._straight_ahead_y:
            new_x = x
            new_y = y + dist
        else:
            raise Exception(self.position + " tried to move about the field without" +
                            "proper bearing assigned.")
        self.location = new_x, new_y
        if (math.hypot(self.immediate_goal[0]-new_x,
                       self.immediate_goal[1]-new_y) <= self.dist_per_timestep):
            self.at_goal = True
            if self.playing_the_ball and not batted_ball.fielded_by:
                batted_ball.fielder_with_chance = self

    def baserun(self, batted_ball, debug=False):
        """Run along the base paths, as appropriate."""
        # Advance along the base path
        if self is batted_ball.running_to_first:
            # Baserunner percentage to base is calculated differently for
            # batter-runners heading to first to account for running delay from
            # the duration of the follow-through, discarding of the bat, etc.
            self.percent_to_base = (
                batted_ball.time_since_contact/self.speed_home_to_first
            )
        else:
            self.percent_to_base += (0.1/self.full_speed_sec_per_foot) / 90
        if debug:
            if self is batted_ball.running_to_home:
                print "{} is {}% to home".format(self.last_name, int(round(self.percent_to_base*100)))
            elif self is batted_ball.running_to_third:
                print "{} is {}% to third".format(self.last_name, int(round(self.percent_to_base*100)))
            elif self is batted_ball.running_to_second:
                print "{} is {}% to second".format(self.last_name, int(round(self.percent_to_base*100)))
            elif self is batted_ball.running_to_first:
                print "{} is {}% to first".format(self.last_name, int(round(self.percent_to_base*100)))
        # If you've safely reached base, either stay there and make it known that
        # you've reached the base safely, or round it and decide whether to actually
        # advance to the next base
        if self.percent_to_base >= 1.0:
            # If batter-runner, make a note that he *did* reach this base safely, regardless of whether they
            # end up out on the throw, for later purposes of scoring the hit
            if not self.advancing_due_to_error:
                if self is batted_ball.running_to_first or self is batted_ball.retreating_to_first:
                    self.base_reached_on_hit = "1B"
                elif self is batted_ball.running_to_second or self is batted_ball.retreating_to_second:
                    self.base_reached_on_hit = "2B"
                elif self is batted_ball.running_to_third or self is batted_ball.retreating_to_third:
                    self.base_reached_on_hit = "3B"
                elif self is batted_ball.running_to_home:
                    self.base_reached_on_hit = "H"
            if not self.will_round_base and not self.safely_on_base:
                print "-- {} has safely reached base [{}]".format(self.last_name, batted_ball.time_since_contact)
                self.safely_on_base = True
                # Record the precise time the runner reached base, for potential use by umpire.call_play_at_base()
                if not self.timestep_reached_base:
                    surplus_percentage_to_base = self.percent_to_base-1
                    surplus_distance = surplus_percentage_to_base*90
                    surplus_time = surplus_distance * self.full_speed_sec_per_foot
                    self.timestep_reached_base = batted_ball.time_since_contact - surplus_time
                self.percent_to_base = 1.0
                if batted_ball.running_to_home is self:
                    self.safely_home = True
                    batted_ball.running_to_home = None
            elif self.will_round_base:
                # We can't have, e.g., two batted_ball.running_to_thirds, so if the
                # preceding runner is rounding his base -- which, if you are rounding
                # your base, he *is* -- but hasn't quite got there yet, while you
                # already have, keep incrementing your baserunning progress for a few
                # timesteps until he rounds the base, at which point we can switch, e.g.,
                # him to batted_ball.running_to_home and you to batted_ball.running_to_third
                next_basepath_is_clear = False
                if self is batted_ball.running_to_third:
                    if not batted_ball.running_to_home or batted_ball.running_to_home.out:
                        next_basepath_is_clear = True
                elif self is batted_ball.running_to_second:
                    if not batted_ball.running_to_third or batted_ball.running_to_third.out:
                        next_basepath_is_clear = True
                elif self is batted_ball.running_to_first:
                    if not batted_ball.running_to_second or batted_ball.running_to_second.out:
                        next_basepath_is_clear = True
                if not next_basepath_is_clear:
                    print ("-- {} is waiting for the preceding runner to round the base "
                           "to technically round the base [{}]").format(
                        self.last_name, batted_ball.time_since_contact
                    )
                if next_basepath_is_clear:
                    # Round the base, retaining the remainder of last timestep's baserunning progress
                    self.percent_to_base -= 1.0
                    self.forced_to_advance = False
                    self.will_round_base = False
                    if self is batted_ball.running_to_first:
                        print "-- {} has rounded first [{}]".format(self.last_name, batted_ball.time_since_contact)
                        batted_ball.running_to_first = None
                        batted_ball.running_to_second = self
                        next_base_coords = (0, 127)
                    elif self is batted_ball.running_to_second:
                        print "-- {} has rounded second [{}]".format(self.last_name, batted_ball.time_since_contact)
                        batted_ball.running_to_second = None
                        batted_ball.running_to_third = self
                        next_base_coords = (-63.5, 63.5)
                    elif self is batted_ball.running_to_third:
                        print "-- {} has rounded third [{}]".format(self.last_name, batted_ball.time_since_contact)
                        batted_ball.running_to_third = None
                        batted_ball.running_to_home = self
                        next_base_coords = (0, 0)
                    # If the ball has not been fielded yet and is still more than 50 feet away,
                    # quickly take the next base
                    self.estimate_whether_you_can_beat_throw(batted_ball=batted_ball)
                    if self.believes_he_can_beat_throw:
                        self.taking_next_base = True
                        print "-- {} is taking the next base because he believes he can beat the throw [{}].".format(
                            self.last_name, batted_ball.time_since_contact
                        )
                    else:
                        self.retreat(batted_ball=batted_ball)
        # If you haven't already, decide whether to round the base you are advancing to, which will
        # be at a 10% reduction in your percentage to base
        if not self._decided_finish and self.percent_to_base > 0.49:
            # Of course, you will not be rounding home
            if self is batted_ball.running_to_home:
                self.will_round_base = False
                self._decided_finish = True
            # For all other baserunners, make decision based on whether the ball has been fielded
            # already, and if it hasn't, whether it was hit to the infield or the outfield -- this
            # reasoning is precluded, however, if there is an immediately preceding runner who
            # himself will not round the base
            else:
                if self is batted_ball.running_to_first:
                    preceding_runner = batted_ball.running_to_second
                elif self is batted_ball.running_to_second:
                    preceding_runner = batted_ball.running_to_third
                elif self is batted_ball.running_to_third:
                    preceding_runner = batted_ball.running_to_home
                else:
                    print ("Error 8181: person.baserun() called for {}, who is none of "
                           "batted_ball.running_to_first, running_to_second, running_to_third, or running_to_home")
                next_basepath_is_clear = False
                if not preceding_runner:
                    next_basepath_is_clear = True
                elif preceding_runner and preceding_runner.out:
                    next_basepath_is_clear = True
                elif preceding_runner and preceding_runner.will_round_base:
                    next_basepath_is_clear = True
                elif preceding_runner and preceding_runner is batted_ball.running_to_home:
                    next_basepath_is_clear = True
                if next_basepath_is_clear:
                    player_fielding_the_ball = next(f for f in batted_ball.at_bat.fielders if f.playing_the_ball)
                    if not batted_ball.fielded_by and player_fielding_the_ball.outfielder:
                        self.will_round_base = True
                        self._decided_finish = True
                        self.percent_to_base -= 0.1
                        if self is batted_ball.running_to_third:
                            base = "third"
                        elif self is batted_ball.running_to_second:
                            base = "second"
                        elif self is batted_ball.running_to_first:
                            base = "first"
                        print ("-- {} will round {} because ball is hit to outfield "
                               "and hasn't been fielded yet [{}]").format(
                            self.last_name, base, batted_ball.time_since_contact
                        )
                    else:
                        self.will_round_base = False
                        self._decided_finish = True
                        if self is batted_ball.running_to_third:
                            base = "third"
                        elif self is batted_ball.running_to_second:
                            base = "second"
                        elif self is batted_ball.running_to_first:
                            base = "first"
                        if player_fielding_the_ball.infielder:
                            print "-- {} will not round {} because the ball was hit to infield [{}]".format(
                                self.last_name, base, batted_ball.time_since_contact)
                        elif batted_ball.fielded_by:
                            print ("-- {} will not round {} because, even though it was hit "
                                   "to outfield, the ball has been fielded already [{}]").format(
                                self.last_name, base, batted_ball.time_since_contact)
                elif not next_basepath_is_clear and self.percent_to_base >= 0.85:
                    # At this point, it looks like the preceding runner won't be rounding
                    # his base, so you'll be forced to stand pat at the immediately coming
                    # base, should you arrive to it safely
                    self.will_round_base = False
                    self._decided_finish = True
                    if self is batted_ball.running_to_third:
                        base = "third"
                    elif self is batted_ball.running_to_second:
                        base = "second"
                    elif self is batted_ball.running_to_first:
                        base = "first"
                    print ("-- {} will not round {} because the preceding runner {} "
                           "is not rounding his base [{}]").format(
                        self.last_name, base, preceding_runner.last_name, batted_ball.time_since_contact
                    )

        ## TODO ADD DIFFICULTY TO FIELD BALL AND CHANCE OF ERROR FOR THROW IF
        ## BATTED_BALL.HEADING_TO_SECOND, due to batter-runner threatening
        ## to take second

    def tentatively_baserun(self, batted_ball):
        """Move along the base paths tentatively before resolution of a fly-ball fielding chance."""
        if not self._done_tentatively_advancing:
            # Determine what your percentage to the next base would be if you decide to
            # advance further on this timestep -- this, when multiplied by 90, conveniently
            # represents the distance required to retreat would be from that position
            percent_to_base_upon_advancement = (
                self.percent_to_base + (0.1/self.full_speed_sec_per_foot) / 90
            )
            if percent_to_base_upon_advancement < 1.0:  # Don't advance onto the next base path -- too weird
                # Estimate how long it would take to retreat if the fly-ball were caught, given
                # your positioning on the base paths if you *were* to advance on this timestep
                time_expected_for_me_to_retreat = (
                    (percent_to_base_upon_advancement * 90) * self.full_speed_sec_per_foot
                )
                # Estimate how long the potential throw to the preceding base you would be
                # retreating to would take -- assume typical throwing velocity and release time
                player_fielding_the_ball = next(f for f in batted_ball.at_bat.fielders if f.playing_the_ball)
                if self is batted_ball.at_bat.frame.on_first:
                    preceding_base_coords = [63.5, 63.5]
                elif self is batted_ball.at_bat.frame.on_second:
                    preceding_base_coords = [0, 127]
                elif self is batted_ball.at_bat.frame.on_third:
                    preceding_base_coords = [-63.5, 63.5]
                dist_from_fielding_chance_to_preceding_base = (
                    math.hypot(player_fielding_the_ball.immediate_goal[0]-preceding_base_coords[0],
                               player_fielding_the_ball.immediate_goal[1]-preceding_base_coords[1])
                )
                time_expected_for_throw_release = (
                    math.sqrt(dist_from_fielding_chance_to_preceding_base) * 0.075
                )
                time_expected_for_throw_itself = (
                    dist_from_fielding_chance_to_preceding_base / 110.  # 110 ft/s = 75 MPH (typical velocity)
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
                    print "-- {} is waiting at {} of the way until the fielding chance is resolved [{}]".format(
                        self.last_name, round(self.percent_to_base, 2), batted_ball.time_since_contact
                    )

    def retreat(self, batted_ball):
        """Retreat to the preceding base."""
        if not self._started_retreating:
            self.percent_to_base = 1 - self.percent_to_base
            self._started_retreating = True
            if self is batted_ball.running_to_second:
                batted_ball.running_to_second = None
                batted_ball.retreating_to_first = self
                if not self.forced_to_retreat:
                    print "-- {} is retreating to first because he does not believe he can beat the throw [{}]".format(
                        self.last_name, batted_ball.time_since_contact)
                elif self.forced_to_retreat:
                    print "-- {} is retreating to first to tag up [{}]".format(
                        self.last_name, batted_ball.time_since_contact
                    )
            elif self is batted_ball.running_to_third:
                batted_ball.running_to_third = None
                batted_ball.retreating_to_second = self
                if not self.forced_to_retreat:
                    print "-- {} is retreating to second because he does not believe he can beat the throw [{}]".format(
                        self.last_name, batted_ball.time_since_contact)
                elif self.forced_to_retreat:
                    print "-- {} is retreating to second to tag up [{}]".format(
                        self.last_name, batted_ball.time_since_contact
                    )
            elif self is batted_ball.running_to_home:
                batted_ball.running_to_home = None
                batted_ball.retreating_to_third = self
                if not self.forced_to_retreat:
                    print "-- {} is retreating to third because he does not believe he can beat the throw [{}]".format(
                        self.last_name, batted_ball.time_since_contact)
                elif self.forced_to_retreat:
                    print "-- {} is retreating to third to tag up [{}]".format(
                        self.last_name, batted_ball.time_since_contact
                    )
        self.percent_to_base += (0.1/self.full_speed_sec_per_foot) / 90
        if self.percent_to_base >= 1.0:
            self.safely_on_base = True
            # Determine the exact timestep that you reached base
            if not self.timestep_reached_base:
                surplus_percentage_to_base = self.percent_to_base-1
                surplus_distance = surplus_percentage_to_base*90
                surplus_time = surplus_distance * self.full_speed_sec_per_foot
                self.timestep_reached_base = batted_ball.time_since_contact - surplus_time
            self.percent_to_base = 1.0
            # Decide whether to quickly tag-up and attempt to advance to the next base --
            # if the next base path is not clear, do not advance
            next_base_path_is_clear = True
            if self is batted_ball.retreating_to_first:
                if batted_ball.retreating_to_second:
                    next_base_path_is_clear = False
            elif self is batted_ball.retreating_to_second:
                if batted_ball.retreating_to_third:
                    next_base_path_is_clear = False
            if next_base_path_is_clear:
                self.percent_to_base = 0.0
                self.estimate_whether_you_can_beat_throw(batted_ball=batted_ball)
                if self.believes_he_can_beat_throw:
                    self.forced_to_retreat = False
                    self._decided_finish = False
                    self.will_round_base = False
                    self.taking_next_base = False
                    self.safely_on_base = False
                    if self is batted_ball.retreating_to_first:
                        print ("-- {} tagged up at first and will now attempt to take second "
                               "because he believes he can beat any throw there [{}]").format(
                            self.last_name, batted_ball.time_since_contact)
                        batted_ball.retreating_to_first = None
                        batted_ball.running_to_second = self
                    elif self is batted_ball.retreating_to_second:
                        print ("-- {} tagged up at second and will now attempt to take third "
                               "because he believes he can beat any throw there [{}]").format(
                            self.last_name, batted_ball.time_since_contact)
                        batted_ball.retreating_to_second = None
                        batted_ball.running_to_third = self
                    elif self is batted_ball.retreating_to_third:
                        print ("-- {} tagged up at third and will now attempt to run home "
                               "because he believes he can beat any throw there [{}]").format(
                            self.last_name, batted_ball.time_since_contact)
                        batted_ball.retreating_to_third = None
                        batted_ball.running_to_home = self
                else:
                    if self is batted_ball.retreating_to_first:
                        print "-- {} tagged up at first and will remain there [{}]".format(
                            self.last_name, batted_ball.time_since_contact
                        )
                    elif self is batted_ball.retreating_to_second:
                        print "-- {} tagged up at second and will remain there [{}]".format(
                            self.last_name, batted_ball.time_since_contact
                        )
                    elif self is batted_ball.retreating_to_third:
                        print "-- {} tagged up at third and will remain there [{}]".format(
                            self.last_name, batted_ball.time_since_contact
                        )

    def estimate_whether_you_can_beat_throw(self, batted_ball):
        if self is batted_ball.running_to_second or self is batted_ball.retreating_to_first:
            # If retreating, it is just to tag up, so the consideration is whether to
            # then attempt to advance upon tagging up
            next_base = "2B"
            next_base_coords = (0, 127)
        elif self is batted_ball.running_to_third or self is batted_ball.retreating_to_second:
            next_base = "3B"
            next_base_coords = (-63.5, 63.5)
        elif self is batted_ball.running_to_home or self is batted_ball.retreating_to_third:
            next_base = "H"
            next_base_coords = (0, 0)
        # Estimate how long it would take you to reach your next base -- TODO this is currently perfect estimate
        dist_from_me_to_next_base = 90 - (self.percent_to_base*90)
        time_expected_for_me_to_reach_next_base = (
            dist_from_me_to_next_base * self.full_speed_sec_per_foot
        )
        # If there is no throw yet, form a preliminary model of it and estimate how
        # long it would take to reach the base you are considering advancing to; do
        # this assuming a fairly typical 75 MPH throwing velocity and pretty decent
        # release time
        if not batted_ball.at_bat.throw:
            # TODO player learns outfielders' arm strengths
            # TODO player which base the throw will target
            player_fielding_the_ball = next(f for f in batted_ball.at_bat.fielders if f.playing_the_ball)
            dist_from_fielding_chance_to_next_base = (
                math.hypot(player_fielding_the_ball.immediate_goal[0]-next_base_coords[0],
                           player_fielding_the_ball.immediate_goal[1]-next_base_coords[1])
            )
            time_expected_for_fielder_approach_to_batted_ball = (
                player_fielding_the_ball.time_needed_to_field_ball - batted_ball.time_since_contact
            )
            time_expected_for_throw_release = (
                math.sqrt(dist_from_fielding_chance_to_next_base) * 0.075
            )
            time_expected_for_throw_itself = (
                dist_from_fielding_chance_to_next_base / 110.  # 110 ft/s = 75 MPH
            )
            time_expected_for_throw_to_next_base = (
                time_expected_for_fielder_approach_to_batted_ball +
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
        # If there is a throw already, reason about how long it would take to reach the base you
        # are considering advancing to
        elif batted_ball.at_bat.throw:
            throw = batted_ball.at_bat.throw
            # Estimate how long it will take throw to reach its target
            distance_from_throw_to_target = 1 - throw.percent_to_target
            time_expected_for_throw_to_reach_target = (
                distance_from_throw_to_target / throw.dist_per_timestep
            )
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
                distance_from_throw_target_to_next_base = (
                    math.hypot(throw_target_coords[0]-next_base_coords[0],
                               throw_target_coords[1]-next_base_coords[1])
                )
                time_expected_for_throw_release = (
                    math.sqrt(distance_from_throw_target_to_next_base) * 0.075
                )
                time_expected_for_throw_itself = (
                    distance_from_throw_target_to_next_base / 110.  # 110 ft/s = 75 MPH
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
        if realistic_estimate_of_difference <= 0:
            my_estimate_of_difference = realistic_estimate_of_difference * self.confidence
        else:
            my_estimate_of_difference = realistic_estimate_of_difference / self.confidence
        # Determine the player's risk buffer, a value in seconds that will be added to the
        # player's estimate -- audacious players will give a negative risk buffer, and thus
        # will decide to challenge the throw even if, all other things being equal they
        # realize the throw may beat them
        risk_buffer = (1.0-self.audacity)/1.5
        if my_estimate_of_difference + risk_buffer < 0:
            self.believes_he_can_beat_throw = True
            if realistic_estimate_of_difference > 0:
                print "-- Due to confidence and/or audacity, {} will riskily attempt to take the next base".format(
                    self.last_name
                )
        else:
            self.believes_he_can_beat_throw = False
            if realistic_estimate_of_difference < 0:
                print ("-- Due to timidness or lack of confidence, {} will (perhaps overcautiously) "
                       "stay at his base").format(self.last_name)

    def field_ball(self, batted_ball):
        """Attempt to field a batted ball.."""
        batted_ball.bobbled = False
        line_drive_at_pitcher = False
        ball_totally_missed = False
        # If the batted ball is a line drive straight to the pitcher,
        # the difficulty is fixed and depends fully on reflexes, rather
        # than on fielding skill
        if batted_ball.time_since_contact < 0.6 and batted_ball.vertical_launch_angle > 0:
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
            difficulty /= self.composure
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
            batted_ball.fielding_difficulty = difficulty = 0.97
            # Simulate whether the ball is cleanly fielded
            difficulty /= self.fly_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.composure
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
            # Simulate whether the ball is cleanly fielded
            batted_ball.fielding_difficulty = difficulty
            difficulty /= self.fly_ball_fielding
            difficulty /= self.glove.fielding_advantage
            difficulty /= self.composure
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
            difficulty /= self.composure
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
        # Instantiate a FieldingAct object, which captures all this data and also modifies the fielder's
        # composure according to the results of the fielding act
        FieldingAct(fielder=self, batted_ball=batted_ball, objective_difficulty=batted_ball.fielding_difficulty,
                    subjective_difficulty=difficulty, line_drive_at_pitcher=line_drive_at_pitcher,
                    ball_totally_missed=ball_totally_missed)


    def decide_throw(self, batted_ball):
        # TODO if there are two outs, take the surest throw that has chance for out
        # TODO player should reason about how much power they need on the throw
        # TODO ego, denying aging, etc., should effect what player believes their throwing velocity is
        # TODO factor in relay throws in reasoning
        # Before reasoning about the throw, assess the baserunner situation
        chance_for_out_at_first = False
        chance_for_out_at_second = False
        chance_for_out_at_third = False
        chance_for_out_at_home = False
        runner_threatening_second = False
        runner_threatening_third = False
        runner_threatening_home = False
        # First, take note of baserunners who are actively advancing or who are being forced to retreat
        # by a fly out -- these represent situations in which there is a real chance of making an out
        if ((batted_ball.running_to_first and not batted_ball.running_to_first.will_round_base and not
            batted_ball.running_to_first.safely_on_base) or
                (batted_ball.retreating_to_first and batted_ball.retreating_to_first.forced_to_retreat and
                    not batted_ball.retreating_to_first.safely_on_base)):
            chance_for_out_at_first = True
        if ((batted_ball.running_to_second and not batted_ball.running_to_second.will_round_base and
            not batted_ball.running_to_second.safely_on_base) or
                (batted_ball.retreating_to_second and batted_ball.retreating_to_second.forced_to_retreat and
                    not batted_ball.retreating_to_second.safely_on_base)):
            chance_for_out_at_second = True
        if ((batted_ball.running_to_third and not batted_ball.running_to_third.will_round_base and
            not batted_ball.running_to_third.safely_on_base) or
                (batted_ball.retreating_to_third and batted_ball.retreating_to_third.forced_to_retreat and
                    not batted_ball.retreating_to_third.safely_on_base)):
            chance_for_out_at_third = True
        if batted_ball.running_to_home and not batted_ball.running_to_home.safely_home:
            chance_for_out_at_home = True
        # Also take note of baserunners who have rounded a base or who apparently will round a base,
        # but represent no real threat of advancing unless there is an error -- in these cases, the
        # throw would be made preemptively to the base that the runner is threatening to advance to
        if ((batted_ball.running_to_first and batted_ball.running_to_first.will_round_base) or
                (batted_ball.retreating_to_first and not batted_ball.retreating_to_first.safely_on_base)):
            # Batter-runner is on a banana turn to first, or has already rounded first
            runner_threatening_second = True
        if ((batted_ball.running_to_second and batted_ball.running_to_second.will_round_base) or
                (batted_ball.retreating_to_second and not batted_ball.retreating_to_second.safely_on_base)):
            runner_threatening_third = True
        if ((batted_ball.running_to_third and batted_ball.running_to_third.will_round_base) or
                (batted_ball.retreating_to_third and not batted_ball.retreating_to_third.safely_on_base)):
            runner_threatening_home = True
        # Now, reason about the utility and chance of success for each potential throw, given
        # the baserunner situation that we just surveyed above
        diff_for_throw_to_home = None
        diff_for_throw_to_third = None
        diff_for_throw_to_second = None
        diff_for_throw_to_first = None
        if chance_for_out_at_home or runner_threatening_home:
            # Determine whether your throw could beat the runner
            dist_to_home = math.hypot(self.location[0]-0, self.location[1]-0)
            time_expected_for_throw_release = (
                math.sqrt(dist_to_home) * self.throwing_release_time
            )
            time_expected_for_throw_itself = dist_to_home / self.throwing_velocity
            time_expected_for_throw_to_home = (
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
            if batted_ball.running_to_home:
                dist_from_runner_to_home = 90 - (batted_ball.running_to_home.percent_to_base*90)
            elif batted_ball.retreating_to_third:
                dist_from_runner_to_home = 90  # This is basically irrelevant
            elif batted_ball.running_to_third:
                dist_from_runner_to_home = 180 - (batted_ball.running_to_third.percent_to_base*90)
            # Assume decent footspeed for runner, but not that fast, a ~7.0 60-yard dash
            time_expected_for_runner_to_reach_home = dist_from_runner_to_home * 0.39
            diff_for_throw_to_home = (
                time_expected_for_throw_to_home - time_expected_for_runner_to_reach_home
            )
        if chance_for_out_at_third or runner_threatening_third:
            # Determine whether your throw could beat the runner
            dist_to_third = math.hypot(self.location[0]--63.5, self.location[1]-63.5)
            time_expected_for_throw_release = (
                math.sqrt(dist_to_third) * self.throwing_release_time
            )
            time_expected_for_throw_itself = dist_to_third / self.throwing_velocity
            time_expected_for_throw_to_third = (
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
            if batted_ball.running_to_third:
                dist_from_runner_to_third = 90 - (batted_ball.running_to_third.percent_to_base*90)
            elif batted_ball.retreating_to_third:
                dist_from_runner_to_third = 90 - (batted_ball.retreating_to_third.percent_to_base*90)
            elif batted_ball.running_to_second:
                dist_from_runner_to_third = 180 - (batted_ball.running_to_second.percent_to_base*90)
            elif batted_ball.retreating_to_second:
                dist_from_runner_to_third = 90  # This is basically irrelevant
            # Assume decent footspeed for runner, but not that fast, a ~7.0 60-yard dash
            time_expected_for_runner_to_reach_third = dist_from_runner_to_third * 0.39
            diff_for_throw_to_third = (
                time_expected_for_throw_to_third - time_expected_for_runner_to_reach_third
            )
        if chance_for_out_at_second or runner_threatening_second:
            # Determine whether your throw could beat the runner
            dist_to_second = math.hypot(self.location[0]-0, self.location[1]-127)
            time_expected_for_throw_release = (
                math.sqrt(dist_to_second) * self.throwing_release_time
            )
            time_expected_for_throw_itself = dist_to_second / self.throwing_velocity
            time_expected_for_throw_to_second = (
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
            if batted_ball.running_to_second:
                dist_from_runner_to_second = 90 - (batted_ball.running_to_second.percent_to_base*90)
            elif batted_ball.retreating_to_second:
                dist_from_runner_to_second = 90 - (batted_ball.retreating_to_second.percent_to_base*90)
            elif batted_ball.running_to_first:
                dist_from_runner_to_second = 180 - (batted_ball.running_to_first.percent_to_base*90)
            elif batted_ball.retreating_to_first:
                dist_from_runner_to_second = 90  # This is basically irrelevant
            # Assume decent footspeed for runner, but not that fast, a ~7.0 60-yard dash
            time_expected_for_runner_to_reach_second = dist_from_runner_to_second * 0.39
            diff_for_throw_to_second = (
                time_expected_for_throw_to_second - time_expected_for_runner_to_reach_second
            )
        if chance_for_out_at_first:
            # Runner going to first who is not on a banana turn or runner who is being forced to
            # tag up at first due to fly out-- determine whether your throw could beat the runner
            runner_in_question = batted_ball.running_to_first or batted_ball.retreating_to_first
            dist_to_first = math.hypot(self.location[0]-63.5, self.location[1]-63.5)
            time_expected_for_throw_release = (
                math.sqrt(dist_to_first) * self.throwing_release_time
            )
            time_expected_for_throw_itself = dist_to_first / self.throwing_velocity
            time_expected_for_throw_to_first = (
                time_expected_for_throw_release + time_expected_for_throw_itself
            )
            dist_from_runner_to_first = 90 - (runner_in_question.percent_to_base*90)
            # Assume decent footspeed for runner, but not that fast, a ~7.0 60-yard dash
            time_expected_for_runner_to_reach_first = dist_from_runner_to_first * 0.39
            diff_for_throw_to_first = (
                time_expected_for_throw_to_first - time_expected_for_runner_to_reach_first
            )
        # Decide where to throw, given the chances of success and potential utility of each
        # TODO give more nuanced scoring procedure here
        if chance_for_out_at_home and diff_for_throw_to_home <= 0:
            print "-- {} ({}) will throw to home from [{}, {}] [{}]".format(
                self.last_name, self.position, int(self.location[0]), int(self.location[1]),
                batted_ball.time_since_contact
            )
            self.throwing_to_home = True
            self._throw_target = batted_ball.covering_home
            self._throw_target_coords = [0, 0]
            self._throw_distance_to_target = dist_to_home
        elif chance_for_out_at_third and diff_for_throw_to_third <= 0:
            print "-- {} ({}) will throw to third from [{}, {}] [{}]".format(
                self.last_name, self.position, int(self.location[0]), int(self.location[1]),
                batted_ball.time_since_contact
            )
            self.throwing_to_third = True
            self._throw_target = batted_ball.covering_third
            self._throw_target_coords = [-63.5, 63.5]
            self._throw_distance_to_target = dist_to_third
        elif chance_for_out_at_second and diff_for_throw_to_second <= 0:
            print "-- {} ({}) will throw to second from [{}, {}] [{}]".format(
                self.last_name, self.position, int(self.location[0]), int(self.location[1]),
                batted_ball.time_since_contact
            )
            self.throwing_to_second = True
            self._throw_target = batted_ball.covering_second
            self._throw_target_coords = [0, 127]
            self._throw_distance_to_target = dist_to_second
        elif chance_for_out_at_first and diff_for_throw_to_first <= 0:
            # If no other runners, just throw to first for due diligence
            print "-- {} ({}) will throw to first from [{}, {}] [{}]".format(
                self.last_name, self.position, int(self.location[0]), int(self.location[1]),
                batted_ball.time_since_contact
            )
            self.throwing_to_first = True
            self._throw_target = batted_ball.covering_first
            self._throw_target_coords = [63.5, 63.5]
            self._throw_distance_to_target = dist_to_first
        elif runner_threatening_home:
            print "-- {} ({}) will throw to home preemptively [{}]".format(
                self.last_name, self.position, batted_ball.time_since_contact
            )
            self.throwing_to_home = True
            self._throw_target = batted_ball.covering_home
            self._throw_target_coords = [0, 0]
            self._throw_distance_to_target = dist_to_home
        elif runner_threatening_third:
            print "-- {} ({}) will throw to third preemptively [{}]".format(
                self.last_name, self.position, batted_ball.time_since_contact
            )
            self.throwing_to_third = True
            self._throw_target = batted_ball.covering_third
            self._throw_target_coords = [-63.5, 63.5]
            self._throw_distance_to_target = dist_to_third
        elif runner_threatening_second:
            print "-- {} ({}) will throw to second preemptively [{}]".format(
                self.last_name, self.position, batted_ball.time_since_contact
            )
            self.throwing_to_second = True
            self._throw_target = batted_ball.covering_second
            self._throw_target_coords = [0, 127]
            self._throw_distance_to_target = dist_to_second
        else:
            print "-- {} ({}) will just throw to pitcher [{}]".format(
                self.last_name, self.position, batted_ball.time_since_contact
            )
            self.throwing_back_to_pitcher = True
            self._throw_target = self.team.pitcher
            self._throw_target_coords = [0, 60.5]
            self._throw_distance_to_target = math.hypot(self.location[0]-0, self.location[1]-60.5)
        self._throw_release = "Overhand"
        self._throw_power = 1.0

    def throw(self, batted_ball):
        """Throw a ball to a target."""
        # Determine the base that is being thrown to, and the runner
        # approaching that base, if any, whose putout would be assisted
        # by the throw
        if self.throwing_to_first:
            targeted_base = "1B"
            if batted_ball.running_to_first:
                runner_to_putout = batted_ball.running_to_first
            elif batted_ball.retreating_to_first:
                runner_to_putout = batted_ball.retreating_to_first
            else:
                runner_to_putout = None
        elif self.throwing_to_second:
            targeted_base = "2B"
            if batted_ball.running_to_second:
                runner_to_putout = batted_ball.running_to_second
            elif batted_ball.retreating_to_second:
                runner_to_putout = batted_ball.retreating_to_second
            else:
                runner_to_putout = None
        elif self.throwing_to_third:
            targeted_base = "3B"
            if batted_ball.running_to_third:
                runner_to_putout = batted_ball.running_to_third
            elif batted_ball.retreating_to_third:
                runner_to_putout = batted_ball.retreating_to_third
            else:
                runner_to_putout = None
        elif self.throwing_to_home:
            targeted_base = "H"
            if batted_ball.running_to_home:
                runner_to_putout = batted_ball.running_to_home
            else:
                runner_to_putout = None
        else:
            targeted_base = None
            runner_to_putout = None
        if self._throw_release == "Overhand":
            # TODO release time should be affected by power on the throw
            release_time = (
                math.sqrt(self._throw_distance_to_target) * self.throwing_release_time
            )
            error = self.throwing_error_per_foot * self._throw_distance_to_target
            height_error = normal(0, error)
            lateral_error = normal(0, error)
        # TODO sidearm throws
        throw = Throw(batted_ball=batted_ball, thrown_by=self, thrown_to=self._throw_target, base=targeted_base,
                      runner_to_putout=runner_to_putout, release_time=release_time,
                      distance_to_target=self._throw_distance_to_target, release=self._throw_release,
                      power=self._throw_power, height_error=height_error, lateral_error=lateral_error,
                      back_to_pitcher=self.throwing_back_to_pitcher)
        return throw

    def tag(self, baserunner):
        pass
        # TODO NEXT!






