#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import tempfile
import time

from tarski.io import FstripsReader
from tarski.io import find_domain_filename
from tarski.reachability import create_reachability_lp, run_clingo
from tarski.theories import Theory
from tarski.utils.command import silentremove, execute

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

    args = parser.parse_args()
    if args.domain is None:
        args.domain = find_domain_filename(args.instance)
        if args.domain is None:
            raise RuntimeError(f'Could not find domain filename that matches instance file "{args.domain}"')

    return args

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

    lp, tr = create_reachability_lp(problem, args.ground_actions)
    with open(theory_output, 'w+t') as output:
        _ = [print(str(r), file=output) for r in lp.rules]
        print("ASP model being copied to %s" % theory_output)
    gringo = shutil.which("gringo")
    if gringo is None:
        raise CommandNotFoundError("gringo")

    with open(args.model_output, 'w+t') as output:
        start_time = time.time()
        command = [gringo, theory_output]
        retcode = execute(command, stdout=output)
        if retcode == 0:
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % (time.time() - start_time))
        else:
            print ("Gringo finished correctly: 0")



    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
