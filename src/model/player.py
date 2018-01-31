#!/usr/bin/python
import line_profiler
from money import Money

class Player:

    # @profile
    def __init__(self, name, copy):
        self.name = name
        self.copy = copy
        self.scholarship = Money(0, 'USD')

    # @profile
    def __str__(self):
        return str(self.__dict__)

    # @profile
    def __eq__(self, other):
        return self.name == other.name and self.copy == other.copy

