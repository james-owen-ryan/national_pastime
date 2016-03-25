import random
from people.event import Event
from outcome import Strike, Ball, FoulBall, Single, Double, Triple, HomeRun, Run, DoublePlay, TriplePlay, FieldersChoice
from playing_action import PitchInterim, PlayingAction
from printout import compose_box_score as COMPOSE_BOX_SCORE


class Game(Event):
    """A baseball game played in a baseball cosmos."""

    def __init__(self, home_team, away_team, ballpark=None, league=None, rules=None,
                 radio=False, trace=False, debug=False):
        """Initialize a Game object."""
        self.cosmos = home_team.city.cosmos
        super(Game, self).__init__(cosmos=self.cosmos)  # This will collect metadata about the date, etc.
        self.home_team = home_team
        self.away_team = away_team
        # If it's a league game, record the game
        if home_team.league is away_team.league:
            home_team.season.games.append(self)
            away_team.season.games.append(self)
        # Turn debug or trace parameters on or off
        self.debug = debug
        self.trace = trace
        # Determine the salience of this game
        self.salience = self._init_determine_salience()
        # Identify the audience of people that have come to the ballpark for the game
        self.audience = self._init_attract_audience()
        # Determine ballpark, league, rules of play, and umpire
        self.ballpark = home_team.ballpark if not ballpark else ballpark  # In case of neutral field
        self.field = self.ballpark.field
        self.league = home_team.league if not league else league  # In case of non-league play
        self.rules = self.league.classification.rules if not rules else rules  # In case of weird rules jazz
        self.umpire = self.league.assign_umpire()
        # Prepare for game
        self.score = [0, 0]  # [away_team_score, home_team_score]
        self.winner = None
        self.loser = None
        self.innings = []
        self.left_on_base = {home_team: [], away_team: []}
        self.player_composures_before = {}
        for player in away_team.players | home_team.players:
            self.player_composures_before[player] = player.person.mood.composure
        # Prepare the radio broadcast, if applicable (this is my testbed for situated
        # procedural sports commentary)
        if radio:
            self.radio_announcer = random.choice(list(self.ballpark.city.residents))
        else:
            self.radio_announcer = None
        if self.radio_announcer:
            self.radio_announcer.call_pregame(game=self)
        # Play the game
        self.transpire()
        # Save the box score
        self.box_score = COMPOSE_BOX_SCORE(game=self)
        # Potentially print the box score
        if self.trace:
            print self.box_score
        print "{} defeated {} {}-{}".format(self.winner.name, self.loser.name, max(self.score), min(self.score))

    def __str__(self):
        """Return string representation."""
        return "{away_team} at {home_team}, {date}".format(
            away_team=self.away_team.name,
            home_team=self.home_team.name,
            date=self.date
        )

    def _init_determine_salience(self):
        """Determine the salience of this game.

        More salient games will be attended by more people, and will have greater ramifications
        on player composure, confidence, etc.
        """
        return 1.0

    def _init_attract_audience(self):
        """Attract an audience of people to come to the ballpark for the game."""
        # TODO USE SALIENCE HERE
        pass

    def transpire(self):
        """Have this game be played."""
        # Play nine innings
        for inning_number in xrange(1, 10):
            Inning(game=self, number=inning_number)
        # If the score is tied, play extra innings until it's no longer tied
        inning_number = 9
        while self.score[0] == self.score[1]:
            inning_number += 1
            Inning(game=self, number=inning_number)
        # Determine the winner
        self.winner = self.home_team if self.score[1] > self.score[0] else self.away_team
        self.loser = self.away_team if self.home_team is self.winner else self.home_team
        # Effect the consequences of this game
        self._evolve_player_confidence_and_composure()

    def _evolve_player_confidence_and_composure(self):
        """Effect the consequences of this game."""
        config = self.cosmos.config
        # Update player confidences and composures  TODO personnel as well, especially umpire, manager
        for player in self.away_team.players | self.home_team.players:
            confidence_before = player.person.personality.confidence
            composure_before = player.person.mood.composure
            # Evolve confidence
            composure_confidence_diff = player.person.mood.composure-player.person.personality.confidence
            change_to_confidence = config.change_to_confidence_after_game(
                composure_confidence_diff=composure_confidence_diff, game_salience=self.salience
            )
            player.person.personality.confidence += change_to_confidence
            # Evolve composure
            change_to_composure = config.change_to_composure_after_game(
                composure_confidence_diff=composure_confidence_diff, game_salience=self.salience
            )
            player.person.mood.composure -= change_to_composure
            # Clamp their new composure
            player.person.mood.composure = max(0.5, min(player.person.mood.composure, 1.5))
            if self.trace:
                print "{}'s confidence changed by {}; his composure reverted from {} to {}".format(
                    player.person.name, round(player.person.personality.confidence-confidence_before, 4),
                    round(composure_before, 2),
                    round(player.person.mood.composure, 2)
                )


class Inning(object):
    """An inning in a baseball game."""

    def __init__(self, game, number):
        """Initialize an Inning object."""
        self.game = game
        self.game.innings.append(self)
        self.number = number
        self.frames = []
        # Modified by self._transpire()
        self.top = None
        self.bottom = None
        # Play out the inning
        self._transpire()

    def _transpire(self):
        """Have the inning be played out."""
        self.top = Frame(inning=self, top=True)
        game_is_over = self.number >= 9 and self.game.score[0] != self.game.score[1]
        if not game_is_over:
            self.bottom = Frame(inning=self, bottom=True)


class Frame(object):
    """A frame in an inning; a half-inning."""

    def __init__(self, inning, top=False, middle=False, bottom=False):
        """Initialize a Frame object."""
        # Set attributes
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
        # Prepare attributes that will hold the players currently on base
        self.on_first = None
        self.on_second = None
        self.on_third = None
        # Prepare other attributes
        self.runs = 0  # Runs batting team has scored this inning
        self.outs = 0
        self.at_bats = []  # Appended to by AtBat.__init__()
        if self.game.trace:
            print "\n\t\t*****  {}  *****\n\n".format(self)
        if self.game.radio_announcer:
            self.game.radio_announcer.call_new_frame(frame=self)
        self._transpire()
        self._review()

    def __str__(self):
        """Return string representation."""
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
        return "{half} of the {nth} inning -- {batting_team} up to bat".format(
            half=self.half,
            nth=self.inning.number if self.inning.number not in ordinals else ordinals[self.inning.number],
            batting_team=self.game.away_team if self.half == 'Top' else self.game.home_team
        )

    def _transpire(self):
        """Play out this frame."""
        while self.outs < 3:
            AtBat(frame=self)
            if self.game.trace:
                print "\n{}. {} outs. Score is {}-{}.\n".format(
                    self.at_bats[-1].result, self.outs, self.game.away_team.runs, self.game.home_team.runs
                )

    def _review(self):
        """Review this frame to effect any outcomes and record statistics."""
        # TODO substitution will change how this should be done
        self.pitching_team.roster.pitcher.career.statistics.innings_pitched.append(self)
        left_on_base_this_frame = []
        for baserunner in self.baserunners:
            self.game.left_on_base[self.batting_team].append(baserunner)
            left_on_base_this_frame.append(baserunner)
        if type(self.at_bats[-1].result) is FieldersChoice:
            self.game.left_on_base[self.batting_team].append(self.at_bats[-1].batter)
            left_on_base_this_frame.append(self.at_bats[-1].batter)
        # Diminish the batter's composure for each of the baserunners they stranded
        number_of_baserunners_stranded = len(left_on_base_this_frame)
        composure_penalty = self.game.cosmos.config.batter_penalty_for_stranding_baserunners(
            n_baserunners=number_of_baserunners_stranded
        )
        self.at_bats[-1].batter.person.mood.composure -= composure_penalty
        if self.game.trace:
            print "{} left these players on base: {}\n".format(
                self.batting_team.city.name, ', '.join(b.person.last_name for b in left_on_base_this_frame)
            )

    @property
    def baserunners(self):
        """Return the current baserunners.

        Baserunners must be appended in this order so that they can check if preceding runners
        are advancing before they attempt to advance themselves.
        """
        baserunners = []
        if self.on_third:
            baserunners.append(self.on_third)
        if self.on_second:
            baserunners.append(self.on_second)
        if self.on_first:
            baserunners.append(self.on_first)
        return baserunners

    @property
    def bases_loaded(self):
        """Return whether the bases are currently loaded."""
        return True if self.on_first and self.on_second and self.on_third else False


class AtBat(object):
    """An at-bat in a frame."""

    def __init__(self, frame):
        """Initialize an AtBat object."""
        self.game = frame.game
        self.frame = frame
        frame.at_bats.append(self)
        # Set attributes for record keeping
        self.pitcher = frame.pitching_team.roster.pitcher
        self.catcher = frame.pitching_team.roster.catcher
        self.fielders = list(frame.pitching_team.roster.fielders)
        self.umpire = self.game.umpire
        # Summon the next batter to the plate
        self.batter = frame.batting_team.roster.next_batter()
        # Prepare attributes
        self.pitches = []
        self.pitch_interims = []
        self.balls = 0
        self.strikes = 0
        self.count = 00  # See playing_action.PitchInterim for info on how counts are represented
        self.playing_action = None  # This gets set by _transpire(), as appropriate
        self.outs = []  # Keep track of this so that we can listen for double- and triple plays
        self.resolved = False
        self.result = None
        self.run_queue = []  # Potential runs; will be counted only if a third out isn't recorded during the play
        if self.game.trace:
            print "1B: {}, 2B: {}, 3B: {}, AB: {}".format(frame.on_first, frame.on_second, frame.on_third, self.batter)
        if not self.game.radio_announcer:
            self._transpire()
        if self.game.radio_announcer:
            self.game.radio_announcer.call_at_bat(at_bat=self)  # This will _transpire the at-bat midway

    def _transpire(self):
        """Play out the at-bat."""
        # TODO substitutions will change where this should be done
        assert not self.resolved, "Call to _transpire() of already resolved AtBat."
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
                # ...the swing...
                elif self.batter.will_swing:
                    self.batter.decide_swing(pitch)
                    swing = self.batter.swing(pitch)
                    if not swing.contact:
                        # ...swing and a miss!
                        Strike(pitch=pitch, looking=False)
                    elif swing.foul_tip:
                        # ...foul tip
                        foul_tip = swing.result
                        if self.catcher.receive_foul_tip():
                            Strike(pitch=pitch, looking=False, foul_tip=foul_tip)
                        else:
                            # ...foul ball
                            FoulBall(batted_ball=foul_tip)
                    elif swing.contact:
                        # ...the ball is hit!
                        self.playing_action = PlayingAction(batted_ball=swing.result)
                        self.playing_action.enact()
                        if self.batter.safely_on_base:
                            self.resolved = True
        if self.playing_action:
            self._review()

    def _review(self):
        """Review the at-bat to effect its outcomes and record statistics."""
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