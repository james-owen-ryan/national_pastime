import random
from people.event import Event
from outcome import Strike, Ball, FoulBall, Single, Double, Triple, HomeRun, Run, DoublePlay, TriplePlay, FieldersChoice
from playing_action import PitchInterim, PlayingAction


# First ever Talk of the Town-integrated game to be completed (03-18-2016):

# Southwark (0-0) has beaten Reading (0-0) 4-3
#
# 		    1   2   3   4   5   6   7   8   9
# 		    __________________________________
# Southwark	0   4   0   0   0   0   0   0   0	4
#
# Reading	0   0   0   0   0   0   0   0   3	3


class Game(Event):
    """A baseball game in a baseball cosmos."""

    def __init__(self, home_team, away_team, ballpark=None, league=None, rules=None,
                 radio=False, trace=False, debug=False):
        """Initialize a Game object."""
        self.cosmos = home_team.city.cosmos
        super(Game, self).__init__(cosmos=self.cosmos)  # This will collect metadata about the date, etc.
        self.home_team = home_team
        self.away_team = away_team
        # Turn debug or trace parameters on or off
        self.debug = debug
        self.trace = trace
        # Determine ballpark, league, rules of play, and umpire
        self.ballpark = home_team.ballpark if not ballpark else ballpark  # In case of neutral field
        self.league = home_team.league if not league else ballpark  # In case of non-league play
        self.rules = home_team.league.rules if not rules else rules  # In case of weird rules jazz
        self.umpire = self.league.umpire
        # Prepare for game
        self.home_team.runs = self.away_team.runs = 0
        home_team.pitcher = home_team.pitcher
        away_team.pitcher = away_team.pitcher
        home_team.batting_order = home_team.players
        away_team.batting_order = away_team.players
        home_team.batter = home_team.batting_order[-1]  # To get decent batter up during testing
        away_team.batter = away_team.batting_order[-1]
        self.home_team.runs = self.away_team.runs = 0
        self.innings = []
        if radio:
            self.radio_announcer = random.choice(self.home_team.city.players)
            while self.radio_announcer in self.home_team.players+self.away_team.players:
                self.radio_announcer = random.choice(self.home_team.city.players)
        else:
            self.radio_announcer = None
        self._init_determine_salience()
        self.composures_before = {}
        for player in away_team.players+home_team.players:
            self.composures_before[player] = player.composure
        if self.radio_announcer:
            self.radio_announcer.call_pregame(game=self)

    def __str__(self):
        """Return string representation."""
        return "{away_team} at {home_team}, {date}".format(
            away_team=self.away_team.name,
            home_team=self.home_team.name,
            date=self.date
        )

    def _init_determine_salience(self):
        """Determine the salience of this game.

        More salient games will have greater ramifications on player composure, confidence,
        etc.
        """
        self.salience = 1.0

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
        print "{} ({}-{}) has beaten {} ({}-{}) {}-{}".format(
            self.winner.city.name, self.winner.wins, self.winner.losses,
            self.loser.city.name, self.loser.wins, self.loser.losses,
            self.winner.runs, self.loser.runs
        )
        if self.trace:
            self.print_box_score()
        self.effect_consequences()
        # print "\n\t\tComposures before and after\n"
        # diffs = []
        # for player in self.away_team.players+self.home_team.players:
        #     print "{}, {}".format(player.name, player.position)
        #     diff = round(player.composure-self.composures_before[player], 2)
        #     diffs.append(diff)
        #     print "\t{}\t{}\t{}".format(round(self.composures_before[player], 2), round(player.composure, 2), diff)
        # print "\nAverage difference: {}".format(sum(diffs)/len(diffs))

    def effect_consequences(self):
        for player in self.away_team.players+self.home_team.players:
            conf_before, comp_before = player.person.personality.confidence, player.composure
            diff = player.composure-player.person.personality.confidence
            player.person.personality.confidence += (diff/100.) * self.salience
            player.composure -= (diff/10.) * self.salience
            if player.composure < 0.5:
                player.composure = 0.5
            elif player.composure > 1.5:
                player.composure = 1.5
            if self.trace:
                print "{}'s confidence changed by {}; his composure reverted from {} to {}".format(
                    player.person.name, round(player.person.personality.confidence-conf_before, 4),
                    round(comp_before, 2),
                    round(player.composure, 2)
                )
        self.winner.wins += 1
        self.loser.losses += 1

    def print_box_score(self):
        print '\n\n'
        print '\t\t' + '   '.join(str(i+1) for i in xrange(len(self.innings)))
        print '\t\t__________________________________'
        if len(self.away_team.city.name) >= 8:
            tabs_needed = '\t'
        else:
            tabs_needed = '\t\t'
        print (self.away_team.city.name + tabs_needed +
               '   '.join(str(inning.top.runs) for inning in self.innings) +
               '\t' + str(self.away_team.runs))
        print ''
        if len(self.home_team.city.name) >= 8:
            tabs_needed = '\t'
        else:
            tabs_needed = '\t\t'
        if self.innings[-1].bottom:
            print (self.home_team.city.name + tabs_needed +
                   '   '.join(str(inning.bottom.runs) for inning in self.innings) +
                   '\t' + str(self.home_team.runs))
        else:  # Home team didn't need to bat in bottom of the ninth inning
            print (self.home_team.city.name + tabs_needed +
                   '   '.join(str(inning.bottom.runs) for inning in self.innings[:-1]) +
                   '   -\t' + str(self.home_team.runs))
        print '\n\n\t {}\n'.format(self.away_team.name)
        print '\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
        for p in self.away_team.players:
            if len(p.career.statistics.at_bats) > 0:
                batting_avg = round(len(p.career.statistics.hits)/float(len(p.career.statistics.at_bats)), 3)
                if batting_avg == 1.0:
                    batting_avg = '1.000'
                else:
                    batting_avg = str(batting_avg)[1:]
            else:
                batting_avg = '.000'
            while len(batting_avg) < 4:
                batting_avg += '0'
            if len(p.person.last_name) >= 8:
                tabs_needed = '\t'
            else:
                tabs_needed = '\t\t'
            print "{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), 
                len(p.career.statistics.runs),
                len(p.career.statistics.hits),
                len(p.career.statistics.doubles), 
                len(p.career.statistics.triples), len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
                len(p.career.statistics.batting_walks), len(p.career.statistics.batting_strikeouts), len(p.career.statistics.stolen_bases), batting_avg
            )
        print '\n\n\t {}\n'.format(self.home_team.name)
        print '\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
        for p in self.home_team.players:
            if len(p.career.statistics.at_bats) > 0:  # TODO Did I screw this up by checking the career stats?
                batting_avg = round(len(p.career.statistics.hits)/float(len(p.career.statistics.at_bats)), 3)
                if batting_avg == 1.0:
                    batting_avg = '1.000'
                else:
                    batting_avg = str(batting_avg)[1:]
            else:
                batting_avg = '.000'
            while len(batting_avg) < 4:
                batting_avg += '0'
            if len(p.person.last_name) >= 8:
                tabs_needed = '\t'
            else:
                tabs_needed = '\t\t'
            print "{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), len(p.career.statistics.runs),
                len(p.career.statistics.hits),
                len(p.career.statistics.doubles), len(p.career.statistics.triples), 
                len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
                len(p.career.statistics.batting_walks), 
                len(p.career.statistics.batting_strikeouts), 
                len(p.career.statistics.stolen_bases), batting_avg
            )


class Inning(object):

    def __init__(self, game, number):
        self.game = game
        self.game.innings.append(self)
        self.number = number
        self.frames = []
        # Modified by self.enact()
        self.top = None
        self.bottom = None

        self.enact()

    def enact(self):
        self.top = Frame(inning=self, top=True)
        if not (self.number >= 9 and
                self.game.home_team.runs > self.game.away_team.runs):
            self.bottom = Frame(inning=self, bottom=True)


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
        if self.game.trace:
            print "\n\t\t*****  {}  *****\n\n".format(self)
        if self.game.radio_announcer:
            self.game.radio_announcer.call_new_frame(frame=self)
        self.enact()
        self.review()

    def __str__(self):
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
            19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first', 22: 'twenty-second',
            23: 'twenty-third', 24: 'twenty-fourth', 25: 'twenty-fifth',
            26: 'twenty-sixth', 27: 'twenty-seventh', 28: 'twenty-eighth',
            29: 'twenty-ninth', 30: 'thirtieth', 31: 'thirty-first'
        }
        if self.inning.number in ordinals:
            if self.half == "Top":
                return "{} of the {} inning -- {} up to bat".format(
                    self.half, ordinals[self.inning.number], self.game.away_team
                )
            else:
                return "{} of the {} inning -- {} up to bat".format(
                    self.half, ordinals[self.inning.number], self.game.home_team
                )
        else:
            if self.half == "Top":
                return "{} of inning {} -- {} up to bat".format(
                    self.half, self.inning.number, self.game.away_team
                )
            else:
                return "{} of inning {} -- {} up to bat".format(
                    self.half, self.inning.number, self.game.home_team
                )

    def get_next_batter(self):
        try:
            batter_index = (
                self.batting_team.batting_order.index(self.batting_team.batter)
            )
            next_batter = self.batting_team.batting_order[batter_index+1]
        except IndexError:  # Reached end of the order, go back to top
            next_batter = self.batting_team.batting_order[0]
        return next_batter

    def enact(self):
        while self.outs < 3:
            AtBat(frame=self)
            if self.game.trace:
                print "\n{}. {} outs. Score is {}-{}.\n".format(
                    self.at_bats[-1].result, self.outs, self.game.away_team.runs, self.game.home_team.runs
                )
            # raw_input("")

    def review(self):
        # TODO substitution will change how this should be done
        self.pitching_team.pitcher.career.statistics.innings_pitched.append(self)
        temp_lob = []
        for baserunner in self.baserunners:
            self.batting_team.left_on_base.append(baserunner)
            temp_lob.append(baserunner)
        if type(self.at_bats[-1].result) is FieldersChoice:
            self.batting_team.left_on_base.append(self.at_bats[-1].batter)
            temp_lob.append(self.at_bats[-1].batter)
        for _ in temp_lob:
            self.at_bats[-1].batter.composure -= 0.05
        if self.game.trace:
            print "{} left these players on base: {}\n".format(
                self.batting_team.city.name, ', '.join(b.person.last_name for b in temp_lob)
            )

    @property
    def baserunners(self):
        baserunners = []
        # Note: they must be appended in this order so that baserunners
        # can check if preceding runners are advancing before they
        # attempt to advance themselves
        if self.on_third:
            baserunners.append(self.on_third)
        if self.on_second:
            baserunners.append(self.on_second)
        if self.on_first:
            baserunners.append(self.on_first)
        return baserunners

    @property
    def bases_loaded(self):
        if self.on_first and self.on_second and self.on_third:
            return True
        else:
            return False


class AtBat(object):

    def __init__(self, frame):
        self.frame = frame
        self.frame.at_bats.append(self)
        self.game = frame.game
        self.batter = frame.get_next_batter()
        frame.batting_team.batter = self.batter
        self.pitcher = frame.pitching_team.pitcher
        self.catcher = frame.pitching_team.catcher
        self.fielders = frame.pitching_team.fielders
        self.umpire = self.game.umpire
        self.pitches = []
        self.pitch_interims = []
        # Blank count to start
        self.balls = self.strikes = 0
        self.count = 00
        # Modified below
        self.playing_action = None
        self.outs = []  # Kept track of as a listener for double- and triple plays
        self.resolved = False
        self.result = None
        self.run_queue = []  # Runs that may be counted if a third out isn't recorded

        if self.game.trace:
            print "1B: {}, 2B: {}, 3B: {}, AB: {}".format(frame.on_first, frame.on_second, frame.on_third, self.batter)

        if not self.game.radio_announcer:
            self.enact()
        if self.game.radio_announcer:
            self.game.radio_announcer.call_at_bat(at_bat=self)  # This will enact the at bat midway

    def enact(self):
        # TODO substitutions will change where this should be done
        assert not self.resolved, "Call to enact() of already resolved AtBat."
        while not self.resolved:
            self.playing_action = None  # Don't retain prior playing action
            # Players get in position, pitcher decides his pitch
            PitchInterim(at_bat=self)
            # The pitch...
            pitch = self.pitcher.pitch(at_bat=self)
            if not pitch.bean:
                self.batter.decide_whether_to_swing(pitch)
                if not self.batter.will_swing:
                    # Catcher attempts to receive pitch
                    pitch.caught = self.catcher.receive_pitch(pitch)  # TODO wild pitches, passed balls
                    # Umpire makes his call
                    pitch.call = pitch.would_be_call
                    if pitch.call == "Strike":
                        Strike(pitch=pitch, looking=True)
                    elif pitch.call == "Ball":
                        Ball(pitch=pitch)
                # The swing...
                elif self.batter.will_swing:
                    self.batter.decide_swing(pitch)
                    swing = self.batter.swing(pitch)
                    if not swing.contact:
                        # Swing and a miss!
                        Strike(pitch=pitch, looking=False)
                    elif swing.foul_tip:
                        foul_tip = swing.result
                        if self.catcher.receive_foul_tip():
                            Strike(pitch=pitch, looking=False, foul_tip=foul_tip)
                        else:
                            FoulBall(batted_ball=foul_tip)
                    elif swing.contact:
                        self.playing_action = PlayingAction(batted_ball=swing.result)
                        self.playing_action.enact()
                        if self.batter.safely_on_base:
                            self.resolved = True
        if self.playing_action:
            self.review()

    def review(self):
        # Score any runs that remain in the run queue -- these are runs whose being scored
        # depended on the at bat not ending with a fly out or force out
        for run in self.run_queue:
            run.dequeue()
        # Check for whether a hit was made; if one was, instantiate the appropriate outcome object
        # [Note: if the batter-runner was part of a call at a base, PlayAtBaseCall.__init__() will
        # score the hit -- in those cases it is precluded here by self.result having already been
        # attributed by the scored hit]
        if not self.result and self.batter.base_reached_on_hit:
            if self.batter.base_reached_on_hit == "1B":
                Single(playing_action=self.playing_action, call=None)
            elif self.batter.base_reached_on_hit == "2B":
                Double(playing_action=self.playing_action, call=None)
            elif self.batter.base_reached_on_hit == "3B":
                Triple(playing_action=self.playing_action, call=None)
            elif self.batter.base_reached_on_hit == "H":
                HomeRun(batted_ball=self.playing_action.batted_ball, call=None, inside_the_park=True)
        # Next, check for whether a double- or triple play was turned -- if one was, instantiate
        # the appropriate outcome object
        if len(self.outs) == 2:
            DoublePlay(at_bat=self, outs=self.outs)
        elif len(self.outs) == 3:
            TriplePlay(at_bat=self, outs=self.outs)
        # Lastly, survey for which bases are now occupied and by whom
        if self.playing_action.running_to_third and self.playing_action.running_to_third.safely_on_base:
            self.frame.on_third = self.playing_action.running_to_third
        elif self.playing_action.retreating_to_third and self.playing_action.retreating_to_third.safely_on_base:
            self.frame.on_third = self.playing_action.retreating_to_third
        else:
            self.frame.on_third = None
        if self.playing_action.running_to_second and self.playing_action.running_to_second.safely_on_base:
            self.frame.on_second = self.playing_action.running_to_second
        elif self.playing_action.retreating_to_second and self.playing_action.retreating_to_second.safely_on_base:
            self.frame.on_second = self.playing_action.retreating_to_second
        else:
            self.frame.on_second = None
        if self.playing_action.running_to_first and self.playing_action.running_to_first.safely_on_base:
            self.frame.on_first = self.playing_action.running_to_first
        elif self.playing_action.retreating_to_first and self.playing_action.retreating_to_first.safely_on_base:
            self.frame.on_first = self.playing_action.retreating_to_first
        else:
            self.frame.on_first = None

    def draw_playing_field(self):
        import turtle
        self.turtle = turtle
        turtle.setworldcoordinates(-450, -450, 450, 450)
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
        turtle.dot(3)
        turtle.goto(63.5, 63.5)
        turtle.dot(3)
        turtle.goto(0, 127)
        turtle.dot(3)
        turtle.goto(-63.5, 63.5)
        turtle.dot(3)
        turtle.goto(0, 0)
        turtle.goto(226, 226)
        turtle.goto(0, 0)
        turtle.goto(-226, 226)
        turtle.penup()
        for f in self.fielders:
            f.get_in_position(at_bat=self)
            turtle.goto(f.location)
            turtle.pendown()
            turtle.color("purple")
            turtle.dot(2)
            turtle.penup()
        for b in self.frame.baserunners:
            b.get_in_position(at_bat=self)
            turtle.goto(b.location)
            turtle.pendown()
            turtle.color("blue")
            turtle.dot(2)
            turtle.penup()
        turtle.update()

    def new_test(self, pitch_coords=None, count=32, power=0.8, uf=None):
        import time
        self.turtle.clearscreen()
        self.draw_playing_field()
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
        contact = False
        while not contact:
            for fielder in self.fielders:
                fielder.get_in_position(at_bat=self)
            p.decide_pitch(at_bat=self)
            if pitch_coords:
                p.intended_x, p.intended_y = pitch_coords
            pitch = p.pitch(at_bat=self)
            b.decide_whether_to_swing(pitch)
            if not b.will_swing:
                pitch.call = pitch.would_be_call
            elif b.will_swing:
                b.decide_swing(pitch)
                b.power = power
                if uf:
                    b.incline = uf
                swing = b.swing(pitch)
                contact = swing.contact
                if contact:
                    print "\n\tThe ball is hit!\n"
                    bb = swing.result
                    turtle = self.turtle
                    turtle.penup()
                    time_since_contact = 0.0
                    for fielder in self.fielders:
                        fielder.decide_immediate_goal(batted_ball=bb)
                    for i in xrange(4):
                        time_since_contact += 0.1
                        bb.batter.baserun(bb)
                        print "Time: {}".format(time_since_contact)
                        bb.act(time_since_contact=time_since_contact)
                        turtle.goto(bb.location)
                        if bb.height < 8.5:
                            turtle.color("green")
                        else:
                            turtle.color("red")
                        turtle.dot(2)
                        turtle.update()
                        print '\n'
                        if bb.height <= 0 and not bb.stopped:
                            print "\t\tBOUNCE"
                        time.sleep(0.03)
                    fielding_chance_resolved = False
                    while not fielding_chance_resolved:
                        time_since_contact += 0.1
                        bb.batter.baserun(bb)
                        print "Time: {}".format(time_since_contact)
                        bb.act(time_since_contact=time_since_contact)
                        print "Height: {}".format(round(bb.height, 2))
                        print "Vel: {}".format(round(bb.speed, 2))
                        print "Baserunner %: {}".format(round(bb.batter.percent_to_base, 2))
                        turtle.goto(bb.location)
                        if bb.height < 8.5:
                            turtle.color("green")
                        else:
                            turtle.color("red")
                        if bb.height <= 0 and not bb.stopped:
                            print "\t\tBOUNCE"
                        turtle.dot(2)
                        turtle.update()
                        for f in self.fielders:
                            f.act(batted_ball=bb)
                            turtle.goto(f.location)
                            if not f.at_goal:
                                turtle.color("purple")
                            else:
                                turtle.color("orange")
                            turtle.dot(2)
                            turtle.update()
                        print '\n'
                        time.sleep(0.03)
                        # Check if ball has left playing field
                        if bb.left_playing_field:
                            print "\nBall has left the playing field."
                            fielding_chance_resolved = True
                        # Check if ball has landed foul
                        elif bb.landed_foul:
                            print "\nFoul ball."
                            fielding_chance_resolved = True
                        # Check if ball rolled foul
                        elif bb.landed and bb.in_foul_territory:
                            if bb.passed_first_or_third_base or bb.touched_by_fielder:
                                print "\nFoul ball."
                                fielding_chance_resolved = True
                        # Potentially simulate a fielding attempt
                        elif (bb.obligated_fielder.at_goal and
                                bb.location == bb.obligated_fielder.immediate_goal[:2]):
                            bb.obligated_fielder.field_ball(batted_ball=bb)
                            print "Difficulty: {}".format(round(bb.fielding_difficulty, 3))
                            if bb.fielded_by:
                                if not bb.landed:
                                    print "\nOut! Caught in flight."
                                    fielding_chance_resolved = True
                                else:
                                    print "\nGround ball cleanly fielded."
                                    fielding_chance_resolved = True
                                    bb.obligated_fielder.decide_throw_or_on_foot_approach_to_target(bb)
                                    throw = bb.obligated_fielder.throw()
                                    while not throw.reached_target and not bb.batter.safely_on_base:
                                        time_since_contact += 0.1
                                        bb.time_since_contact += 0.1
                                        print "Time: {}".format(time_since_contact)
                                        bb.batter.baserun(bb)
                                        print "Baserunner %: {}".format(round(bb.batter.percent_to_base, 2))
                                        throw.move()
                                        print "Throw %: {}".format(round(throw.percent_to_target, 2))
                                        if bb.batter.safely_on_base and throw.reached_target:
                                            print "Tie goes to the runner - Safe!"
                                        elif bb.batter.safely_on_base:
                                            print "Safe!"
                                        elif throw.reached_target:
                                            print "Force out!"
                            elif not bb.fielded:
                                print "ERROR!"
                                fielding_chance_resolved = True
                    return bb