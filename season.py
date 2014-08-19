class Season(object):

    def __init__(self, league):

        self.league = league
        league.seasons.append(self)
        self.year = league.country.year
        self.teams = league.teams
        self.records = {}
        self.champion = None

        for t in self.teams:
            t.wins = 0
            t.losses = 0
            t.record = '0-0'

        self.sim_season()


    def __str__(self):

        rep = str(self.year) + ' ' + self.league.name + ' season'
        return rep


    def sim_game(self, host, visitor, show_score=False, postseason=False):

        extra_innings = 0

        host_runs = int(round(((2 * normal(host.ortg, 5)) * 0.55)))
        vis_runs = int(round(((2 * normal(visitor.ortg, 5)) * 0.45)))

        if host_runs < 0:
            host_runs = 0
        if vis_runs < 0:
            vis_runs = 0

        while host_runs == vis_runs:
            extra_innings += 1
            if show_score:
                raw_input('\nGame extends into ' + str(9+extra_innings) +
                          'th inning with score tied ' + str(host_runs) +
                          '-' + str(vis_runs) + '... ')
            vis_score = (int(round(((2 * normal(visitor.ortg,5))*0.45)))
                          / 9)
            if vis_score < 0:
                vis_score = 0
            vis_runs += vis_score
            if show_score:
                if vis_score == 1:
                    raw_input('\n' + visitor.city.name +
                              ' scores 1 run in top of inning. ')
                else:
                    raw_input('\n' + visitor.city.name + ' scores ' +
                              str(vis_score) +
                              ' runs in top of inning. ')
            host_score = (int(round(((2 * normal(host.ortg,5))*0.55)))
                          / 9)
            if host_score < 0:
                host_score = 0
            host_runs += host_score
            if show_score:
                if host_score == 1:
                    raw_input('\n' + host.city.name + ' scores 1 run. ')
                else:
                    raw_input('\n' + host.city.name + ' scores ' +
                              str(host_score) +
                              ' runs in bottom of inning. ')

        if host_runs > vis_runs:
            winner = host
            loser = visitor
        if vis_runs > host_runs:
            winner = visitor
            loser = host

        if show_score:
            print(host.name + ' ' + str(host_runs) + ', ' + visitor.name +
                  ' ' + str(vis_runs))

        if not postseason:
            winner.wins += 1
            winner.cumulative_wins += 1
            loser.losses += 1
            loser.cumulative_losses += 1
            host.record = str(host.wins) + '-' + str(host.losses)
            visitor.record = str(visitor.wins) + '-' + str(visitor.losses)

        host.ortg = int(round(normal(host.ortg, 0.15)))
        visitor.ortg = int(round(normal(visitor.ortg, 0.15)))

        return winner
