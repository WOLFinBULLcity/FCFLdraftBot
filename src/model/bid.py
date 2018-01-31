#!/usr/bin/python
import line_profiler

class Bid:

    # @profile
    def __init__(self, team, amount, time, id, comment):
        self.team = team
        self.amount = amount
        self.time = time
        self.id = id
        self.comment = comment
        # print("Bid of " + str(self.amount.format("en_US")) + " from coach " + self.team.coach + " for team " +
        #       self.team.name + " at " + time.strftime('%Y-%m-%d %H:%M:%S') + ". ID = " + self.id)

    # @profile
    def __str__(self):
        return str(self.__dict__)

    # @profile
    def __eq__(self, other):
        return self.id == other.id and self.team == other.team
