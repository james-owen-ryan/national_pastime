# TODO  IT MIGHT BE COOL TO UNIFY EQUIVALENT ROSTERS, SO THAT YOU CAN CHECK
# TODO  ROSTER.GAMES ACROSS POTENTIALLY DIFFERENT TEAMS (E.G., A HIGH SCHOOL TEAM
# TODO  THAT BANDS TOGETHER AGAIN AS A MINOR-LEAGUE TEAM, OR A MAJOR-LEAGUE TEAM
# TODO  THAT PLAYS AN INFORMAL GAME IN A PARK, ETC.)


class Roster(object):
    """The roster of a baseball team."""

    def __init__(self, lineup, bullpen=None, bench=None):
        """Initialize a Roster object.

        @param lineup: A tuple in the following order: (P, C, 1B, 2B, 3B, SS, LF, CF, RF).
        """
        # Set personnel attributes
        self.players = set(lineup) | set(bullpen) | set(bench)
        self.lineup = lineup
        self.pitcher, self.catcher = self.battery = lineup[:2]
        self.fielders = lineup
        self.bullpen = bullpen
        self.bench = bench
        self.batting_order = list(self.lineup)  # TODO make rational
        self.batter = None
        # Prepare attributes
        self.games = []  # Number of games this roster has played

    def next_batter(self):
        """Return the next batter."""
        try:
            last_batter_index = self.batting_order.index(self.batter)
            self.batter = self.batting_order[last_batter_index+1]
        except ValueError:  # Game is just starting; send out your first batter
            self.batter = self.batting_order[0]
        except IndexError:  # Reached end of the order; start back to top
            self.batter = self.batting_order[0]
        return self.batter