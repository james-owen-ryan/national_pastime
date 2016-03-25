import random
import datetime


class LeagueSchedule(object):
    """A schedule for a baseball league's season."""

    def __init__(self, league):
        """Initialize a Schedule object."""
        self.league = league
        self.year = league.cosmos.year
        # Set a date of opening day
        opening_day = [self.league.cosmos.year] + self.league.cosmos.config.determine_opening_day()
        opening_day_ordinal_date = datetime.date(*opening_day).toordinal()
        self.opening_day = opening_day_ordinal_date
        # Set a date for the regular season to end
        regular_season_terminus = (
            [self.league.cosmos.year] + self.league.cosmos.config.determine_regular_season_terminus()
        )
        regular_season_terminus_ordinal_date = datetime.date(*regular_season_terminus).toordinal()
        self.regular_season_terminus = regular_season_terminus_ordinal_date
        # Determine the targeted number of games each team will be scheduled to play
        targeted_number_of_games_per_team = league.cosmos.config.number_of_games_per_season(year=self.year)
        # Use that to determine how many times each team will play each opponent
        self.number_of_games_per_opponent = targeted_number_of_games_per_team / (len(league.teams)-1)
        self.number_of_games_per_team = self.number_of_games_per_opponent * (len(league.teams)-1)
        # Prepare team schedules for each team
        for team in league.teams:
            team.season.schedule = TeamSchedule(team=team)
        # Schedule the games
        self._init_schedule_games()

    def _init_schedule_games(self):
        """Schedule games for this season."""
        # Prepare N rounds of series slots, where N is the number of times each
        # team will play each of their opponents, which we determined in __int__()
        rounds_of_series_slots = self._prepare_all_rounds_of_series_slots()
        # Determine a start date (ordinal date) for each series slot
        start_dates_for_the_series_slots = self._determine_series_slot_start_dates(
            rounds_of_series_slots=rounds_of_series_slots
        )
        # Determine how many games will be played in each series (such that each
        # team plays the same number of games against each opponent)
        number_of_games_in_each_series_for_team_pair = self._determine_the_number_of_games_for_each_series(
            number_of_series=len(rounds_of_series_slots)
        )
        # Lastly, shuffle the order of the rounds (otherwise every team will alternate
        # home and away series, which isn't really realistic)
        random.shuffle(rounds_of_series_slots)
        # Instantiate series objects for all the series that will be played this year
        for round_of_series_slots in rounds_of_series_slots:
            for series_slot in round_of_series_slots:
                series_slot_start_date = start_dates_for_the_series_slots[0]
                start_dates_for_the_series_slots = start_dates_for_the_series_slots[1:]
                try:
                    series_slot_end_date = start_dates_for_the_series_slots[0]
                except IndexError:
                    # We've reached the end of the last series slot, so here we attribute
                    # the terminus of the regular season
                    series_slot_end_date = self.regular_season_terminus
                for away_team, home_team in series_slot:
                    key = tuple(sorted([home_team, away_team], key=lambda t: t.name))
                    # Since we don't care about the actual ordering of the series lengths we've decided,
                    # we can just pop off the list specifying them (i.e., consume it in reverse order)
                    number_of_games_in_this_series = number_of_games_in_each_series_for_team_pair[key].pop()
                    Series(
                        home_team=home_team, away_team=away_team,
                        number_of_games=number_of_games_in_this_series,
                        date_range=(series_slot_start_date, series_slot_end_date)
                    )

    def _prepare_all_rounds_of_series_slots(self):
        """Prepare all the needed rounds of series slots."""
        rounds_of_series_slots = []
        number_of_rounds_we_need = self.number_of_games_per_opponent / 3  # Trust me
        while number_of_rounds_we_need > 0:
            # I don't fully get this code -- I just copied it from StackOverflow; it
            # works lol
            if number_of_rounds_we_need == 1:
                next_round_of_series_slots = list(self._produce_rounds_of_series_slots(number_of_rounds=1))
                rounds_of_series_slots.append(next_round_of_series_slots)
                number_of_rounds_we_need -= 1
            else:
                # Generate two rounds such that each team visits and hosts each other
                # team exactly once across the two rounds
                next_two_rounds_of_series_slots = list(self._produce_rounds_of_series_slots(number_of_rounds=2))
                # Split the agglomerated list into its constituent rounds
                index_between_the_rounds = len(next_two_rounds_of_series_slots) / 2
                first_of_the_two_series_rounds = next_two_rounds_of_series_slots[:index_between_the_rounds]
                second_of_the_two_series_round = next_two_rounds_of_series_slots[index_between_the_rounds:]
                rounds_of_series_slots.append(first_of_the_two_series_rounds)
                rounds_of_series_slots.append(second_of_the_two_series_round)
                number_of_rounds_we_need -= 2
        return rounds_of_series_slots

    def _produce_rounds_of_series_slots(self, number_of_rounds, force_home_series_for=None):
        """Return a round of series slots.

        A series slot is a list of (away_team, home_team) match-ups, and a round of
        series slots include exactly one match-up between each pair of teams in the
        league (with each team having an equal number of home games across the round).

        @param number_of_rounds: If 2 is passed for this, a pair of rounds will be returned
                                 such that each team plays exactly one series at each other
                                 team's home ballpark (and thus hosts each team exactly once
                                 as well).
        """
        assert len(self.league.teams) % 2 == 0, (
            "{} HAS AN ODD NUMBER OF TEAMS -- THAT DOESN'T WORK".format(self.league.name)
        )
        # Randomly shuffle the teams
        teams = list(self.league.teams)
        random.shuffle(teams)
        # If we want to force a home series this round for a team (e.g., to give a
        # certain team the honor of hosting Opening Day, which in real life was a
        # tradition for the Reds in honor of them being the oldest team, or to
        # christen a new ballpark), we place them at the back of the list, since
        # index[-1] is always guaranteed to be awarded a home series
        if force_home_series_for:
            teams.remove(force_home_series_for)
            teams.append(force_home_series_for)
        # Carry out this procedure that I copied from StackOverflow
        sets = None if number_of_rounds == 1 else len(self.league.teams)*2-2
        count = len(teams)
        sets = sets or (count-1)
        half = count / 2
        for turn in range(sets):
            left = teams[:half]
            right = teams[count-half-1+1:][::-1]
            pairings = zip(left, right)
            if turn % 2 == 1:
                pairings = [(y, x) for (x, y) in pairings]
            teams.insert(1, teams.pop())
            yield pairings

    def _determine_series_slot_start_dates(self, rounds_of_series_slots):
        """Determine a start date for each of the rounds."""
        # Determine offtime windows (how many days off) between all the series slots
        number_of_off_days_between_series_slots = self._determine_number_of_off_days_between_series_slots(
            rounds_of_series_slots=rounds_of_series_slots
        )
        # Schedule these; we already know that the first round will start on
        # opening day, so let's start with that
        series_slot_start_dates = [self.opening_day]
        # Now iterate through the rest of the rounds to set ordinal dates for the
        # start of each one
        for number_of_off_days_between_these_two_slots in number_of_off_days_between_series_slots:
            start_date_of_last_slot = series_slot_start_dates[-1]
            # Add four days to play the games for this round, and also add number
            # of off days that we already determined
            start_date_of_this_slot = start_date_of_last_slot + 4 + number_of_off_days_between_these_two_slots
            series_slot_start_dates.append(start_date_of_this_slot)
        return series_slot_start_dates

    def _determine_number_of_off_days_between_series_slots(self, rounds_of_series_slots):
        """Return a list of windows of offtime (in number of days) between the series rounds."""
        # Determine how many days will be in this regular season
        number_of_days_in_the_regular_season = self.regular_season_terminus-self.opening_day
        # Determine how many days must be set aside for games
        max_number_of_games_in_a_series = 4
        number_of_days_to_dedicate_to_games = (
            max_number_of_games_in_a_series * sum(len(r) for r in rounds_of_series_slots)
        )
        # Determine how much room there is for off days
        days_of_off_time = number_of_days_in_the_regular_season - number_of_days_to_dedicate_to_games
        # Determine a base number of off days between series slots (which could be zero)
        number_of_series_slots = sum(len(round_of_slots) for round_of_slots in rounds_of_series_slots)
        base_number_of_days_between_series_slots = days_of_off_time / number_of_series_slots
        # Prepare a list using this base number
        number_of_windows = number_of_series_slots - 1
        number_of_off_days_between_slots = [base_number_of_days_between_series_slots for _ in xrange(number_of_windows)]
        # Because we used integer division, we probably have a few extra off days that
        # we can distribute randomly across the round interstices
        while sum(number_of_off_days_between_slots) < days_of_off_time:
            index_of_random_window = random.randint(0, number_of_windows-1)
            number_of_off_days_between_slots[index_of_random_window] += 1
        return number_of_off_days_between_slots

    def _determine_the_number_of_games_for_each_series(self, number_of_series):
        """Return a dictionary specifying how many games will be played for each {team1, team2} set."""
        number_of_games_in_each_series_for_team_pair = {}
        for team in self.league.teams:
            for other_team in self.league.teams:
                if team is not other_team:
                    key = tuple(sorted([team, other_team], key=lambda t: t.name))
                    if key not in number_of_games_in_each_series_for_team_pair:
                        number_of_games_in_each_series_for_team_pair[key] = (
                            self._determine_number_of_games_for_each_series_between_two_teams(
                                total_number_of_games=self.number_of_games_per_opponent,
                                number_of_series=number_of_series
                            )
                        )
        return number_of_games_in_each_series_for_team_pair

    @staticmethod
    def _determine_number_of_games_for_each_series_between_two_teams(total_number_of_games, number_of_series):
        """Determine the number of that games that will be played for each series
        that is being scheduled between these two teams.
        """
        # First, start with three games per series
        number_of_games_for_each_series = [3 for _ in xrange(number_of_series)]
        # While the sum thereof is not equal to the total number of games that we need these
        # teams to play against one another, turn a three-game series into a four-game series
        while sum(number_of_games_for_each_series) != total_number_of_games:
            indices_of_three_game_series = [
                i for i in xrange(number_of_series) if number_of_games_for_each_series[i] == 3
            ]
            random_index = random.choice(indices_of_three_game_series)
            # Turn the randomly selected three-game series into a four-game series
            number_of_games_for_each_series[random_index] += 1
        return number_of_games_for_each_series


class TeamSchedule(object):
    """A schedule for a baseball team's season."""

    def __init__(self, team):
        """Initialize a TeamSchedule object."""
        self.team = team
        self.series = []
        self.upcoming_series = []  # This list gets consumed as the season progresses

    @property
    def next_game(self):
        """Return the date and location of the next scheduled game as a tuple (ordinal_date, timestep, city)."""
        if self.upcoming_series:
            next_series = self.upcoming_series[0]
            number_of_games_already_played_in_that_series = len(next_series.games)
            date_of_next_game, timestep_of_next_game = (
                next_series.dates_scheduled[number_of_games_already_played_in_that_series]
            )
            return date_of_next_game, timestep_of_next_game, next_series.away_team, next_series.home_team
        return None


class Series(object):
    """A series of baseball games between two teams."""

    def __init__(self, home_team, away_team, number_of_games, date_range):
        """Initialize a Series object."""
        self.home_team = home_team
        self.away_team = away_team
        self.games = []  # Will become populated with actual Game objects as they conclude
        self.dates_scheduled = self._schedule_each_game(number_of_games=number_of_games, date_range=date_range)
        for team in home_team, away_team:
            team.season.schedule.series.append(self)
            team.season.schedule.upcoming_series.append(self)

    def _schedule_each_game(self, number_of_games, date_range):
        """Schedule each game in this series, i.e., set an ordinal date on which each will be played."""
        cosmos = self.home_team.cosmos
        # Compile all the available days
        earliest_start_date, latest_end_date = date_range
        # Decide whether there will be a doubleheader in this series, which tells us
        # how many days we need to take up for the series
        doubleheader_in_this_series = random.random() < cosmos.config.chance_of_a_doubleheader(year=cosmos.year)
        number_of_days_needed = number_of_games if not doubleheader_in_this_series else number_of_games-1
        # Determine which date the series will start on
        dates_series_could_this_start_on = list(xrange(earliest_start_date, latest_end_date-number_of_days_needed+1))
        # Randomly pick a date to start on  TODO TRAVEL CONSIDERATIONS ONCE YOU HAVE TRAVEL SYSTEM
        chosen_start_date = random.choice(dates_series_could_this_start_on)
        # Schedule the dates  TODO NIGHT BASEBALL
        if doubleheader_in_this_series:
            dates_scheduled = [(chosen_start_date, 'day'), (chosen_start_date, 'day')]  # A true day doubleheader :)
            number_of_days_needed -= 2
            next_date = chosen_start_date + 1
        else:
            dates_scheduled = []
            next_date = chosen_start_date
        while number_of_days_needed:
            dates_scheduled.append((next_date, 'day'))
            number_of_days_needed -= 1
        return dates_scheduled