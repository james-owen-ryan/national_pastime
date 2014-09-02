import random


class Game(object):

    def __init__(self, league, home_team, away_team):
        self.league = league
        self.home_team = home_team
        self.away_team = away_team
        # Prepare for game
        home_team.pitcher = home_team.pitcher
        away_team.pitcher = away_team.pitcher
        home_team.batting_order = home_team.players
        away_team.batting_order = away_team.players
        home_team.batter = home_team.batting_order[0]
        away_team.batter = away_team.batting_order[0]
        self.home_team.runs = self.away_team.runs = 0
        self.innings = []
        for inning_n in xrange(1, 10):
            Inning(game=self, number=inning_n)
        inning_n = 9
        while home_team.runs == away_team.runs:
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
        # Players currently on base
        self.first = None
        self.second = None
        self.third = None
        # Other miscellany
        self.outs = 0
        self.at_bats = []
        # Enact top frame
        self.frame = 'Top'
        print "\t {} \n".format(self)
        raw_input("")
        batting_team = self.game.away_team
        pitching_team = self.game.home_team
        while self.outs < 3:
            # batting_team.consider_changes(game=self.game)
            # .pitching_team.consider_changes(game=self.game)
            # self.simulate_deadball_events()
            ab = AtBat(inning=self, pitcher=pitching_team.pitcher,
                       batter=batting_team.batter, fielders=pitching_team.fielders)
            print ab.outcome
            print "1B: {}  2B: {}  3B: {}".format(self.first, self.second, self.third)
            raw_input("")
        self.outs = 0
        # Enact bottom frame
        self.frame = 'Bottom'
        print "\t {} \n".format(self)
        raw_input("")
        batting_team = self.game.home_team
        pitching_team = self.game.away_team
        if not batting_team.runs > pitching_team.runs:
            while self.outs < 3:
                # self.batting_team.consider_changes(game=self.game)
                # self.pitching_team.consider_changes(game=self.game)
                # self.simulate_deadball_events()
                ab = AtBat(inning=self, pitcher=pitching_team.pitcher,
                           batter=batting_team.batter, fielders=pitching_team.fielders)
                print ab.outcome
                print "1B: {}  2B: {}  3B: {}".format(self.first, self.second, self.third)
                raw_input('')

    def __str__(self):
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth'
        }
        if self.frame == "Top":
            return "{} of the {} inning -- {} up to bat".format(
                self.frame, ordinals[self.number], self.game.away_team
            )
        else:
            return "{} of the {} inning -- {} up to bat".format(
                self.frame, ordinals[self.number], self.game.home_team
            )


class AtBat(object):

    def __init__(self, inning, pitcher, batter, catcher, fielders, umpire=None):
        self.inning = inning
        # self.game = inning.game
        # self.inning.at_bats.append(self)
        self.batter = batter
        self.pitcher = pitcher
        self.catcher = catcher
        self.fielders = fielders
        if not umpire:
            self.umpire = pitcher.hometown.players[-1]
        else:
            self.umpire = umpire
        self.pitches = []

    def enact(self, pitch_coords=None, count=None, power=0.8):
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
        kind, x, y = p.decide_pitch(batter=b,
                                    count=count)
        if pitch_coords:
            x, y = pitch_coords
        pitch = p.pitch(batter=b, catcher=c, at_bat=self,
                        x=x, y=y, kind=kind)
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
                print "\n\tVertical launch angle: {}".format(bb.vertical_launch_angle)
                print "\tHorizontal launch angle: {}".format(bb.horizontal_launch_angle)
                print "\tDistance: {}".format(bb.true_distance)
                print "\tLanding point: {}".format(bb.true_landing_point)
                return bb
            elif not swing.contact:
                print "\n\tSwing and a miss!"
                print "Reasons: {}\n".format(swing.swing_and_miss_reasons)
                return swing


    # def enact(self):
    #     # if pitcher.intent == "bean":
    #     #     batter.walk(beanball=True)
    #     # if pitcher.intent == "walk":
    #     #     batter.walk(intentional=True)
    #     x = random.random()
    #     if x < 0.1:
    #         return self.home_run()
    #     elif x < 0.4:
    #         return self.strikeout(swing_and_a_miss=True)
    #     elif x < 0.75:
    #         return self.strikeout(called_third_strike=True)
    #     elif x < 0.8:
    #         return self.walk(beanball=True)
    #     elif x < 0.9:
    #         return self.walk(hit_by_pitch=True)
    #     elif x < 0.95:
    #         return self.walk(intentional=True)
    #     else:
    #         return self.walk()

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