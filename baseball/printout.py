def compose_box_score(game):
    box_score = ''
    box_score += '\n\n'
    box_score += '\n\t\t' + '   '.join(str(i+1) for i in xrange(len(game.innings)))
    box_score += '\n\t\t__________________________________'
    if len(game.away_team.city.name) >= 8:
        tabs_needed = '\t'
    else:
        tabs_needed = '\t\t'
    box_score += ('\n' + game.away_team.city.name + tabs_needed +
           '   '.join(str(inning.top.runs) for inning in game.innings) +
           '\t' + str(game.score[0]))
    box_score += '\n'
    if len(game.home_team.city.name) >= 8:
        tabs_needed = '\t'
    else:
        tabs_needed = '\t\t'
    if game.innings[-1].bottom:
        box_score += ('\n' + game.home_team.city.name + tabs_needed +
               '   '.join(str(inning.bottom.runs) for inning in game.innings) +
               '\t' + str(game.score[1]))
    else:  # Home team didn't need to bat in bottom of the ninth inning
        box_score += ('\n' + game.home_team.city.name + tabs_needed +
               '   '.join(str(inning.bottom.runs) for inning in game.innings[:-1]) +
               '   -\t' + str(game.score[1]))
    box_score += '\n\n\n\t {}\n'.format(game.away_team.name)
    box_score += '\n\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
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
        box_score += "\n{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), 
            len(p.career.statistics.runs),
            len(p.career.statistics.hits),
            len(p.career.statistics.doubles), 
            len(p.career.statistics.triples), len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
            len(p.career.statistics.batting_walks), len(p.career.statistics.batting_strikeouts), len(p.career.statistics.stolen_bases), batting_avg
        )
    box_score += '\n\n\n\t {}\n'.format(game.home_team.name)
    box_score += '\n\t\t\tAB\tR\tH\t2B\t3B\tHR\tRBI\tBB\tSO\tSB\tAVG'
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
        box_score += "\n{}{}{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            p.person.last_name, tabs_needed, p.position, len(p.career.statistics.at_bats), len(p.career.statistics.runs),
            len(p.career.statistics.hits),
            len(p.career.statistics.doubles), len(p.career.statistics.triples), 
            len(p.career.statistics.home_runs), len(p.career.statistics.rbi),
            len(p.career.statistics.batting_walks), 
            len(p.career.statistics.batting_strikeouts), 
            len(p.career.statistics.stolen_bases), batting_avg
        )
    return box_score


def compile_league_standings(season):
    standings = ''
    standings += "\n\n\t\t\tFinal {} {} Standings\n\n".format(season.league.cosmos.year, season.league.name)
    team_order = sorted(season.teams, key=lambda t: len(t.wins), reverse=True)
    for team in team_order:
        standings += "{}: {}-{}\n".format(team.team.name, len(team.wins), len(team.losses))
    return standings


def compile_career_leaders(league):
    career_leaders = ''
    # Batting average leaders
    career_leaders += "\n\n\t\tBATTING AVERAGE LEADERS\n"
    batting_averages = {}
    for player in set(league.players) | league.history.former_players:
        if len(player.career.statistics.hits) > 100:
            batting_average = len(player.career.statistics.hits)/float(len(player.career.statistics.at_bats))
            batting_averages[player] = batting_average
    leaders = list(batting_averages.keys())
    leaders.sort(key=lambda p: batting_averages[p], reverse=True)
    # leaders[0].batting_titles.append(self.current_season)
    for i in xrange(9):
        career_leaders += "\n{}\t{}\t{}\t\t{}\t{}-{}".format(
            i+1, round(batting_averages[leaders[i]], 3),
            leaders[i].person.name, leaders[i].position,
            leaders[i].career.debut.year,
            leaders[i].career.finale.year if leaders[i].career.finale else 'active',
        )
    # Home run leaders
    career_leaders += "\n\n\t\tHOME RUN KINGS\n"
    leaders = list(league.players)
    leaders.sort(key=lambda p: len(p.career.statistics.home_runs), reverse=True)
    # leaders[0].home_run_titles.append(self.current_season)
    for i in xrange(9):
        career_leaders += "\n{}\t{}\t{}\t\t{}\t{}-{}".format(
            i+1, len(leaders[i].career.statistics.home_runs),
            leaders[i].person.name, leaders[i].position,
            leaders[i].career.debut.year,
            leaders[i].career.finale.year if leaders[i].career.finale else 'active',
        )
    return career_leaders