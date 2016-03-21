import re
import os
import time
import random
from outcome import Strikeout, BaseOnBalls
from career import AnnouncerCareer


# TODO the fact that all the methods are currently static indicates that
# no interesting subjective aspects of the announcer's personage are being
# exploited yet


class Announcer(object):
    """The baseball-announcer layer of a person's being."""

    def __init__(self, person):
        """Initialize an Announcer object."""
        self.person = person  # The person in whom this announcer layer embeds
        # Prepare career attribute
        self.career = AnnouncerCareer(announcer=self)

    @staticmethod
    def call_pregame(self, game):
        """Introduce the game about to be played as part of a radio broadcast."""
        os.system("say We are here in {}, where the hometown {} will host the visiting {}".format(
            game.home_team.city.name, game.home_team.nickname, game.away_team.name
        ))
        time.sleep(0.7)

    @staticmethod
    def call_new_frame(self, frame):
        """Introduce the next frame about to be played as part of a radio broadcast."""
        os.system("say {}".format(str(frame)))

    @staticmethod
    def call_at_bat(self, at_bat):
        """Call an at bat as part of a radio broadcast."""
        positions = {
            "P": "pitcher", "C": "catcher", "1B": "first baseman", "2B": "second baseman",
            "3B": "third baseman", "SS": "shortstop", "LF": "left fielder",
            "CF": "center fielder", "RF": "right fielder"
        }
        score_before = [at_bat.game.away_team.runs, at_bat.game.home_team.runs]
        if at_bat.batter.plate_appearances:
            if at_bat.batter.batting_walks:
                walks_str = " with {} walks ".format(len(at_bat.batter.batting_walks))
            else:
                walks_str = ""
            ab_str = "who is {} for {} {} so far".format(
                len(at_bat.batter.hits), len(at_bat.batter.at_bats), walks_str
            )
        else:
            ab_str = "in his first at bat"
        os.system('say Up to bat for {} is {}, a {} from {} {} today'.format(
            at_bat.batter.team.city.name, at_bat.batter.name, positions[at_bat.batter.position],
            at_bat.batter.hometown.name, ab_str
        ))
        time.sleep(0.5)
        if at_bat.batter.home_runs:
            if len(at_bat.batter.home_runs) > 1:
                os.system('say {} is out of his mind today, he has hit {} home runs'.format(
                    at_bat.batter.last_name, len(at_bat.batter.home_runs)
                ))
            else:
                os.system('say {} hit a home run in the {}'.format(
                    at_bat.batter.last_name, str(at_bat.batter.home_runs[-1].at_bat.frame).split(' inning')[0]
                ))
            time.sleep(0.5)
        elif at_bat.batter.doubles:
            os.system('say {} had a double in the {}'.format(
                at_bat.batter.last_name, str(at_bat.batter.home_runs[-1].at_bat.frame).split(' inning')[0]
            ))
            time.sleep(0.5)
        if at_bat.batter.plate_appearances:
            if type(at_bat.batter.plate_appearances[-1].result) is Strikeout:
                os.system('say {} struck out in his last at bat'.format(at_bat.batter.last_name))
                time.sleep(0.2)
                if at_bat.batter.composure < 0.7:
                    nervous_str = random.choice(["he looks visibly rattled out there",
                                                 "he appears very nervous at the plate",
                                                 "he is visibly shaking right now",
                                                 "he seems quite nervous"])
                    os.system('say {}'.format(nervous_str))
                time.sleep(0.5)
            elif type(at_bat.batter.plate_appearances[-1].result) is BaseOnBalls:
                os.system('say {} was walked in his last at bat'.format(at_bat.batter.last_name))
                time.sleep(0.5)
        elif at_bat.batter.composure > 1.3:
            conf_str = random.choice(["he looks very composed out there",
                                      "he looks very confident at the plate",
                                      "he is looking cool as can be right now",
                                      "he is appearing to be unflappable today"])
            os.system('say {}'.format(conf_str))
        outs_str = random.choice(['the scoreboard shows {} outs'.format(at_bat.frame.outs),
                                  '{} outs for the {}'.format(at_bat.frame.outs, at_bat.batter.team),
                                  'we are at {} outs'.format(at_bat.frame.outs),
                                  '{} outs on the board'.format(at_bat.frame.outs)])
        os.system('say {}'.format(outs_str))
        if not at_bat.frame.baserunners and random.random() < 0.2:
            os.system('say There are no runners on.')
        elif at_bat.frame.bases_loaded:
            os.system('say Bases are loaded!')
        else:
            if at_bat.frame.on_first and at_bat.frame.on_second:
                os.system('say runners on first and second')
            elif at_bat.frame.on_first and at_bat.frame.on_third:
                os.system('say runners on first and third')
            elif at_bat.frame.on_second and at_bat.frame.on_third:
                os.system('say runners on second and third')
            elif at_bat.frame.on_first:
                os.system('say theres a runner on first')
            elif at_bat.frame.on_second:
                os.system('say theres a runner on second')
            elif at_bat.frame.on_third:
                os.system('say theres a runner on third')
        at_bat.enact()
        # Announcer will call the batted ball at this point, at playing_action.enact()'s behest,
        # if there is one
        time.sleep(1.5)
        result = re.sub("\(", '', str(at_bat.result))
        result = re.sub("\)", '', result)
        result = re.sub("'", '', result)
        for position in positions:
            result = re.sub(' {} '.format(position), ' {} '.format(positions[position]), result)
        os.system('say {}'.format(result))
        score_after = [at_bat.game.away_team.runs, at_bat.game.home_team.runs]
        if score_before != score_after or random.random() < 0.15:
            os.system('say the score is {}, {}, {}, {}'.format(
                at_bat.game.away_team.city.name, at_bat.game.away_team.runs,
                at_bat.game.home_team.city.name, at_bat.game.home_team.runs))
        time.sleep(0.5)

    @staticmethod
    def call_batted_ball(self, batted_ball):
        """Call a batted ball as it comes off the bat as part of a radio broadcast."""
        positions = {
            "P": "pitcher", "C": "catcher", "1B": "first baseman", "2B": "second baseman",
            "3B": "third baseman", "SS": "shortstop", "LF": "left fielder",
            "CF": "center fielder", "RF": "right fielder"
        }
        bb_description = str(batted_ball)
        re.sub("\(", "", bb_description)
        for position in positions:
            bb_description = re.sub(" {}\)".format(position), ", {}, ".format(positions[position]),
                                    bb_description)
        os.system('say {}'.format(bb_description))
        time.sleep(0.5)
        if batted_ball.true_distance > 315:
            hit_deep_str = random.choice(["its hit way back!", "its hit very deep!",
                                          "its going, its going, its...",
                                          "this may be a home run!"])
            os.system('say {}'.format(hit_deep_str))