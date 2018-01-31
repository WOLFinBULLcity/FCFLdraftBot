#!/usr/bin/python
import line_profiler

class TeamAssignments:

    # @profile
    def __init__(self):
        self.url = None
        self.teams = []

    # @profile
    def set_url(self, url):
        self.url = url

    # @profile
    def add_team(self, team):
        # Only add the team if it's new
        for idx in range(len(self.teams)):
            if self.teams[idx].id == team.id:
                # If we already have this team assignment, update it and exit.
                self.teams[idx] = team
                return
        self.teams.append(team)

    # @profile
    def team_from_coach(self, coach):
        for idx in range(len(self.teams)):
            if self.teams[idx].coach == coach:
                return self.teams[idx]
        return None

    # @profile
    def team_from_name(self, name):
        for idx in range(len(self.teams)):
            if self.teams[idx].name == name:
                return self.teams[idx]
        return None



