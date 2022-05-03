import argparse
import os
import shutil
import sys
import tempfile
import time

from tarski.io import find_domain_filename

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate models.')
    parser.add_argument('-i', '--instance', required=True, help="The path to the problem instance file.")
    parser.add_argument('--domain', default=None, help="(Optional) The path to the problem domain file. If none is "
                                                       "provided, the system will try to automatically deduce "
                                                       "it from the instance filename.")

    parser.add_argument('-m', '--model-output', default='output.model', help="Model output file.")
    parser.add_argument('-t', '--theory-output', default='output.theory', help="Theory output file.")
    parser.add_argument('--ground-actions', action='store_true', help="Ground actions or not.")
    parser.add_argument('-r', '--remove-files', action='store_true', help="Remove model and theory files.")
    parser.add_argument('--clingo', action='store_true', help="Use clingo instead of gringo to avoid I/O overhead.")
    parser.add_argument('--dynasp-preprocessor', action='store_true', help="Use dynasp to preproces s queries for faster grounding.")


    args = parser.parse_args()
    if args.domain is None:
        args.domain = find_domain_filename(args.instance)
        if args.domain is None:
            raise RuntimeError(f'Could not find domain filename that matches instance file "{args.domain}"')

    return args


def select_grounder(use_clingo):
    grounder_name = "gringo"
    if use_clingo:
        grounder_name = "clingo"
    grounder = shutil.which(grounder_name)
    if grounder is None:
        raise CommandNotFoundError("gringo")
    return grounder


def compute_time(start, use_clingo, model):
    if  use_clingo:
        # Clingo -> "Reading : Xs"
        with open(model, "r") as mf:
            for line in mf:
                if line.startswith("Reading      :"):
                    return (float(line.split()[2]))
    else:
        # Gringo -> manual computation
        return (time.time() - start)


def find_dynasp():
    if os.environ.get('DYNASP_BIN_PATH') is not None:
        return os.environ.get('DYNASP_BIN_PATH')
    else:
        print("You need to set an environment variable $DYNASP_BIN_PATH as the path to the binary file of dynasp.")
        sys.exit(-1)


def file_length(filename):
    with open(filename) as f:
        i = 0
        for _, _ in enumerate(f):
            i = i + 1
    return i

def get_number_of_atoms(filename):
    with open(filename) as f:
        counter = 0
        for line in f.readlines():
            if "atom" in line:
                counter = counter+1
    return counter

def sanitize(rules):
    new_rules = []
    for r in rules:
        for replacement in ((", ", ","), ("1 = 1,", ""), ("()", "")):
            r = r.replace(*replacement)
        if "goal()" in r:
            r = r.replace("goal()", "goal_reachable")
        new_rules.append(r)
    return new_rules
