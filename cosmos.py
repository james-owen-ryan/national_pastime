import random

from place import Country
from ballpark import Ballpark
from game import Game, Inning, Frame, AtBat
from rules import Rules


# POSSIBLE HARD-CODERS:
#       "Single hit by Cyrille Buroker"
#       "Home run hit by Steward Wainer!"  [Was waiting a long time to see this finally]
#       FINALLY, a double is hit! By Bob McKibben (Philadelphia).


us = Country(year=1890)
pitcher = min(us.players, key=lambda p: p.pitch_control)
slap = min(us.players, key=lambda b: b.swing_timing_error)
random.shuffle(us.players)
fatty = next(p for p in us.players if p.weight > 200 and p.swing_timing_error < .1)
random.shuffle(us.players)
ump = next(z for z in us.players if z.hometown.name in ("Minneapolis", "St. Paul", "Duluth"))
catcher = max(us.players, key=lambda qqq: qqq.pitch_receiving)
other_fielders = random.sample(us.players, 7)
for i in xrange(len(other_fielders)):
    d = {0: "1B", 1: "2B", 2: "SS", 3: "3B", 4: "RF", 5: "CF", 6: "LF"}
    other_fielders[i].position = d[i]
fielders = other_fielders + [pitcher, catcher]
catcher.position = "C"
pitcher.position = "P"
l = us.leagues[0]
home_team = l.teams[0]
ballpark = Ballpark(city=l.teams[0].city, tenants=[home_team])
if any(t for t in l.teams if t.city.name in ("Minneapolis", "St. Paul", "Duluth") and t is not home_team):
    away_team = next(t for t in l.teams if t.city.name in ("Minneapolis", "St. Paul", "Duluth") and
                     t is not home_team)
else:
    away_team = l.teams[1]

# game = Game(ballpark=ballpark, league=l, home_team=home_team,
#             away_team=random.choice([t for t in l.teams if t is not home_team]),
#             rules=Rules(), radio=False); game.enact()
# inning = Inning(game=game, number=5); frame = Frame(inning=inning, bottom=True); ab = AtBat(frame=frame); ab.enact(); print ab.result
# ab.draw_playing_field()
# frame = Frame(inning=inning, bottom=True); ab = AtBat(frame=frame);

for i in xrange(31):
    l.conduct_season()
    us.year += 1
    l.conduct_offseason()
    for player in us.players:
        player.increase_in_age()