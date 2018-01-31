#!/usr/bin/python
import line_profiler

class Roster:

    # @profile
    def __init__(self):
        self.url = None
        self.conference = None
        self.auctions = []

    # @profile
    def set_url(self, url):
        self.url = url

    # @profile
    def add_auction(self, auction):
        # Only add the auction if it's new
        for a in self.auctions:
            if a == auction:
                # If we already have this auction, exit.
                return
        self.auctions.append(auction)

    # def from_coach(self, coach):
    #     for team in self.teams:
    #         if team.coach == coach:
    #             return team
    #     return None
    #
    # def from_team(self, team):
    #     for t in self.teams:
    #         if t.team == team:
    #             return t
    #     return None



