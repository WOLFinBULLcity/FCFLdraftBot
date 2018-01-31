#!/usr/bin/python
import line_profiler

from model.draft import Draft
from model.team_assignments import TeamAssignments

class Conference:

    # @profile
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.description = None
        self.team_assignments = TeamAssignments()
        self.draft = None

    # @profile
    def __str__(self):
        return str(self.__dict__)

    # @profile
    def __eq__(self, other):
        return self.name == other.name and self.id == other.id

