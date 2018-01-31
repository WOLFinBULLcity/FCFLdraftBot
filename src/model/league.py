#!/usr/bin/python
import line_profiler

class League:

    # @profile
    def __init__(self, name):
        self.name = name
        self.conferences = []

    # @profile
    def add_conference(self, conference):
        # Only add the conference if it's new
        for c in self.conferences:
            if c == conference:
                # If we already have this auction, exit.
                return
        self.conferences.append(conference)


    # @profile
    def conference_from_id(self, id):
        for conference in self.conferences:
            if conference.id == id:
                return conference
        return None

    # @profile
    def conference_from_team(self, team):
        for conference in self.conferences:
            for t in conference.team_assignments.teams:
                if t == team:
                    return conference
        return None



