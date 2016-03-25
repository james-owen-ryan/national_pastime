import random
from career import ScoutCareer


class Scout(object):
    """The baseball-scout layer of a person's being."""

    def __init__(self, person, team):
        """Initialize a Scout object."""
        self.person = person  # The person in whom this scout layer embeds
        person.scout = self
        self.career = ScoutCareer(scout=self)
        self.team = team

    def secure_a_player(self, position):
        """Secure and sign a player to play at the given position of need."""
        city = self.team.city
        state = city.state
        country = city.country
        free_agents = state.free_agents | set(random.sample(country.free_agents, min(1000, len(country.free_agents))))
        free_agents = {p for p in free_agents if 16 < p.person.age < 41}
        return max(free_agents, key=lambda fa: self.grade(prospect=fa, position=position))

    @staticmethod
    def grade(prospect, position):
        """Grade a prospect for their skill in playing at the given position."""
        if position == 'P':
            grade = (1.4-prospect.pitch_control) + 1.3*(prospect.pitch_speed/67.0) + prospect.person.mood.composure
        elif position == "C":
            grade = (
                1.5*prospect.pitch_receiving + 0.75*(prospect.throwing_velocity_mph/72.0) +
                (2-prospect.swing_timing_error/0.14) + (prospect.bat_speed/2.0) + prospect.person.mood.composure
            )
        elif position == "1B":
            grade = (
                prospect.ground_ball_fielding +
                1.7*(2-prospect.swing_timing_error/0.14) + 1.5*(prospect.bat_speed/2.0) +
                prospect.person.mood.composure
            )
        elif position == "2B":
            grade = (
                prospect.ground_ball_fielding +
                1.25*(2-prospect.swing_timing_error/0.14) + 0.5*(prospect.bat_speed/2.0) +
                prospect.person.mood.composure
            )
        elif position == "3B":
            grade = (
                prospect.ground_ball_fielding +
                1.25*(2-prospect.swing_timing_error/0.14) + 0.5*(prospect.bat_speed/2.0) +
                prospect.person.mood.composure
            )
        elif position == "SS":
            grade = (
                prospect.ground_ball_fielding +
                0.9*(2-prospect.swing_timing_error/0.14) + 0.33*(prospect.bat_speed/2.0) +
                prospect.person.mood.composure
            )
        elif position == "LF":
            grade = (
                prospect.fly_ball_fielding + 0.75*(prospect.throwing_velocity_mph/72.0) +
                1.5*(2-prospect.swing_timing_error/0.14) +
                (prospect.person.body.full_speed_seconds_per_foot/0.040623) +
                prospect.bat_speed/2.0 + prospect.person.mood.composure
            )
        elif position == "CF":
            grade = (
                prospect.fly_ball_fielding + 0.75*(prospect.throwing_velocity_mph/72.0) +
                1.75*(2-prospect.swing_timing_error/0.14) +
                0.75*(prospect.person.body.full_speed_seconds_per_foot/0.040623) +
                1.5*(prospect.bat_speed/2.0) + prospect.person.mood.composure
            )
        else:  # position == "RF"
            grade = (
                0.75*prospect.fly_ball_fielding + (prospect.throwing_velocity_mph/72.0) +
                2*(2-prospect.swing_timing_error/0.14) +
                0.75*(prospect.person.body.full_speed_seconds_per_foot/0.040623) +
                1.75*(prospect.bat_speed/2.0) + prospect.person.mood.composure
            )
        return grade