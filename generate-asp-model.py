#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import uuid

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

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if args.fd_split or args.htd_split:
        command = [dir_path+'/src/translate/pddl_to_prolog.py', domain_file, instance_file]
        if args.htd_split:
            command.extend(['--htd', '--only-output-htd-program'])
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)
    else:
        command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
                 instance_file, '--only-output-direct-program']
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)


    if args.lpopt_preprocessor:
        lpopt = find_lpopt()
        temporary_filename = str(uuid.uuid4())
        command = [lpopt, "-f", theory_output]
        temp_file = open(temporary_filename, "w+t")
        execute(command, stdout=temporary_filename)
        os.rename(temporary_filename, theory_output)

    grounder = select_grounder(args.grounder)

    extra_options = []

    # It is unclear whether we can still support clingo, but I left this here
    # just in case we revert the change.
    if args.grounder == 'clingo':
        extra_options = ['-V2', '--quiet']
    elif args.grounder == 'gringo':
        extra_options=['--output', 'text']
    elif args.grounder == 'newground':
        extra_options=['--no-show', '--ground']

    use_clingo = args.grounder == 'clingo'

    with open(args.model_output, 'w+t') as output:
        start_time = time.time()
        command = [grounder, theory_output] + extra_options
        retcode = execute(command, stdout=output)
        if retcode == 0 or retcode == 30:
            # For some reason, clingo returns 30 for correct exit
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % compute_time(start_time, use_clingo, args.model_output))
            if args.grounder == 'newground':
                with open(args.model_output, 'r') as model_file:
                    print(model_file.read())
        else:
            print ("Gringo finished correctly: 0")

    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
