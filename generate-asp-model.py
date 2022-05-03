#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import tempfile
import time
import uuid

from tarski.io import FstripsReader
from tarski.io import find_domain_filename
from tarski.reachability import create_reachability_lp, run_clingo
from tarski.theories import Theory
from tarski.utils.command import silentremove, execute
from tarski.syntax.transform.universal_effect_elimination import expand_universal_effect, compile_universal_effects_away

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
        return (time.time() - start_time)


def find_dynasp():
    if os.environ.get('DYNASP_BIN_PATH') is not None:
        return os.environ.get('DYNASP_BIN_PATH')
    else:
        print("You need to set an environment variable $DYNASP_BIN_PATH as the path to the binary file of dynasp.")
        sys.exit(-1)


def sanitize(rules):
    new_rules = []
    for r in rules:
        for replacement in ((", ", ","), ("1 = 1,", "")):
            r = r.replace(*replacement)
        if "goal()" in r:
            r = r.replace("goal()", "goal_reachable")
        new_rules.append(r)
    return new_rules

if __name__ == '__main__':
    args = parse_arguments()

    domain_file = args.domain
    instance_file = args.instance
    if not os.path.isfile(domain_file):
        sys.stderr.write("Error: Domain file does not exist.\n")
        sys.exit()
    if not os.path.isfile(instance_file):
        sys.stderr.write("Error: Instance file does not exist.\n")
        sys.exit()

    theory_output = args.theory_output

    problem = FstripsReader(
        raise_on_error=True,
        theories=[Theory.EQUALITY],
        strict_with_requirements=False).read_problem(domain_file, instance_file)
    problem = compile_universal_effects_away(problem)

    lp, tr = create_reachability_lp(problem, args.ground_actions)
    with open(theory_output, 'w+t') as output:
        rules = sanitize(lp.rules)
        _ = [print(str(r), file=output) for r in rules]
        print("ASP model being copied to %s" % theory_output)

    if args.dynasp_preprocessor:
        dynasp = find_dynasp()
        temporary_filename = str(uuid.uuid4())
        command = [dynasp, "-f", theory_output, "-a", "lpopt"]
        execute(command, stdout=temporary_filename)
        os.rename(temporary_filename, theory_output)

    grounder = select_grounder(args.clingo)

    extra_options = []
    if args.clingo:
        extra_options = ['-V2', '--quiet']
    with open(args.model_output, 'w+t') as output:
        start_time = time.time()
        command = [grounder, theory_output] + extra_options
        retcode = execute(command, stdout=output)
        if retcode == 0 or retcode == 30:
            # For some reason, clingo returns 30 for correct exit
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % compute_time(start_time, args.clingo, args.model_output))
        else:
            print ("Gringo finished correctly: 0")



    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
