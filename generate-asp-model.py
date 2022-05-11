#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import uuid

from tarski.io import FstripsReader
from tarski.reachability import create_reachability_lp, run_clingo
from tarski.theories import Theory
from tarski.utils.command import silentremove, execute
from tarski.syntax.transform.universal_effect_elimination import expand_universal_effect, compile_universal_effects_away

from utils import *

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

    if args.fd_split or args.htd_split:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        command = [dir_path+'/src/translate/pddl_to_prolog.py', domain_file, instance_file]
        if args.htd_split:
            command.extend(['--htd', '--only-output-htd-program'])
            theory_output = "after-htd-split.lp"
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command)
        print("ASP model being copied to %s" % theory_output)
    else:
        lp, tr = create_reachability_lp(problem, args.ground_actions)
        with open(theory_output, 'w+t') as output:
            rules = sanitize(lp.rules)
            _ = [print(str(r), file=output) for r in rules]
            print("ASP model being copied to %s" % theory_output)


    if args.dynasp_preprocessor:
        dynasp = find_dynasp()
        temporary_filename = str(uuid.uuid4())
        command = [dynasp, "-f", theory_output, "-a", "lpopt"]
        temp_file = open(temporary_filename, "w+t")
        execute(command, stdout=temporary_filename)
        os.rename(temporary_filename, theory_output)

    grounder = select_grounder(args.clingo)

    extra_options = []
    if args.clingo:
        extra_options = ['-V2', '--quiet']
    else:
        extra_options=['--output', 'text']
    with open(args.model_output, 'w+t') as output:
        start_time = time.time()
        command = [grounder, theory_output] + extra_options
        retcode = execute(command, stdout=output)
        if retcode == 0 or retcode == 30:
            # For some reason, clingo returns 30 for correct exit
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % compute_time(start_time, args.clingo, args.model_output))
            if not args.clingo:
                print("Size of the model: %d" % file_length(args.model_output))
                print("Number of atoms (not actions): %d" % get_number_of_atoms(args.model_output, args.fd_split, args.htd_split))
        else:
            print ("Gringo finished correctly: 0")

    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
