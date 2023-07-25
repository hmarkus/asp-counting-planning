#! /usr/bin/env python

class Configuration:
    def __init__(self, name, arguments, relevance_analysis=True):
        self.name = name
        self.arguments = arguments
        self.relevance_analysis = relevance_analysis

    def __str__(self):
        return self.name
