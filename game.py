import random
from outcome import Strike, Ball, Strikeout, BaseOnBalls

COUNTS = {(0, 0): 00, (1, 0): 10, (2, 0): 20, (3, 0): 30,
          (0, 1): 10, (1, 1): 11, (2, 1): 21, (3, 1): 31,
          (0, 2): 02, (1, 2): 12, (2, 2): 22, (3, 2): 32}


class Game(object):

    def __init__(self, ballpark, home_team, away_team, league, rules):
        self.ballpark = ballpark
        self.league = league
        self.home_team = home_team
        self.away_team = away_team
        self.rules = rules  # Rules game will be played under
        # Prepare for game
        home_team.pitcher = home_team.pitcher
        away_team.pitcher = away_team.pitcher
        home_team.batting_order = home_team.players
        away_team.batting_order = away_team.players
        home_team.batter = home_team.batting_order[0]
        away_team.batter = away_team.batting_order[0]
        self.home_team.runs = self.away_team.runs = 0
        self.innings = []
        self.umpire = next(z for z in self.league.country.players if
                           z.hometown.name in ("Minneapolis", "St. Paul", "Duluth"))

    def enact(self):
        for inning_n in xrange(1, 10):
            Inning(game=self, number=inning_n)
        inning_n = 9
        while self.home_team.runs == self.away_team.runs:
            inning_n += 1
            Inning(game=self, number=inning_n)
        if self.home_team.runs > self.away_team.runs:
            self.winner = self.home_team
            self.loser = self.away_team
        else:
            self.winner = self.away_team
            self.loser = self.home_team
        print "{} has beaten {} {}-{}".format(
            self.winner.city.name, self.loser.city.name, self.winner.runs, self.loser.runs
        )
        self.home_team.runs = self.away_team.runs = 0

    @staticmethod
    def get_next_batter(team):
        try:
            batter_index = team.batting_order.index(team.batter)
            next_batter = team.batting_order[batter_index+1]
        except IndexError:  # Reached end of the order, go back to top
            next_batter = team.batting_order[0]
        return next_batter


class Inning(object):

    def __init__(self, game, number):
        self.game = game
        self.game.innings.append(self)
        self.number = number
        self.frames = []

    def enact(self):
        top = Frame(inning=self, top=True)
        top.enact()
        if not (self.number >= 9 and
                self.game.home_team.runs > self.game.away_team.runs):
            bottom = Frame(inning=self, bottom=True)
            bottom.enact()


class Frame(object):

    def __init__(self, inning, top=False, middle=False, bottom=False):
        self.inning = inning
        inning.frames.append(self)
        self.game = inning.game
        if top:
            self.half = "Top"
            self.batting_team = self.game.away_team
            self.pitching_team = self.game.home_team
        elif middle:
            self.half = "Middle"
        elif bottom:
            self.half = "Bottom"
            self.batting_team = self.game.home_team
            self.pitching_team = self.game.away_team
        # Players currently on base
        self.on_first = None
        self.on_second = None
        self.on_third = None
        # Other miscellany
        self.runs = 0  # Runs batting team has scored this inning
        self.outs = 0
        self.at_bats = []  # Appended to by AtBat.__init__()
        self.at_bat = None

    def enact(self):
        while self.outs < 3:
            self.at_bat = AtBat(frame=self)

    def advance_runners(self):
        """Advance the batter to first and any preceding runners, as necessary."""
        if self.on_first and self.on_second and self.on_third:
            self.batting_team.runs += 1  # Third advances and scores
            self.on_third = self.on_second
            self.on_second = self.on_first
            self.on_first = self.at_bat.batter
        elif self.inning.first and self.inning.second:
            self.on_third = self.on_second
            self.on_second = self.on_first
            self.on_first = self.at_bat.batter
        elif self.on_first:
            self.on_second = self.on_first
            self.on_first = self.at_bat.batter
        else:
            self.on_first = self.at_bat.batter

    def __str__(self):
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth'
        }
        if self.half == "Top":
            return "{} of the {} inning -- {} up to bat".format(
                self.half, ordinals[self.inning.number], self.game.away_team
            )
        else:
            return "{} of the {} inning -- {} up to bat".format(
                self.half, ordinals[self.inning.number], self.game.home_team
            )


class AtBat(object):

    def __init__(self, frame):
        self.frame = frame
        self.frame.at_bats.append(self)
        self.game = frame.game
        self.batter = frame.batting_team.batter
        self.pitcher = frame.pitching_team.pitcher
        self.catcher = frame.pitching_team.catcher
        self.fielders = frame.pitching_team.fielders
        self.umpire = self.game.umpire
        self.pitches = []
        # Blank count to start
        self.balls = self.strikes = 0
        self.count = 00
        # Modified below
        self.result = None

    def enact(self):
        resolved = False
        while not resolved:
            self.count = COUNTS[(self.balls, self.strikes)]
            # Fielders get in position
            for fielder in self.fielders:
                fielder.get_in_position()
            # Pitcher prepares delivery
            kind, x, y = self.pitcher.decide_pitch(at_bat=self)
            # The pitch...
            pitch = self.pitcher.pitch(at_bat=self, x=x, y=y, kind=kind)
            batter_will_swing = self.batter.decide_whether_to_swing(pitch)
            if not batter_will_swing:
                if not pitch.bean:
                    # Catcher attempts to receive pitch
                    pitch.caught = self.catcher.receive_pitch(pitch)
                    # Umpire makes his call
                    pitch.call = pitch.would_be_call
                    if pitch.call == "Strike":
                        Strike(pitch=pitch)
                    elif pitch.call == "Ball":
                        Ball(pitch=pitch)
            # The swing...
            elif batter_will_swing:
                power, upward_force, pull = (
                    self.batter.decide_how_to_swing(pitch)
                )
                swing = self.batter.swing(pitch, power, upward_force,
                                          pull)
                if not swing.contact:
                    # Swing and a miss!
                    Strike(pitch=pitch)
                else:
                    # Contact is made
                    batted_ball = swing.result
                    time_since_contact = 0.0
                    # Fielders read the batted ball and decide immediate goals



    def draw_playing_field(self):
        import turtle
        self.turtle = turtle
        turtle.setworldcoordinates(-1000, -1000, 1000, 1000)
        turtle.ht()
        turtle.tracer(10000)
        turtle.penup()
        turtle.goto(-226, 226)
        turtle.pendown()
        h, k = 226, 400  # Our vertex is the center-field wall
        a = -0.0034
        for x in xrange(0, 453):
            y = (a * (x - h)**2) + k
            turtle.goto(x-226, y)
        turtle.goto(0, -60)
        turtle.goto(-226, 226)
        turtle.penup()
        turtle.goto(0, 0)
        turtle.pendown()
        turtle.dot()
        turtle.goto(66.5, 66.5)
        turtle.dot()
        turtle.goto(0, 127)
        turtle.dot()
        turtle.goto(-66.5, 66.5)
        turtle.dot()
        turtle.goto(0, 0)
        turtle.goto(226, 226)
        turtle.goto(0, 0)
        turtle.goto(-226, 226)
        turtle.update()

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
            fielder.get_in_position()
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
            _, upward_force, pull = (
                b.decide_how_to_swing(pitch)
            )
            power = power
            swing = b.swing(pitch, power, upward_force,
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