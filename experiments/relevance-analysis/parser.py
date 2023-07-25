#! /usr/bin/env python

import re
import sys

from lab.parser import Parser

PATTERNS = [
    ('ground', r'Gringo finished correctly: (\d+)', int),
    ('total_time', r'Total time \(in seconds\): (.+)s', float),
    ('model_size', r'Size of the model: (\d+)', int),
    ('atoms', r'Number of atoms \(not actions\): (\d+)', int),
    ('non_temporary_atoms', r'Number of atoms discarding temporary ones: (\d+)', int),
    ('relevant_atoms', r'Number of relevant atoms: (\d+)', int),
    ('actions', r'# of actions: (\d+)', int)
]

DRIVER_LOG_PATTERNS = [
    ('gringo_time', r'run-grounder wall-clock time: (.+)s', float),
    ('newground_time', r'run-counter wall-clock time: (.+)s', float),
]

class OurParser(Parser):
    def __init__(self):
        Parser.__init__(self)

        for name, pattern, typ in PATTERNS:
            self.add_pattern(name, pattern, type=typ)

        for name, pattern, typ in DRIVER_LOG_PATTERNS:
            self.add_pattern(name, pattern, file='driver.log', type=typ)



def main():
    parser = OurParser()
    parser.parse()

main()
