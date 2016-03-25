def compose_box_score(game):
    box_score = ''
    box_score += '\n\n'
    box_score += '\t\t' + '   '.join(str(i+1) for i in xrange(len(game.innings)))
    box_score += '\t\t__________________________________'
    if len(game.away_team.city.name) >= 8:
        tabs_needed = '\t'
    else:
        tabs_needed = '\t\t'
    box_score += (game.away_team.city.name + tabs_needed +
           '   '.join(str(inning.top.runs) for inning in game.innings) +
           '\t' + str(game.score[0]))
    box_score += ''
    if len(game.home_team.city.name) >= 8:
        tabs_needed = '\t'
    else:
        tabs_needed = '\t\t'
    if game.innings[-1].bottom:
        box_score += (game.home_team.city.name + tabs_needed +
               '   '.join(str(inning.bottom.runs) for inning in game.innings) +
               '\t' + str(game.score[1]))
    else:  # Home team didn't need to bat in bottom of the ninth inning
        box_score += (game.home_team.city.name + tabs_needed +
               '   '.join(str(inning.bottom.runs) for inning in game.innings[:-1]) +
               '   -\t' + str(game.score[1]))
    box_score += '\n\n\t {}\n'.format(game.away_team.name)
    box_score += '\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
    for p in game.away_team.players:
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
        box_score += "{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), 
            len(p.career.statistics.runs),
            len(p.career.statistics.hits),
            len(p.career.statistics.doubles), 
            len(p.career.statistics.triples), len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
            len(p.career.statistics.batting_walks), len(p.career.statistics.batting_strikeouts), len(p.career.statistics.stolen_bases), batting_avg
        )
    box_score += '\n\n\t {}\n'.format(game.home_team.name)
    box_score += '\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
    for p in game.home_team.players:
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
        box_score += "{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), len(p.career.statistics.runs),
            len(p.career.statistics.hits),
            len(p.career.statistics.doubles), len(p.career.statistics.triples), 
            len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
            len(p.career.statistics.batting_walks), 
            len(p.career.statistics.batting_strikeouts), 
            len(p.career.statistics.stolen_bases), batting_avg
        )
    return box_score


def compose_league_standings(season):
    standings = ''
    standings += "\n\n\t\t\tFinal {} {} Standings\n\n".format(season.league.cosmos.year, season.league.name)
    team_order = sorted(season.teams, key=lambda t: t.wins, reverse=True)
    for team in team_order:
        standings += "{}: {}-{}".format(team.team.name, team.wins, team.losses)
    return standings


def compose_league_leaders(season):
    league_leaders = ''
    # Batting average leaders
    league_leaders += "\n\n\t\tBATTING AVERAGE LEADERS"
    for player in season.players:
        batting_average = len(player.hits)/float(len(player.at_bats))
        player.yearly_batting_averages[season.cosmos.year] = round(batting_average, 3)
        player.career_hits += player.hits
        player.career_at_bats += player.at_bats
        player.hits = []
        player.at_bats = []
    leaders = list(season.players)
    leaders.sort(key=lambda p: p.yearly_batting_averages[season.cosmos.year], reverse=True)
    # leaders[0].batting_titles.append(self.current_season)
    for i in xrange(9):
        league_leaders += "{}\t{}\t{}\t{}".format(
            i+1, round(leaders[i].yearly_batting_averages[season.cosmos.year], 3),
            leaders[i].name, leaders[i].team.city.name,
        )
    # Home run leaders
    league_leaders += "\n\n\t\tHOME RUN KINGS"
    for player in season.players:
        player.yearly_home_runs[season.cosmos.year] = len(player.home_runs)
        player.career_home_runs += player.home_runs
        player.home_runs = []
    leaders = list(season.players)
    leaders.sort(key=lambda p: p.yearly_home_runs[season.cosmos.year], reverse=True)
    # leaders[0].home_run_titles.append(self.current_season)
    for i in xrange(9):
        league_leaders += "{}\t{}\t{}\t{}".format(
            i+1, leaders[i].yearly_home_runs[season.cosmos.year],
            season.players[i].name, leaders[i].team.city.name,
        )
    return league_leaders