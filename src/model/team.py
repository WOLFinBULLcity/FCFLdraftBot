#!/usr/bin/python
import line_profiler

class Team:

    # @profile
    def __init__(self, coach, name, id):
        self.coach = coach
        self.name = name
        self.id = id

    # @profile
    def __str__(self):
        return str(self.__dict__)

    # @profile
    def __eq__(self, other):
        return self.coach == other.coach and self.name == other.name and self.id == other.id
